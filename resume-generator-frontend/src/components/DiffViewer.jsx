import { X } from 'lucide-react'

export default function DiffViewer({ diff, onClose }) {
  if (!diff) return null

  const lines = diff.split('\n')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Version Diff</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>
        <div className="flex-1 overflow-auto p-4">
          <pre className="text-xs font-mono">
            {lines.map((line, i) => {
              let className = 'text-gray-700'
              if (line.startsWith('+++') || line.startsWith('---')) {
                className = 'text-gray-500 font-bold'
              } else if (line.startsWith('@@')) {
                className = 'text-blue-600'
              } else if (line.startsWith('+')) {
                className = 'text-green-700 bg-green-50'
              } else if (line.startsWith('-')) {
                className = 'text-red-700 bg-red-50'
              }
              return (
                <div key={i} className={`${className} px-2`}>
                  {line || ' '}
                </div>
              )
            })}
          </pre>
        </div>
      </div>
    </div>
  )
}
