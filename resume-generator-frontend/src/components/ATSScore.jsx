import { Loader2 } from 'lucide-react'

const IMPORTANCE_STYLES = {
  high: 'bg-red-50 text-red-700 border-red-200',
  medium: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  low: 'bg-gray-50 text-gray-600 border-gray-200',
}

export default function ATSScore({ result, loading, error }) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-5 flex items-center gap-2 text-sm text-gray-500">
        <Loader2 className="w-4 h-4 animate-spin text-primary-600" />
        Analyzing ATS match...
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-5 text-sm text-gray-500">
        {error}
      </div>
    )
  }

  if (!result) return null

  const percent = result.match_percent
  const barColor =
    percent >= 75 ? 'bg-green-500' : percent >= 50 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900">{percent}% match</h3>
      <div className="mt-2 h-2 w-full bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${percent}%` }} />
      </div>

      {result.matched_keywords?.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Matched keywords
          </h4>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {result.matched_keywords.map((keyword) => (
              <span
                key={keyword}
                className="px-2 py-0.5 text-xs rounded-full bg-green-50 text-green-700 border border-green-200"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {result.missing_keywords?.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Missing keywords
          </h4>
          <div className="mt-2 space-y-3">
            {result.missing_keywords.map((gap) => (
              <div key={gap.keyword}>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-gray-900">{gap.keyword}</span>
                  <span
                    className={`px-1.5 py-0.5 text-xs rounded border ${
                      IMPORTANCE_STYLES[gap.importance] || IMPORTANCE_STYLES.low
                    }`}
                  >
                    {gap.importance}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{gap.suggestion}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.summary && <p className="mt-4 text-sm text-gray-600">{result.summary}</p>}
    </div>
  )
}
