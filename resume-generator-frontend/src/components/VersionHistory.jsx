import { useState, useEffect, useCallback } from 'react'
import { GitCommit, Tag, Clock, Eye } from 'lucide-react'
import { supabase } from '../lib/supabase'

export default function VersionHistory({ resumeId, user, onViewVersion }) {
  const [versions, setVersions] = useState([])
  const [branches, setBranches] = useState([])
  const [tags, setTags] = useState([])
  const [selectedBranch, setSelectedBranch] = useState('main')
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    if (!resumeId || !user) return
    setLoading(true)
    try {
      const [versionsRes, branchesRes, tagsRes] = await Promise.all([
        supabase
          .from('resume_versions')
          .select('*')
          .eq('resume_id', resumeId)
          .eq('branch_name', selectedBranch)
          .order('created_at', { ascending: false }),
        supabase.from('branches').select('*').eq('resume_id', resumeId),
        supabase.from('tags').select('*').eq('resume_id', resumeId),
      ])

      setVersions(versionsRes.data || [])
      setBranches(branchesRes.data || [])
      setTags(tagsRes.data || [])
    } catch (err) {
      console.error('Failed to fetch history:', err)
    } finally {
      setLoading(false)
    }
  }, [resumeId, user, selectedBranch])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <GitCommit className="w-4 h-4 text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-900">Version History</h3>
      </div>

      <select
        value={selectedBranch}
        onChange={(e) => setSelectedBranch(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
      >
        {branches.map((b) => (
          <option key={b.id} value={b.name}>
            {b.name}
          </option>
        ))}
      </select>

      {loading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : versions.length === 0 ? (
        <p className="text-sm text-gray-400">No versions yet. Save your resume to create the first commit.</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {versions.map((v, i) => {
            const versionTags = tags.filter((t) => t.version_id === v.id)
            return (
              <div
                key={v.id}
                className={`p-3 rounded-lg border text-sm cursor-pointer hover:bg-gray-50 ${
                  i === 0 ? 'border-blue-300 bg-blue-50' : 'border-gray-200'
                }`}
                onClick={() => onViewVersion?.(v)}
              >
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    {new Date(v.created_at).toLocaleString()}
                  </span>
                  {i === 0 && (
                    <span className="ml-auto text-xs text-blue-600 font-medium">HEAD</span>
                  )}
                </div>
                {v.message && <p className="mt-1 text-gray-700">{v.message}</p>}
                {versionTags.length > 0 && (
                  <div className="mt-1 flex gap-1 flex-wrap">
                    {versionTags.map((t) => (
                      <span
                        key={t.id}
                        className="flex items-center gap-1 px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded"
                      >
                        <Tag className="w-2 h-2" />
                        {t.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
