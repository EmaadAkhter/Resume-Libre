import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Save, Eye, Edit, Copy, Check } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'
import { useGenerationStream } from '../hooks/useGenerationStream'
import { useTemplates } from '../hooks/useTemplates'
import ResumeForm from '../components/ResumeForm'
import MarkdownEditor from '../components/MarkdownEditor'
import ExportMenu from '../components/ExportMenu'
import SystemPromptModal from '../components/SystemPromptModal'
import VersionHistory from '../components/VersionHistory'
import BranchManager from '../components/BranchManager'
import DiffViewer from '../components/DiffViewer'

export default function ResumeEditor({ user }) {
  const { resumeId } = useParams()
  const navigate = useNavigate()
  const { streamGeneration } = useGenerationStream()
  const { templates, selectedTemplate, selectTemplate } = useTemplates(user)

  const [resume, setResume] = useState(null)
  const [resumeContent, setResumeContent] = useState('')
  const [pdfUrl, setPdfUrl] = useState(null)
  const [compilingPdf, setCompilingPdf] = useState(false)
  const [currentView, setCurrentView] = useState('edit')
  const [loading, setLoading] = useState(false)
  const [backendConnected, setBackendConnected] = useState(true)
  const [customSystemPrompt, setCustomSystemPrompt] = useState(null)
  const [copied, setCopied] = useState(false)
  const [currentBranch, setCurrentBranch] = useState('main')
  const [showHistory, setShowHistory] = useState(false)
  const [diff, setDiff] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const compilePdf = async (latexSource) => {
    const src = latexSource || resumeContent
    if (!src) return
    setCompilingPdf(true)
    try {
      const resp = await fetch(`${apiUrl}/export-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ markdown_content: src, latex_content: src, format: 'latex_pdf' }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'Compilation failed')
      }
      const blob = await resp.blob()
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
      setPdfUrl(URL.createObjectURL(blob))
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: err.message })
    } finally {
      setCompilingPdf(false)
    }
  }

  useEffect(() => {
    const onConnected = () => setBackendConnected(true)
    const onDisconnected = () => setBackendConnected(false)
    eventBus.on(EVENTS.BACKEND_CONNECTED, onConnected)
    eventBus.on(EVENTS.BACKEND_DISCONNECTED, onDisconnected)
    return () => {
      eventBus.off(EVENTS.BACKEND_CONNECTED, onConnected)
      eventBus.off(EVENTS.BACKEND_DISCONNECTED, onDisconnected)
    }
  }, [])

  const loadResume = useCallback(async () => {
    if (!resumeId || !user) return
    const { data } = await supabase
      .from('resumes')
      .select('*')
      .eq('id', resumeId)
      .eq('user_id', user.id)
      .single()

    if (data) {
      setResume(data)
      setCurrentBranch(data.current_branch)

      // Load latest version content
      const { data: branch } = await supabase
        .from('branches')
        .select('head_version_id')
        .eq('resume_id', resumeId)
        .eq('name', data.current_branch)
        .single()

      if (branch?.head_version_id) {
        const { data: version } = await supabase
          .from('resume_versions')
          .select('*')
          .eq('id', branch.head_version_id)
          .single()

        if (version) {
          setResumeContent(version.latex_content || version.content)
        }
      }
    }
  }, [resumeId, user])

  useEffect(() => {
    loadResume()
  }, [loadResume])

  const handleGenerate = async (params) => {
    setLoading(true)
    setResumeContent('')
    setPdfUrl(null)

    try {
      const content = await streamGeneration(
        params,
        (token, full) => {
          setResumeContent(full)
        },
        async (full) => {
          setCurrentView('preview')
          // If AI output markdown despite tex request, convert to LaTeX first
          if (!full.includes('\\documentclass')) {
            try {
              const resp = await fetch(`${apiUrl}/export-resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ markdown_content: full, format: 'latex' }),
              })
              const latex = await resp.text()
              setResumeContent(latex)
              compilePdf(latex)
            } catch {
              setResumeContent(full)
              compilePdf(full)
            }
          } else {
            setResumeContent(full)
            compilePdf(full)
          }
        },
        (err) => {
          eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: err })
        }
      )

      if (content) {
        await saveVersion(content, params)
      }
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Generation failed',
      })
    } finally {
      setLoading(false)
    }
  }

  const saveVersion = async (content, params) => {
    try {
      const { data: branch } = await supabase
        .from('branches')
        .select('head_version_id')
        .eq('resume_id', resumeId)
        .eq('name', currentBranch)
        .single()

      const { error } = await supabase.from('resume_versions').insert({
        resume_id: resumeId,
        parent_version_id: branch?.head_version_id,
        branch_name: currentBranch,
        message: params ? 'AI generated' : 'Manual edit',
        content: '',
        latex_content: content,
        generation_prompt: JSON.stringify(params || {}),
        template_id: selectedTemplate?.id,
      })

      if (error) throw error

      // Update branch head
      const { data: newVersion } = await supabase
        .from('resume_versions')
        .select('id')
        .eq('resume_id', resumeId)
        .eq('branch_name', currentBranch)
        .order('created_at', { ascending: false })
        .limit(1)
        .single()

      if (newVersion) {
        await supabase
          .from('branches')
          .update({ head_version_id: newVersion.id })
          .eq('resume_id', resumeId)
          .eq('name', currentBranch)
      }
    } catch (err) {
      console.error('Failed to save version:', err)
    }
  }

  const handleSave = async () => {
    if (!resumeContent) return
    await saveVersion(resumeContent)
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
      type: 'success',
      message: 'Resume saved!',
    })
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(resumeContent)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Copied to clipboard!',
      })
    } catch {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Failed to copy',
      })
    }
  }

  const handleViewVersion = (version) => {
    setResumeContent(version.content)
    setCurrentView('preview')
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
      type: 'info',
      message: `Viewing version from ${new Date(version.created_at).toLocaleString()}`,
    })
  }

  if (!resume) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-400">
        Loading resume...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-500 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900">{resume.name}</h1>
            <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-100 rounded">
              {currentBranch}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <SystemPromptModal onApply={(prompt) => setCustomSystemPrompt(prompt)} />

            <div className="flex border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => setCurrentView('edit')}
                className={`px-3 py-1.5 text-sm font-medium flex items-center gap-1 ${
                  currentView === 'edit' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Edit className="w-3 h-3" />
                Edit
              </button>
              <button
                onClick={() => {
                  setCurrentView('preview')
                  compilePdf()
                }}
                className={`px-3 py-1.5 text-sm font-medium flex items-center gap-1 ${
                  currentView === 'preview' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Eye className="w-3 h-3" />
                Preview
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
            >
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </button>

            <button
              onClick={handleSave}
              className="flex items-center gap-1 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
            >
              <Save className="w-4 h-4" />
              Save
            </button>

            <ExportMenu
              resumeContent={resumeContent}
              latexContent={resumeContent}
              backendConnected={backendConnected}
            />

            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
            >
              History
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-4 flex gap-4">
        {/* Left: Form */}
        <div className="w-80 flex-shrink-0">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <ResumeForm
              onGenerate={handleGenerate}
              loading={loading}
              backendConnected={backendConnected}
              templates={templates}
              selectedTemplate={selectedTemplate}
              onSelectTemplate={selectTemplate}
              user={user}
            />
          </div>
        </div>

        {/* Center: Editor/Preview */}
        <div className="flex-1 bg-white border border-gray-200 rounded-lg overflow-hidden">
          {currentView === 'edit' ? (
            <MarkdownEditor content={resumeContent} onChange={setResumeContent} />
          ) : compilingPdf ? (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              Compiling PDF...
            </div>
          ) : pdfUrl ? (
            <iframe src={`${pdfUrl}#navpanes=0&toolbar=0`} className="w-full h-full border-0" title="Resume PDF Preview" />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
              Click Preview to compile
            </div>
          )}
        </div>

        {/* Right: Version history + branches (toggleable) */}
        {showHistory && (
          <div className="w-72 flex-shrink-0 space-y-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <BranchManager
                resumeId={resumeId}
                user={user}
                currentBranch={currentBranch}
                onBranchChange={setCurrentBranch}
              />
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <VersionHistory
                resumeId={resumeId}
                user={user}
                onViewVersion={handleViewVersion}
              />
            </div>
          </div>
        )}
      </div>

      {diff && <DiffViewer diff={diff} onClose={() => setDiff(null)} />}
    </div>
  )
}
