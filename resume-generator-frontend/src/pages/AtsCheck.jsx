import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle,
  Loader2,
  Upload,
  XCircle,
} from 'lucide-react'

const STATUS_META = {
  pass: { Icon: CheckCircle, color: 'text-green-600', label: 'Pass' },
  warn: { Icon: AlertTriangle, color: 'text-yellow-600', label: 'Warning' },
  fail: { Icon: XCircle, color: 'text-red-600', label: 'Fail' },
}

// No account, no auth header — the endpoint is unauthenticated by design
// and everything is processed in memory server-side.
export default function AtsCheck() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const checkFile = async (file) => {
    if (!file) return
    if (!/\.(pdf|docx)$/i.test(file.name)) {
      setError('Only .pdf and .docx files are supported.')
      return
    }
    setLoading(true)
    setError(null)
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

  const summary = report?.summary

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="flex items-center justify-between px-6 py-4 max-w-3xl mx-auto">
        <Link to="/" className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="w-4 h-4" />
          Back
        </Link>
        <span className="text-xs text-gray-500">ATS parseability check</span>
      </nav>

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
            dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
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
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
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
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900 text-sm truncate pr-4">
                {report.filename}
              </h2>
              <span className="text-sm text-gray-600 whitespace-nowrap">
                {summary.passed} passed · {summary.warned} warnings · {summary.failed} failed
              </span>
            </div>

            <div className="space-y-3">
              {report.checks.map((check) => {
                const { Icon, color, label } = STATUS_META[check.status] || STATUS_META.warn
                return (
                  <div
                    key={check.id}
                    className="bg-white rounded-lg border border-gray-200 p-4 flex gap-3"
                  >
                    <Icon className={`w-5 h-5 mt-0.5 shrink-0 ${color}`} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 text-sm">{check.id}</h3>
                        <span className={`text-xs font-medium ${color}`}>{label}</span>
                      </div>
                      <p className="mt-1 text-sm text-gray-600">{check.reason}</p>
                      {check.status !== 'pass' && (
                        <p className="mt-1 text-sm text-gray-700">
                          <span className="font-medium">Fix:</span> {check.fix}
                        </p>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            <p className="mt-6 text-xs text-gray-500 text-center">
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
