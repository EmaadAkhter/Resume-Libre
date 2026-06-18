import { FileText, FileCode, Lock } from 'lucide-react'

export default function TemplatePicker({ templates, selected, onSelect, user }) {
  return (
    <select
      value={selected?.id || ''}
      onChange={(e) => {
        const template = templates.find((t) => t.id === e.target.value)
        onSelect(template || null)
      }}
      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-sm bg-white"
    >
      <option value="">No template (AI decides format)</option>
      {templates.map((t) => (
        <option key={t.id} value={t.id}>
          {t.is_admin_only ? '[Admin] ' : ''}
          {t.name} ({t.format.toUpperCase()})
        </option>
      ))}
    </select>
  )
}
