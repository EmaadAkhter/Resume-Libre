import { Briefcase, ExternalLink } from 'lucide-react'

// Job-aggregator referral, shown ONLY when the resume has zero failed
// checks. That gate is deliberate: revenue lands on the pass path, so the
// checker can never profit from manufacturing problems — the incentive
// points toward accuracy, not alarm.
//
// Configure with a URL template containing {query}, e.g.
//   VITE_JOB_SEARCH_URL=https://www.adzuna.com/search?q={query}&aid=YOUR_ID
// Unset (the default, including every self-hosted install) → renders
// nothing, so nobody unknowingly sends referral traffic to someone else.
const URL_TEMPLATE = import.meta.env.VITE_JOB_SEARCH_URL || ''
const MAX_SKILLS = 5

export default function JobMatchCta({ report }) {
  if (!URL_TEMPLATE || !report?.summary) return null
  if (report.summary.failed > 0) return null

  // Skills only — never the name, email, or phone. Personal data must not
  // ride in an outbound URL.
  const skills = (report.extracted?.skills?.value || []).slice(0, MAX_SKILLS)
  if (skills.length === 0) return null

  const href = URL_TEMPLATE.replace(
    '{query}',
    encodeURIComponent(skills.join(' '))
  )

  return (
    <div className="mt-6 bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-start gap-3">
        <Briefcase className="w-5 h-5 text-primary-600 shrink-0 mt-0.5" />
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-gray-900">
            Your resume parses cleanly — go use it
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            No failed checks. Here are openings matching the skills an ATS
            reads off your resume:
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {skills.map((skill) => (
              <span
                key={skill}
                className="px-2 py-0.5 text-xs rounded-full bg-primary-50 text-primary-700 border border-primary-200"
              >
                {skill}
              </span>
            ))}
          </div>
          <a
            href={href}
            target="_blank"
            rel="sponsored noopener"
            className="mt-3 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            Browse matching roles
            <ExternalLink className="w-4 h-4" />
          </a>
          <p className="mt-2 text-xs text-gray-400">
            Partner link — we may earn a commission if you apply. Only these
            skill keywords are shared; your resume never leaves this page.
          </p>
        </div>
      </div>
    </div>
  )
}
