import { useState, useEffect } from 'react'
import { Settings, X, RotateCcw } from 'lucide-react'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function SystemPromptModal({ onApply }) {
  const [show, setShow] = useState(false)
  const [editor, setEditor] = useState('')
  const [defaultPrompt, setDefaultPrompt] = useState('')
  const [custom, setCustom] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    loadDefault()
  }, [])

  const loadDefault = async () => {
    try {
      const response = await fetch(`${apiUrl}/get-system-prompt`)
      if (!response.ok) throw new Error('Failed to load system prompt')
      const data = await response.json()
      setDefaultPrompt(data.prompt)
      setEditor(data.prompt)
    } catch {
      const fallback = 'You are a professional resume writer. Create an ATS-friendly, one-page resume in markdown format.'
      setDefaultPrompt(fallback)
      setEditor(fallback)
    }
  }

  const handleSave = () => {
    setCustom(editor.trim())
    setShow(false)
    eventBus.emit(EVENTS.SYSTEM_PROMPT_UPDATED, editor.trim())
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
      type: 'success',
      message: 'System prompt updated!',
    })
    onApply?.(editor.trim())
  }

  const handleReset = () => {
    setCustom(null)
    setEditor(defaultPrompt)
    eventBus.emit(EVENTS.SYSTEM_PROMPT_RESET)
    eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
      type: 'success',
      message: 'System prompt reset to default',
    })
    onApply?.(null)
  }

  return (
    <>
      <button
        onClick={() => {
          setEditor(custom || defaultPrompt)
          setShow(true)
        }}
        className="flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium"
      >
        <Settings className="w-3 h-3" />
        System Prompt
      </button>

      {show && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Edit System Prompt</h2>
              <button onClick={() => setShow(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <p className="text-sm text-gray-600 mb-4">
                Customize the system prompt to change how the AI formats your resume.
              </p>
              <textarea
                value={editor}
                onChange={(e) => setEditor(e.target.value)}
                className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm"
              />
            </div>
            <div className="p-4 border-t border-gray-200 flex flex-col gap-2">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
              >
                <RotateCcw className="w-4 h-4" />
                Reset to Default
              </button>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShow(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
