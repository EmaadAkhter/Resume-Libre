import { useEffect, useState } from 'react'
import { Check, Copy, Globe, Loader2, Trash2, UploadCloud } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

// Publish the current compiled PDF to the user's public page (/r/<user_id>).
// One live public resume per user; republishing overwrites it.
export default function PublishMenu({ user, resume, pdfUrl }) {
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [published, setPublished] = useState(false)
  const [copied, setCopied] = useState(false)

  const publicUrl = user ? `${window.location.origin}/r/${user.id}` : null

  useEffect(() => {
    if (!user) return
    supabase
      .from('public_resumes')
      .select('user_id')
      .eq('user_id', user.id)
      .maybeSingle()
      .then(({ data }) => setPublished(Boolean(data)))
      .catch(() => {})
  }, [user])

  const toast = (type, message) =>
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type, message })

  const publish = async () => {
    if (!pdfUrl || busy) return
    setBusy(true)
    try {
      const blob = await (await fetch(pdfUrl)).blob()
      const { error: upErr } = await supabase.storage
        .from('public-resumes')
        .upload(`${user.id}.pdf`, blob, {
          upsert: true,
          contentType: 'application/pdf',
        })
      if (upErr) throw upErr

      const { error: rowErr } = await supabase.from('public_resumes').upsert({
        user_id: user.id,
        resume_id: resume?.id ?? null,
        display_name: resume?.name || 'Resume',
        published_at: new Date().toISOString(),
      })
      if (rowErr) throw rowErr

      setPublished(true)
      await navigator.clipboard.writeText(publicUrl).catch(() => {})
      toast('success', `Published! Link copied: ${publicUrl}`)
    } catch (err) {
      toast('error', err.message || 'Publishing failed')
    } finally {
      setBusy(false)
      setOpen(false)
    }
  }

  const copyLink = async () => {
    await navigator.clipboard.writeText(publicUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const unpublish = async () => {
    setBusy(true)
    try {
      await supabase.storage.from('public-resumes').remove([`${user.id}.pdf`])
      const { error } = await supabase
        .from('public_resumes')
        .delete()
        .eq('user_id', user.id)
      if (error) throw error
      setPublished(false)
      toast('success', 'Resume unpublished — the public link is dead.')
    } catch (err) {
      toast('error', err.message || 'Unpublish failed')
    } finally {
      setBusy(false)
      setOpen(false)
    }
  }

  if (!user) return null

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => (published ? setOpen(!open) : publish())}
        disabled={busy || (!published && !pdfUrl)}
        title={!pdfUrl && !published ? 'Compile a PDF first (Preview)' : undefined}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition text-sm font-medium disabled:opacity-50 ${
          published
            ? 'bg-primary-50 text-primary-700 border border-primary-200 hover:bg-primary-100'
            : 'bg-primary-600 hover:bg-primary-700 text-white'
        }`}
      >
        {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
        {published ? 'Published' : 'Publish'}
      </button>

      {open && published && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
            <button
              type="button"
              onClick={copyLink}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
            >
              {copied ? <Check className="w-4 h-4 text-primary-600" /> : <Copy className="w-4 h-4" />}
              Copy public link
            </button>
            <button
              type="button"
              onClick={publish}
              disabled={!pdfUrl}
              title={!pdfUrl ? 'Compile a PDF first (Preview)' : undefined}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left disabled:opacity-50"
            >
              <UploadCloud className="w-4 h-4" />
              Republish current PDF
            </button>
            <button
              type="button"
              onClick={unpublish}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left"
            >
              <Trash2 className="w-4 h-4" />
              Unpublish
            </button>
          </div>
        </>
      )}
    </div>
  )
}
