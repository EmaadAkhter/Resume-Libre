export default function MarkdownPreview({ content }) {
  if (!content) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
        No resume to preview yet
      </div>
    )
  }

  const lines = content.split('\n')

  return (
    <div className="w-full h-full overflow-y-auto p-4">
      {lines.map((line, i) => {
        line = line.trim()
        if (!line) return <br key={i} />

        if (line.startsWith('# ')) {
          return (
            <h1 key={i} className="text-2xl font-bold mb-2 text-center">
              {line.substring(2)}
            </h1>
          )
        } else if (line.startsWith('## ')) {
          return (
            <h2 key={i} className="text-xl font-bold mt-4 mb-2 border-b-2 border-gray-800">
              {line.substring(3)}
            </h2>
          )
        } else if (line.startsWith('### ')) {
          return (
            <h3 key={i} className="text-lg font-bold mt-3 mb-1">
              {line.substring(4)}
            </h3>
          )
        } else if (line.startsWith('- ') || line.startsWith('* ')) {
          return (
            <li key={i} className="ml-5">
              {renderInlineLinks(line.substring(2))}
            </li>
          )
        } else {
          return <p key={i} className="mb-2">{renderInlineLinks(line)}</p>
        }
      })}
    </div>
  )
}

function renderInlineLinks(content) {
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
  const parts = []
  let lastIndex = 0
  let match

  while ((match = linkRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.substring(lastIndex, match.index))
    }
    parts.push(
      <a
        key={match.index}
        href={match[2]}
        className="text-blue-600 hover:underline"
        target="_blank"
        rel="noopener noreferrer"
      >
        {match[1]}
      </a>
    )
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < content.length) {
    parts.push(content.substring(lastIndex))
  }

  return parts.length > 0 ? parts : content
}
