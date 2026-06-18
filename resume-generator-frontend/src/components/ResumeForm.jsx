import { useState } from 'react'
import { FileText, Settings, Sparkles, Upload } from 'lucide-react'
import TemplatePicker from './TemplatePicker'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function ResumeForm({
  onGenerate,
  loading,
  backendConnected,
  templates,
  selectedTemplate,
  onSelectTemplate,
  user,
}) {
  const [githubUsername, setGithubUsername] = useState('')
  const [additionalInfo, setAdditionalInfo] = useState('')
  const [priority, setPriority] = useState('experience')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [uploadedResumeText, setUploadedResumeText] = useState(null)
  const [useAsTemplate, setUseAsTemplate] = useState(false)
  const [useAsData, setUseAsData] = useState(true)
  const [customSystemPrompt, setCustomSystemPrompt] = useState(null)
  const [onOpenSystemPrompt, setOnOpenSystemPrompt] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    if (!backendConnected) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Backend server is not connected.',
      })
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${apiUrl}/extract-resume`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to upload resume')
      }

      const data = await response.json()
      setUploadedResumeText(data.text)
      setUploadedFile(file.name)

      if (useAsData) {
        setAdditionalInfo((prev) =>
          prev.trim()
            ? `${prev}\n\n--- Extracted from uploaded resume ---\n${data.text}`
            : data.text
        )
      }

      eventBus.emit(EVENTS.FILE_UPLOADED, { filename: file.name, text: data.text })
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Resume uploaded successfully!',
      })
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, { type: 'error', message: err.message })
    }
  }

  const handleRemoveUpload = () => {
    setUploadedFile(null)
    setUploadedResumeText(null)
    if (useAsData && uploadedResumeText) {
      setAdditionalInfo((prev) =>
        prev
          .replace(`\n\n--- Extracted from uploaded resume ---\n${uploadedResumeText}`, '')
          .replace(uploadedResumeText, '')
          .trim()
      )
    }
    eventBus.emit(EVENTS.FILE_REMOVED)
  }

  const handleGenerate = () => {
    if (!githubUsername && !additionalInfo) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Please provide a GitHub username or additional information',
      })
      return
    }

    if (!backendConnected) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Backend server is not connected.',
      })
      return
    }

    onGenerate({
      github_username: githubUsername || null,
      additional_info: additionalInfo || null,
      priority,
      custom_system_prompt: customSystemPrompt,
      resume_template:
        uploadedResumeText && useAsTemplate ? uploadedResumeText : selectedTemplate?.content,
      template_format: selectedTemplate?.format || 'md',
    })
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">GitHub Username</label>
        <input
          type="text"
          value={githubUsername}
          onChange={(e) => setGithubUsername(e.target.value)}
          placeholder="e.g., octocat"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
        />
        <p className="mt-1 text-xs text-gray-500">We'll fetch your README</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Template</label>
        <TemplatePicker
          templates={templates}
          selected={selectedTemplate}
          onSelect={onSelectTemplate}
          user={user}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload Resume (Optional)
        </label>
        <input
          type="file"
          onChange={handleFileUpload}
          accept=".pdf,.docx,.txt,.md,.tex"
          className="hidden"
          id="resumeUpload"
          disabled={loading}
        />
        <label
          htmlFor="resumeUpload"
          className={`w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2 ${
            loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
          }`}
        >
          <Upload className="w-4 h-4" />
          {loading ? 'Uploading...' : 'Upload PDF/DOCX/TXT'}
        </label>
        {uploadedFile && (
          <div className="mt-2 text-xs text-green-600 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>{uploadedFile}</span>
            <button
              onClick={handleRemoveUpload}
              className="text-red-600 hover:text-red-700 ml-auto"
            >
              Remove
            </button>
          </div>
        )}
        {uploadedFile && (
          <div className="mt-2 space-y-2">
            <label className="flex items-center text-xs text-gray-600">
              <input
                type="checkbox"
                checked={useAsTemplate}
                onChange={(e) => setUseAsTemplate(e.target.checked)}
                className="mr-2"
              />
              Use as template structure
            </label>
            <label className="flex items-center text-xs text-gray-600">
              <input
                type="checkbox"
                checked={useAsData}
                onChange={(e) => setUseAsData(e.target.checked)}
                className="mr-2"
              />
              Extract data into additional info
            </label>
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Resume Focus</label>
        <div className="space-y-2">
          <div
            onClick={() => setPriority('experience')}
            className={`border-2 rounded-lg p-3 cursor-pointer transition ${
              priority === 'experience' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex items-start gap-2">
              <input
                type="radio"
                checked={priority === 'experience'}
                onChange={() => setPriority('experience')}
                className="mt-1"
              />
              <div>
                <div className="font-semibold text-gray-900 text-sm">Experience First</div>
                <div className="text-xs text-gray-600">Emphasize work history</div>
              </div>
            </div>
          </div>
          <div
            onClick={() => setPriority('projects')}
            className={`border-2 rounded-lg p-3 cursor-pointer transition ${
              priority === 'projects' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex items-start gap-2">
              <input
                type="radio"
                checked={priority === 'projects'}
                onChange={() => setPriority('projects')}
                className="mt-1"
              />
              <div>
                <div className="font-semibold text-gray-900 text-sm">Projects First</div>
                <div className="text-xs text-gray-600">Highlight projects</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Additional Information
        </label>
        <textarea
          value={additionalInfo}
          onChange={(e) => setAdditionalInfo(e.target.value)}
          placeholder="Add any extra details: email, phone, work experience, skills not in your GitHub..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm h-32 resize-none"
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium disabled:opacity-50"
      >
        <Sparkles className="w-4 h-4" />
        {loading ? 'Generating...' : 'Generate Resume'}
      </button>
    </div>
  )
}
