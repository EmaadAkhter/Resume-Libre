import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useGenerationStream } from '../hooks/useGenerationStream'
import { authHeaders } from '../lib/api'
import ResumeForm from '../components/ResumeForm'
import FresherWizard from '../components/FresherWizard'
import MarkdownEditor from '../components/MarkdownEditor'

// Standalone demo: no account, no Supabase, nothing saved.
// Works whenever the backend allows unauthenticated generation (DEMO_MODE).
export default function Demo() {
  const { streamGeneration } = useGenerationStream()
  const [resumeContent, setResumeContent] = useState('')
  const [pdfUrl, setPdfUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [compiling, setCompiling] = useState(false)
  const [error, setError] = useState(null)
  const [inputMode, setInputMode] = useState('standard') // 'standard' | 'guided'

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const compilePdf = async (latexSource) => {
    if (!latexSource) return
    setCompiling(true)
    try {
      const resp = await fetch(`${apiUrl}/export-resume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Demo-Mode': 'true',
          ...(await authHeaders()),
        },
        body: JSON.stringify({
          markdown_content: latexSource,
          latex_content: latexSource,
          format: 'latex_pdf',
        }),
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || 'PDF compilation failed')
      }
      const blob = await resp.blob()
      if (pdfUrl) URL.revokeObjectURL(pdfUrl)
      setPdfUrl(URL.createObjectURL(blob))
    } catch (err) {
      setError(err.message)
    } finally {
      setCompiling(false)
    }
  }

  const handleGenerate = async (params) => {
    setLoading(true)
    setError(null)
    setResumeContent('')
    setPdfUrl(null)
    try {
      await streamGeneration(
        params,
        (token, full) => setResumeContent(full),
        (full) => {
          setResumeContent(full)
          compilePdf(full)
        },
        (err) => setError(err),
        { 'X-Demo-Mode': 'true' }
      )
    } catch {
      /* onError already set the message */
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <Link to="/" className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" />
          Back
        </Link>
        <span className="text-xs text-gray-500">Demo — nothing is saved</span>
      </nav>

      <div className="max-w-6xl mx-auto px-6 pb-12 grid lg:grid-cols-[380px_1fr] gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-5 h-fit">
          <div className="flex text-xs rounded-lg border border-gray-300 overflow-hidden mb-4">
            <button
              type="button"
              onClick={() => setInputMode('standard')}
              className={`flex-1 px-2 py-1.5 font-medium ${inputMode === 'standard' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
            >
              Standard
            </button>
            <button
              type="button"
              onClick={() => setInputMode('guided')}
              className={`flex-1 px-2 py-1.5 font-medium ${inputMode === 'guided' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
            >
              Guided (no GitHub needed)
            </button>
          </div>
          {inputMode === 'standard' ? (
            <ResumeForm
              onGenerate={handleGenerate}
              loading={loading}
              backendConnected={true}
              templates={[]}
              selectedTemplate={null}
              onSelectTemplate={() => {}}
              user={null}
            />
          ) : (
            <FresherWizard onGenerate={handleGenerate} loading={loading} />
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 min-h-[600px]">
          {error && (
            <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}
          {pdfUrl ? (
            <iframe src={pdfUrl} title="Resume PDF" className="w-full h-[80vh] rounded" />
          ) : resumeContent ? (
            <MarkdownEditor content={resumeContent} onChange={setResumeContent} />
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400 text-sm">
              {compiling
                ? 'Compiling PDF…'
                : 'Fill the form and hit Generate — output appears here'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
