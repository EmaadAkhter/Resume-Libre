import { useState } from 'react'
import { Upload, Plus, X } from 'lucide-react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function TemplateUploader({ user, onUpload }) {
  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [content, setContent] = useState('')
  const [format, setFormat] = useState('md')
  const [isPublic, setIsPublic] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleFileRead = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (ev) => {
      setContent(ev.target.result)
      setName(file.name.replace(/\.(md|tex)$/, ''))
      setFormat(file.name.endsWith('.tex') ? 'tex' : 'md')
    }
    reader.readAsText(file)
  }

  const handleSubmit = async () => {
    if (!name || !content) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Name and content are required',
      })
      return
    }

    setUploading(true)
    try {
      await onUpload(name, content, format, description, isPublic)
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Template uploaded successfully!',
      })
      setShowModal(false)
      setName('')
      setDescription('')
      setContent('')
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to upload template',
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
      >
        <Plus className="w-4 h-4" />
        Upload Template
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Upload Template</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload .md or .tex file
                </label>
                <input
                  type="file"
                  onChange={handleFileRead}
                  accept=".md,.tex,.txt"
                  className="hidden"
                  id="templateFile"
                />
                <label
                  htmlFor="templateFile"
                  className="w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Upload className="w-4 h-4" />
                  Choose file
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <input
                  type="text"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm bg-white"
                >
                  <option value="md">Markdown (.md)</option>
                  <option value="tex">LaTeX (.tex)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Content</label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm font-mono h-48 resize-none"
                  placeholder="Paste template content or upload a file above..."
                />
              </div>

              {user?.role === 'admin' && (
                <label className="flex items-center text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    className="mr-2"
                  />
                  Make this template public (visible to all users)
                </label>
              )}
            </div>

            <div className="p-4 border-t border-gray-200 flex gap-2 justify-end">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Save Template'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
