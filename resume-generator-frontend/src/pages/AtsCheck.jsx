import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Loader2, Sparkles, Upload } from 'lucide-react'
import { authHeaders } from '../lib/api'
import AtsReport from '../components/ats/AtsReport'
import JobMatchCta from '../components/ats/JobMatchCta'

// The basic check needs no account — the endpoint is unauthenticated by
// design and everything is processed in memory server-side. Only the
// optional AI resolve pass (LLM cost) requires being signed in.
export default function AtsCheck({ inShell = false }) {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  // Re-submitted for the AI resolve pass on the ambiguous fields.
  const [lastFile, setLastFile] = useState(null)
  const [signedIn, setSignedIn] = useState(null)
  const [resolving, setResolving] = useState(false)
  const [resolveError, setResolveError] = useState(null)
  const inputRef = useRef(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // authHeaders() is async (Supabase session lookup), so signed-in state is
  // determined in an effect once a report is on screen.
  useEffect(() => {
    if (!report?.extracted) return undefined
    let cancelled = false
    authHeaders().then((headers) => {
      if (!cancelled) setSignedIn(Object.keys(headers).length > 0)
    })
    return () => {
      cancelled = true
    }
  }, [report])

  // Only fields the LLM fallback can actually address. Link-annotation
  // recoveries (linkedin/github) stay low-confidence by design — the URL
  // isn't in the visible text, so there's nothing for the AI to resolve.
  const RESOLVABLE = ['name', 'email', 'phone', 'dates']
  const ambiguousCount = report?.extracted
    ? RESOLVABLE.filter((k) => {
        const r = report.extracted[k]
        return r && (r.failed || r.confidence === 'low' || r.value == null)
      }).length
    : 0

  const resolveWithAi = async () => {
    if (!lastFile || resolving) return
    setResolving(true)
    setResolveError(null)
    try {
      const headers = await authHeaders()
      const formData = new FormData()
      formData.append('file', lastFile)
      const resp = await fetch(`${apiUrl}/ats/extract`, {
        method: 'POST',
        headers,
        body: formData,
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `AI resolve failed (${resp.status})`)
      }
      const data = await resp.json()
      setReport((prev) => ({
        ...prev,
        extracted: { ...prev.extracted, ...data.extracted },
      }))
    } catch (err) {
      setResolveError(err.message)
    } finally {
      setResolving(false)
    }
  }

  const checkFile = async (file) => {
    if (!file) return
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setError('Only .pdf and .docx files are supported.')
      return
    }
    setLastFile(file)
    setLoading(true)
    setError(null)
    setResolveError(null)
    setReport(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const resp = await fetch(`${apiUrl}/ats/check`, {
        method: 'POST',
        body: formData,
      })
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}))
        throw new Error(err.detail || `Check failed (${resp.status})`)
      }
      setReport(await resp.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    checkFile(e.dataTransfer.files?.[0])
  }

  return (
    <div className={inShell ? '' : 'min-h-screen bg-gray-50'}>
      {!inShell && (
        <nav className="flex items-center justify-between px-6 py-4 max-w-3xl mx-auto">
          <Link to="/" className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
          <span className="text-xs text-gray-500">ATS parseability check</span>
        </nav>
      )}

      <main className="max-w-3xl mx-auto px-6 pb-16">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 text-center">
          Can ATS software actually read your resume?
        </h1>
        <p className="mt-3 text-sm text-gray-600 text-center max-w-xl mx-auto">
          Upload your resume and get a plain checklist of how reliably applicant
          tracking systems can extract its text — no fake score, just what to fix.
        </p>

        <p className="mt-6 text-xs text-gray-500 text-center">
          Processed in memory, never stored. No account needed.
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          className={`mt-2 bg-white rounded-lg border-2 border-dashed p-10 text-center cursor-pointer transition ${
            dragging ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={(e) => checkFile(e.target.files?.[0])}
          />
          {loading ? (
            <div className="flex flex-col items-center gap-2 text-gray-500">
              <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
              <span className="text-sm">Checking your resume…</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-gray-500">
              <Upload className="w-8 h-8 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">
                Drop your resume here or click to browse
              </span>
              <span className="text-xs">PDF or DOCX, up to 5 MB</span>
            </div>
          )}
        </div>

        {error && (
          <div className="mt-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {report && (
          <div className="mt-8">
            <h2 className="font-semibold text-gray-900 text-sm truncate mb-4">
              {report.filename || lastFile?.name}
            </h2>

            <AtsReport report={report} />

            {report.extracted && (
              <div className="mt-6">
                {ambiguousCount > 0 && signedIn === true && (
                  <div className="mt-4">
                    <button
                      type="button"
                      onClick={resolveWithAi}
                      disabled={resolving || !lastFile}
                      className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
                    >
                      {resolving ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Resolving…
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          Resolve {ambiguousCount} ambiguous{' '}
                          {ambiguousCount === 1 ? 'field' : 'fields'} with AI
                        </>
                      )}
                    </button>
                    {resolveError && (
                      <p className="mt-2 text-sm text-red-600">{resolveError}</p>
                    )}
                  </div>
                )}

                {ambiguousCount > 0 && signedIn === false && (
                  <p className="mt-4 text-xs text-gray-500">
                    <Link to="/login" className="underline hover:text-gray-700">
                      Sign in
                    </Link>{' '}
                    to resolve ambiguous fields with AI.
                  </p>
                )}
              </div>
            )}

            <p className="mt-6 text-xs text-gray-400 text-center">
              Checks are calibrated against a small manual dataset and generic
              PDF-extraction behavior — not against any commercial ATS's
              internal parser.
            </p>

            <JobMatchCta report={report} />

            <p className="mt-4 text-xs text-gray-500 text-center">
              Want a resume that passes these checks by construction?{' '}
              <Link to="/" className="underline hover:text-gray-700">
                Generate one with Resume-Libre
              </Link>
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
