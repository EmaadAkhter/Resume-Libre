import { useState, useEffect } from 'react'
import { FileText, Sparkles, Upload } from 'lucide-react'
import TemplatePicker from './TemplatePicker'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'
import { authHeaders } from '../lib/api'

export default function ResumeForm({
  onGenerate,
  loading,
  backendConnected,
  templates,
  selectedTemplate,
  onSelectTemplate,
  user,
  customSystemPrompt = null,
}) {
  const [githubUsername, setGithubUsername] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [linkedinMode, setLinkedinMode] = useState('paste') // 'paste' | 'url'
  const [linkedinText, setLinkedinText] = useState('')
  const [additionalInfo, setAdditionalInfo] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [targetRole, setTargetRole] = useState('')
  const [roles, setRoles] = useState([])
  const [priority, setPriority] = useState('experience')
  const [uploadedFile, setUploadedFile] = useState(null)
  const [uploadedResumeText, setUploadedResumeText] = useState(null)
  const [useAsTemplate, setUseAsTemplate] = useState(false)
  const [useAsData, setUseAsData] = useState(true)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetch(`${apiUrl}/ats/roles`)
      .then((r) => (r.ok ? r.json() : { roles: [] }))
      .then((d) => setRoles(d.roles || []))
      .catch(() => {})
  }, [apiUrl])

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
        headers: await authHeaders(),
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
    if (!githubUsername && !linkedinUrl && !additionalInfo && !linkedinText) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: 'Please provide a GitHub username, LinkedIn URL, or additional information',
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

    // Pasted LinkedIn text rides in the additional_info prompt slot — no scraping needed
    const info = linkedinText.trim()
      ? `${additionalInfo}\n\n--- LinkedIn profile (pasted) ---\n${linkedinText.trim()}`.trim()
      : additionalInfo

    onGenerate({
      github_username: githubUsername || null,
      linkedin_url: linkedinMode === 'url' ? linkedinUrl || null : null,
      additional_info: info || null,
      job_description: jobDescription || null,
      target_role: targetRole || null,
      priority,
      custom_system_prompt: customSystemPrompt,
      resume_template:
        uploadedResumeText && useAsTemplate ? uploadedResumeText : selectedTemplate?.content,
      template_format: 'tex',
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
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">LinkedIn (Optional)</label>
          <div className="flex text-xs rounded-lg border border-gray-300 overflow-hidden">
            <button
              type="button"
              onClick={() => setLinkedinMode('paste')}
              className={`px-2 py-1 ${linkedinMode === 'paste' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
            >
              Paste text
            </button>
            <button
              type="button"
              onClick={() => setLinkedinMode('url')}
              className={`px-2 py-1 ${linkedinMode === 'url' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600'}`}
            >
              URL
            </button>
          </div>
        </div>
        {linkedinMode === 'paste' ? (
          <>
            <textarea
              value={linkedinText}
              onChange={(e) => setLinkedinText(e.target.value)}
              placeholder="Open your LinkedIn profile, select all (Ctrl/Cmd+A), copy, and paste here..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm h-24 resize-none"
            />
            <p className="mt-1 text-xs text-gray-500">
              Fastest & most reliable — no scraping involved
            </p>
          </>
        ) : (
          <>
            <input
              type="url"
              value={linkedinUrl}
              onChange={(e) => setLinkedinUrl(e.target.value)}
              placeholder="https://linkedin.com/in/username"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm"
            />
            <p className="mt-1 text-xs text-gray-500">
              We'll try to fetch your profile — can take a few minutes and requires the server to
              have scraping configured. Pasting text is faster.
            </p>
          </>
        )}
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
          <div
            onClick={() => setPriority('balanced')}
            className={`border-2 rounded-lg p-3 cursor-pointer transition ${
              priority === 'balanced' ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex items-start gap-2">
              <input
                type="radio"
                checked={priority === 'balanced'}
                onChange={() => setPriority('balanced')}
                className="mt-1"
              />
              <div>
                <div className="font-semibold text-gray-900 text-sm">Balanced</div>
                <div className="text-xs text-gray-600">Equal weight — experience & projects</div>
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

      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 list-none flex items-center gap-2">
          <span className="group-open:rotate-90 transition-transform inline-block">▶</span>
          Target a specific job (optional)
        </summary>
        <div className="mt-2 space-y-2">
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste job description here — AI will tailor the resume to match..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm h-28 resize-none"
          />
          {roles.length > 0 && (
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                No job description? Pick a target role for the match analysis:
              </label>
              <select
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                disabled={Boolean(jobDescription.trim())}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg outline-none text-sm bg-white disabled:opacity-50"
              >
                <option value="">— none —</option>
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </details>

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
