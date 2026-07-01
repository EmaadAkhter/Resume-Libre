import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Plus, LogOut, Trash2, Clock } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'
import TemplateUploader from '../components/TemplateUploader'
import { useTemplates } from '../hooks/useTemplates'

export default function Dashboard({ user, profile, logout }) {
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const navigate = useNavigate()

  const { templates, selectedTemplate, selectTemplate, uploadTemplate } = useTemplates(user)

  const fetchResumes = useCallback(async () => {
    if (!user) return
    setLoading(true)
    try {
      const { data } = await supabase
        .from('resumes')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false })
      setResumes(data || [])
    } catch (err) {
      console.error('Failed to fetch resumes:', err)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    fetchResumes()
  }, [fetchResumes])

  const handleCreate = async () => {
    if (!newName) return
    try {
      const { data, error } = await supabase
        .from('resumes')
        .insert({
          user_id: user.id,
          name: newName,
          template_id: selectedTemplate?.id,
        })
        .select()
        .single()

      if (error) throw error

      // Create default main branch
      await supabase.from('branches').insert({
        resume_id: data.id,
        name: 'main',
      })

      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Resume created!',
      })
      setNewName('')
      setShowCreate(false)
      navigate(`/resume/${data.id}`)
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to create resume',
      })
    }
  }

  const handleDelete = async (resumeId) => {
    if (!confirm('Delete this resume and all its versions?')) return
    try {
      const { error } = await supabase.from('resumes').delete().eq('id', resumeId)
      if (error) throw error
      setResumes((prev) => prev.filter((r) => r.id !== resumeId))
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: 'Resume deleted',
      })
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to delete',
      })
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <img src="/logo.png" alt="ResumeLibre" className="h-16 w-auto" style={{ viewTransitionName: 'site-logo' }} />
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600">{profile?.email || user?.email}</span>
            {profile?.role === 'admin' && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded font-medium">
                Admin
              </span>
            )}
            <button
              onClick={() => {
                logout()
                navigate('/login')
              }}
              className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">My Resumes</h2>
          <div className="flex gap-2">
            <TemplateUploader user={user} onUpload={uploadTemplate} />
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition text-sm font-medium"
            >
              <Plus className="w-4 h-4" />
              New Resume
            </button>
          </div>
        </div>

        {showCreate && (
          <div className="mb-6 bg-white border border-gray-200 rounded-lg p-4">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Resume name (e.g., 'Software Engineer Resume')"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3"
            />
            <div className="mb-3">
              <label className="block text-xs text-gray-600 mb-1">Template (optional)</label>
              <select
                value={selectedTemplate?.id || ''}
                onChange={(e) => {
                  const t = templates.find((t) => t.id === e.target.value)
                  selectTemplate(t || null)
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="">No template</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.is_admin_only ? '[Admin] ' : ''}
                    {t.name} ({t.format.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium"
              >
                Create
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <p className="text-gray-400 text-sm">Loading...</p>
        ) : resumes.length === 0 ? (
          <div className="text-center py-16">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 text-sm">
              No resumes yet. Create one to get started!
            </p>
          </div>
        ) : (
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {resumes.map((resume) => (
              <div
                key={resume.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition cursor-pointer group"
                onClick={() => navigate(`/resume/${resume.id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-sm">{resume.name}</h3>
                    <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {new Date(resume.updated_at).toLocaleDateString()}
                    </div>
                    <div className="mt-2 text-xs text-gray-500">
                      Branch: {resume.current_branch}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(resume.id)
                    }}
                    className="text-gray-300 hover:text-red-600 opacity-0 group-hover:opacity-100 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
