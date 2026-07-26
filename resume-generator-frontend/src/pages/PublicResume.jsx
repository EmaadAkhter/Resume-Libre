import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Download, FileX, Loader2, Sparkles } from 'lucide-react'
import { supabase } from '../lib/supabase'

// Public, shareable resume page: resumelibre.com/r/<user_id>
// PDF is served straight from the public storage bucket — no auth, no backend.
export default function PublicResume() {
  const { userId } = useParams()
  const [entry, setEntry] = useState(null)
  const [status, setStatus] = useState('loading') // loading | ready | missing

  useEffect(() => {
    let cancelled = false
    supabase
      .from('public_resumes')
      .select('display_name, published_at')
      .eq('user_id', userId)
      .maybeSingle()
      .then(({ data }) => {
        if (cancelled) return
        if (data) {
          setEntry(data)
          setStatus('ready')
        } else {
          setStatus('missing')
        }
      })
      .catch(() => !cancelled && setStatus('missing'))
    return () => {
      cancelled = true
    }
  }, [userId])

  // Cache-bust with published_at so a republish shows up immediately.
  const pdfUrl = entry
    ? `${supabase.storage.from('public-resumes').getPublicUrl(`${userId}.pdf`).data.publicUrl}?v=${encodeURIComponent(entry.published_at)}`
    : null

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className="flex items-center justify-between px-6 py-3 max-w-5xl mx-auto w-full">
        <Link to="/">
          <img src="/logo.png" alt="ResumeLibre" className="h-10 w-auto" />
        </Link>
        {status === 'ready' && (
          <a
            href={pdfUrl}
            download={`${entry.display_name}.pdf`}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            <Download className="w-4 h-4" />
            Download PDF
          </a>
        )}
      </nav>

      <main className="flex-1 max-w-5xl mx-auto px-4 sm:px-6 pb-10 w-full">
        {status === 'loading' && (
          <div className="h-[70vh] flex items-center justify-center text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        )}

        {status === 'missing' && (
          <div className="h-[70vh] flex flex-col items-center justify-center gap-3 text-center">
            <FileX className="w-10 h-10 text-gray-300" />
            <p className="text-gray-600 font-medium">No published resume here</p>
            <p className="text-sm text-gray-500 max-w-sm">
              This link doesn&apos;t point to a published resume — it may have
              been taken down by its owner.
            </p>
            <Link
              to="/"
              className="mt-2 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
            >
              <Sparkles className="w-4 h-4" />
              Make your own
            </Link>
          </div>
        )}

        {status === 'ready' && (
          <>
            <h1 className="text-lg font-semibold text-gray-900 mb-3 truncate">
              {entry.display_name}
            </h1>
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
              <iframe
                src={`${pdfUrl}#navpanes=0&toolbar=0`}
                title={entry.display_name}
                className="w-full h-[80vh]"
              />
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-5xl mx-auto px-6 py-4 text-center text-xs text-gray-500">
          Hosted with{' '}
          <Link to="/" className="font-medium text-primary-600 hover:underline">
            Resume-Libre
          </Link>{' '}
          — open-source AI resume generator with a real ATS parseability
          checker. Make yours free.
        </div>
      </footer>
    </div>
  )
}
