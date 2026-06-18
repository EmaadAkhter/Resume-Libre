import { useState } from 'react'
import { GitBranch, Plus, Merge } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { eventBus } from '../lib/eventBus'
import { EVENTS } from '../lib/eventTypes'

export default function BranchManager({ resumeId, user, currentBranch, onBranchChange }) {
  const [branches, setBranches] = useState([])
  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [showMerge, setShowMerge] = useState(false)
  const [mergeSource, setMergeSource] = useState('')

  const fetchBranches = async () => {
    if (!resumeId || !user) return
    const { data } = await supabase.from('branches').select('*').eq('resume_id', resumeId).order('created_at')
    setBranches(data || [])
  }

  useState(() => {
    fetchBranches()
  }, [])

  const handleCreate = async () => {
    if (!newName) return
    try {
      const { error } = await supabase
        .from('branches')
        .insert({ resume_id: resumeId, name: newName })
      if (error) throw error
      eventBus.emit(EVENTS.BRANCH_CREATED, { name: newName })
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: `Branch '${newName}' created`,
      })
      setNewName('')
      setShowCreate(false)
      fetchBranches()
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to create branch',
      })
    }
  }

  const handleMerge = async () => {
    if (!mergeSource) return
    try {
      const { error } = await supabase
        .from('branches')
        .update({ head_version_id: branches.find((b) => b.name === mergeSource)?.head_version_id })
        .eq('resume_id', resumeId)
        .eq('name', currentBranch)
      if (error) throw error
      eventBus.emit(EVENTS.BRANCH_MERGED, { source: mergeSource, target: currentBranch })
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'success',
        message: `Merged '${mergeSource}' into '${currentBranch}'`,
      })
      setShowMerge(false)
      onBranchChange?.(currentBranch)
    } catch (err) {
      eventBus.emit(EVENTS.NOTIFICATION_SHOW, {
        type: 'error',
        message: err.message || 'Failed to merge',
      })
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-gray-500" />
        <h3 className="text-sm font-semibold text-gray-900">Branches</h3>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium"
        >
          <Plus className="w-3 h-3" />
          New
        </button>
        <button
          onClick={() => setShowMerge(!showMerge)}
          className="flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded text-xs font-medium"
        >
          <Merge className="w-3 h-3" />
          Merge
        </button>
      </div>

      {showCreate && (
        <div className="flex gap-2">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="branch-name"
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
          />
          <button
            onClick={handleCreate}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium"
          >
            Create
          </button>
        </div>
      )}

      {showMerge && (
        <div className="flex gap-2">
          <select
            value={mergeSource}
            onChange={(e) => setMergeSource(e.target.value)}
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs bg-white"
          >
            <option value="">Select branch to merge</option>
            {branches
              .filter((b) => b.name !== currentBranch)
              .map((b) => (
                <option key={b.id} value={b.name}>
                  {b.name}
                </option>
              ))}
          </select>
          <button
            onClick={handleMerge}
            disabled={!mergeSource}
            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-medium disabled:opacity-50"
          >
            Merge
          </button>
        </div>
      )}

      <div className="space-y-1">
        {branches.map((b) => (
          <div
            key={b.id}
            className={`flex items-center gap-2 px-2 py-1 rounded text-sm cursor-pointer ${
              b.name === currentBranch ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-100'
            }`}
            onClick={() => onBranchChange?.(b.name)}
          >
            <GitBranch className="w-3 h-3" />
            {b.name}
            {b.name === currentBranch && (
              <span className="ml-auto text-xs text-blue-500">current</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
