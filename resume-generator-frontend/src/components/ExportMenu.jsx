import { useState } from 'react'
import { Download, FileText, FileType, FileCode } from 'lucide-react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function ExportMenu({ resumeContent, latexContent, backendConnected }) {
  const [showMenu, setShowMenu] = useState(false)
  const [exporting, setExporting] = useState(false)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const handleExport = async (format) => {
    setShowMenu(false)
    if (!resumeContent) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: 'No resume to export' })
      return
    }
    if (!backendConnected) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Backend server is not connected.',
      })
      return
    }

    eventBus.emit(EVENTS.EXPORT_REQUESTED, { format })
    setExporting(true)

    try {
      const body = {
        markdown_content: resumeContent,
        format,
      }
      if (latexContent && format === 'latex_pdf') {
        body.latex_content = latexContent
      }

      const response = await fetch(`${apiUrl}/export-resume`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to export resume')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url

      const ext = { pdf: 'pdf', latex_pdf: 'pdf', docx: 'docx', md: 'md', latex: 'tex' }
      a.download = `resume.${ext[format] || format}`

      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      eventBus.emit(EVENTS.EXPORT_COMPLETED, { format })
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: `Resume exported as ${format.toUpperCase()} successfully!`,
      })
    } catch (err) {
      eventBus.emit(EVENTS.EXPORT_FAILED, { format, error: err.message })
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to export resume',
      })
    } finally {
      setExporting(false)
    }
  }

  const options = [
    { format: 'latex_pdf', label: 'PDF (LaTeX)', icon: <FileText className="w-4 h-4" /> },
    { format: 'pdf', label: 'PDF (Basic)', icon: <FileText className="w-4 h-4" /> },
    { format: 'docx', label: 'DOCX', icon: <FileType className="w-4 h-4" /> },
    { format: 'md', label: 'Markdown', icon: <FileCode className="w-4 h-4" /> },
    { format: 'latex', label: 'LaTeX Source', icon: <FileCode className="w-4 h-4" /> },
  ]

  return (
    <div className="relative">
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={exporting}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium disabled:opacity-50"
      >
        <Download className="w-4 h-4" />
        {exporting ? 'Exporting...' : 'Export'}
      </button>

      {showMenu && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
          <div className="absolute right-0 mt-2 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
            {options.map((opt) => (
              <button
                key={opt.format}
                onClick={() => handleExport(opt.format)}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition text-left"
              >
                {opt.icon}
                {opt.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
