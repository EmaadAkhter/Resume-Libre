import { useState } from 'react'
import { Bot, Github, GraduationCap, Linkedin, Plus, X } from 'lucide-react'

const SOURCE_TYPES = {
  github: { label: 'GitHub', Icon: Github, placeholder: 'username' },
  linkedin: {
    label: 'LinkedIn',
    Icon: Linkedin,
    placeholder: 'https://linkedin.com/in/username',
  },
  orcid: { label: 'ORCID', Icon: GraduationCap, placeholder: '0000-0002-1825-0097' },
  huggingface: { label: 'Hugging Face', Icon: Bot, placeholder: 'username' },
}

export default function ProfileSources({ sources, onChange }) {
  const [showMenu, setShowMenu] = useState(false)

  const addSource = (type) => {
    onChange([...sources, { id: crypto.randomUUID(), type, value: '' }])
    setShowMenu(false)
  }

  const updateSource = (id, value) => {
    onChange(sources.map((s) => (s.id === id ? { ...s, value } : s)))
  }

  const removeSource = (id) => {
    onChange(sources.filter((s) => s.id !== id))
  }

  const hasLinkedin = sources.some((s) => s.type === 'linkedin')

  return (
    <div className="space-y-2">
      {sources.map((source) => {
        const { label, Icon, placeholder } = SOURCE_TYPES[source.type]
        return (
          <div key={source.id} className="flex items-center gap-2">
            <span className="w-24 shrink-0 flex items-center gap-1.5 text-xs font-medium text-gray-600">
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </span>
            <input
              type="text"
              value={source.value}
              onChange={(e) => updateSource(source.id, e.target.value)}
              placeholder={placeholder}
              className="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 outline-none text-sm"
            />
            <button
              type="button"
              onClick={() => removeSource(source.id)}
              aria-label={`Remove ${label} profile`}
              className="p-1 text-gray-400 hover:text-red-600 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}

      {hasLinkedin && (
        <p className="text-xs text-gray-500">
          Tip: pasting your LinkedIn text into Additional Information is faster and needs no
          scraping.
        </p>
      )}

      <div className="relative">
        <button
          type="button"
          onClick={() => setShowMenu(!showMenu)}
          className="w-full px-3 py-2 border-2 border-dashed border-gray-300 rounded-lg hover:border-primary-500 hover:bg-primary-50 transition text-gray-600 text-sm font-medium flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add profile
        </button>

        {showMenu && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
            <div className="absolute left-0 mt-2 w-44 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
              {Object.entries(SOURCE_TYPES).map(([type, { label, Icon }]) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => addSource(type)}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition text-left"
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {sources.length === 0 && (
        <p className="text-xs text-gray-500">Add GitHub, LinkedIn, ORCID or Hugging Face</p>
      )}
    </div>
  )
}
