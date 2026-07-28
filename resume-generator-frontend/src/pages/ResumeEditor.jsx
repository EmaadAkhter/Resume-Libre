import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Save, Eye, Edit, Copy, Check, FileSearch, Sparkles } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'
import { useGenerationStream } from '../hooks/useGenerationStream'
import { authHeaders } from '../lib/api'
import { useTemplates } from '../hooks/useTemplates'
import ResumeForm from '../components/ResumeForm'
import FresherWizard from '../components/FresherWizard'
import MarkdownEditor from '../components/MarkdownEditor'
import ExportMenu from '../components/ExportMenu'
import PublishMenu from '../components/PublishMenu'
import SystemPromptModal from '../components/SystemPromptModal'
import VersionHistory from '../components/VersionHistory'
import BranchManager from '../components/BranchManager'
import ATSScore from '../components/ATSScore'
import AtsReport, { CHECK_TITLES } from '../components/ats/AtsReport'
import JobMatchCta from '../components/ats/JobMatchCta'
import LoadingScreen from '../components/LoadingScreen'

// One line per non-passing check, in the shape the regeneration prompt
// expects. Capped so it always fits the backend's 4000-char query limit.
export function buildAtsFeedback(report) {
  if (!report?.checks) return ''
  return report.checks
    .filter((c) => c.status === 'fail' || c.status === 'warn' || c.status === 'info')
    .map((c) => `- ${CHECK_TITLES[c.id] || c.id}: ${c.reason} Fix: ${c.fix}`)
    .join('\n')
    .slice(0, 3500)
}

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
  const [inputMode, setInputMode] = useState('standard') // 'standard' | 'guided'
  const [atsScore, setAtsScore] = useState(null)
  const [atsLoading, setAtsLoading] = useState(false)
  const [atsError, setAtsError] = useState(null)
  const [parseReport, setParseReport] = useState(null)
  const [lastParams, setLastParams] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const compilePdf = async (latexSource) => {
    const src = latexSource || resumeContent
    if (!src) return
    setCompilingPdf(true)
    try {
      const resp = await fetch(`${apiUrl}/export-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
        body: JSON.stringify({ markdown_content: src, latex_content: src, format: 'latex_pdf' }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'Compilation failed')
      }
      const blob = await resp.blob()
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
      setPdfUrl(URL.createObjectURL(blob))
      runParseabilityCheck(blob)
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: err.message })
    } finally {
      setCompilingPdf(false)
    }
  }

  // Free deterministic check of the freshly compiled PDF — the same
  // /ats/check the public page uses. Auth header only improves the
  // rate-limit bucketing; failures are silent (nice-to-have panel).
  const runParseabilityCheck = async (blob) => {
    try {
      const formData = new FormData()
      formData.append('file', new File([blob], 'resume.pdf', { type: 'application/pdf' }))
      const resp = await fetch(`${apiUrl}/ats/check`, {
        method: 'POST',
        headers: await authHeaders(),
        body: formData,
      })
      if (resp.ok) setParseReport(await resp.json())
    } catch {
      /* non-fatal */
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

  const runAtsAnalysis = async (resumeText, jobDescription, targetRole) => {
    setAtsLoading(true)
    setAtsError(null)
    try {
      const resp = await fetch(`${apiUrl}/analyze-ats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription || null,
          target_role: jobDescription ? null : targetRole || null,
        }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `ATS analysis failed (${resp.status})`)
      }
      setAtsScore(await resp.json())
    } catch (err) {
      // Non-fatal: the resume itself generated fine, so no toast — just an inline note
      setAtsError(err.message || 'ATS analysis failed')
    } finally {
      setAtsLoading(false)
    }
  }

  const handleGenerate = async (params) => {
    // FresherWizard omits these — fall back to the editor's selections
    params.resume_template ??= selectedTemplate?.content
    params.priority ??= 'experience'

    // Remembered so "Fix issues & regenerate" can replay this run with
    // the parseability findings appended.
    setLastParams(params)

    const jobDescription = params.job_description?.trim() || ''
    const targetRole = params.target_role || ''

    setLoading(true)
    setResumeContent('')
    setPdfUrl(null)
    setAtsScore(null)
    setParseReport(null)
    setAtsError(null)

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
                headers: { 'Content-Type': 'application/json', ...(await authHeaders()) },
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
          if (jobDescription || targetRole) {
            runAtsAnalysis(full, jobDescription, targetRole)
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
    return <LoadingScreen label="Loading resume..." />
  }

  const parseIssueCount = parseReport
    ? parseReport.checks.filter((c) => ['fail', 'warn', 'info'].includes(c.status)).length
    : 0
  const atsDotColor = parseReport
    ? parseReport.summary.failed > 0
      ? 'bg-red-500'
      : parseReport.summary.warned > 0
        ? 'bg-amber-400'
        : 'bg-emerald-500'
    : null

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-y-2 mb-4">
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
                  currentView === 'edit' ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50'
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
                  currentView === 'preview' ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Eye className="w-3 h-3" />
                Preview
              </button>
              <button
                onClick={() => setCurrentView('ats')}
                className={`px-3 py-1.5 text-sm font-medium flex items-center gap-1 ${
                  currentView === 'ats' ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <FileSearch className="w-3 h-3" />
                ATS
                {atsDotColor && (
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${atsDotColor}`}
                    aria-hidden="true"
                  />
                )}
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

            <PublishMenu user={user} resume={resume} pdfUrl={pdfUrl} />

            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
            >
              History
            </button>
        </div>
      </div>

      <div className="flex items-stretch gap-4">
        {/* Left: Form */}
        <div className="w-80 flex-shrink-0">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex text-xs rounded-lg border border-gray-300 overflow-hidden mb-4">
              <button
                type="button"
                onClick={() => setInputMode('standard')}
                className={`flex-1 px-2 py-1.5 font-medium ${inputMode === 'standard' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600'}`}
              >
                Standard
              </button>
              <button
                type="button"
                onClick={() => setInputMode('guided')}
                className={`flex-1 px-2 py-1.5 font-medium ${inputMode === 'guided' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600'}`}
              >
                Guided (no GitHub needed)
              </button>
            </div>
            {inputMode === 'standard' ? (
              <ResumeForm
                onGenerate={handleGenerate}
                loading={loading}
                backendConnected={backendConnected}
                templates={templates}
                selectedTemplate={selectedTemplate}
                onSelectTemplate={selectTemplate}
                user={user}
                customSystemPrompt={customSystemPrompt}
              />
            ) : (
              <FresherWizard onGenerate={handleGenerate} loading={loading} />
            )}
          </div>
          {(atsScore || atsLoading || atsError) && (
            <div className="mt-4">
              <ATSScore result={atsScore} loading={atsLoading} error={atsError} />
            </div>
          )}
        </div>

        {/* Center: Editor/Preview/ATS */}
        <div className="flex-1 h-[calc(100vh-180px)] bg-white border border-gray-200 rounded-lg overflow-hidden">
          {currentView === 'edit' ? (
            <MarkdownEditor content={resumeContent} onChange={setResumeContent} />
          ) : currentView === 'ats' ? (
            <div className="h-full overflow-y-auto p-5">
              {parseReport ? (
                <div className="space-y-4">
                  <AtsReport report={parseReport} />
                  <JobMatchCta report={parseReport} />
                  {parseIssueCount > 0 && lastParams && (
                    <button
                      onClick={() =>
                        handleGenerate({
                          ...lastParams,
                          ats_feedback: buildAtsFeedback(parseReport),
                        })
                      }
                      disabled={loading}
                      className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium"
                    >
                      <Sparkles className="w-4 h-4" />
                      {loading
                        ? 'Regenerating...'
                        : `Fix ${parseIssueCount} issue${parseIssueCount === 1 ? '' : 's'} & regenerate`}
                    </button>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm text-center px-8">
                  Generate a resume — the parseability check runs automatically after each
                  compile.
                </div>
              )}
            </div>
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
    </>
  )
}
