export default function MarkdownEditor({ content, onChange }) {
  return (
    <textarea
      value={content}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-full p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-mono text-sm resize-none"
      placeholder="Resume markdown will appear here..."
      spellCheck={false}
    />
  )
}
