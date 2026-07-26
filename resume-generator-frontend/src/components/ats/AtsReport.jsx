import {
  AlertTriangle,
  Calendar,
  CheckCircle,
  ChevronDown,
  Github,
  Lightbulb,
  Linkedin,
  LayoutList,
  Mail,
  Phone,
  User,
  Wrench,
  XCircle,
} from 'lucide-react'

import { BandGauge, CategoryBar, OutcomeBar, ThresholdMeter } from './AtsCharts'

// Status is a reserved scale and always ships icon + label, never color alone.
const STATUS_META = {
  pass: {
    Icon: CheckCircle,
    text: 'text-emerald-600',
    chip: 'bg-emerald-50 text-emerald-700',
    label: 'Pass',
  },
  warn: {
    Icon: AlertTriangle,
    text: 'text-amber-600',
    chip: 'bg-amber-50 text-amber-700',
    label: 'Warning',
  },
  fail: {
    Icon: XCircle,
    text: 'text-red-600',
    chip: 'bg-red-50 text-red-700',
    label: 'Fail',
  },
  info: {
    Icon: Lightbulb,
    text: 'text-blue-600',
    chip: 'bg-blue-50 text-blue-700',
    label: 'Suggestion',
  },
}

// Friendly names — the API's check ids are machine identifiers.
// Named export: the editor reuses these to build regeneration feedback.
export const CHECK_TITLES = {
  'extraction-agreement': 'Text extraction agreement',
  columns: 'Column layout',
  tables: 'Tables',
  'encoding-sanity': 'Fonts & encoding',
  'content-completeness': 'Content completeness',
  'section-headers': 'Section headings',
  'contact-info': 'Contact info',
  'page-count': 'Page count',
  'resume-length': 'Resume length',
  'font-count': 'Font variety',
  'tiny-font': 'Tiny font sizes',
  images: 'Images & graphics',
  'special-characters': 'Special characters',
  margins: 'Page margins',
  'link-only-contact': 'Clickable-link contacts',
  'header-footer-contact': 'Header/footer contact',
  'scanned-pdf': 'Scanned PDF',
  'writing-tips': 'Writing suggestions',
  'bullet-density': 'Bullet density',
  'quantified-bullets': 'Quantified achievements',
  'long-bullets': 'Overlong bullets',
  'repeated-verbs': 'Action-verb variety',
  'first-person': 'First-person pronouns',
  buzzwords: 'Cliché phrases',
  'all-caps-lines': 'ALL-CAPS lines',
  'duplicate-bullets': 'Duplicate bullets',
  'date-format-consistency': 'Date format consistency',
  'hyphenation-breaks': 'Hyphenation breaks',
  'orphan-headings': 'Empty sections',
  'multiple-emails': 'Multiple emails',
  'broken-links': 'Broken links',
  'file-size': 'File size',
  'encrypted-pdf': 'PDF encryption',
  filename: 'File name',
}

// Category labels in fixed display order; groups holding a warn/fail float
// above all-pass groups at render time.
export const CATEGORY_META = {
  extraction: 'Extraction',
  layout: 'Layout',
  typography: 'Typography',
  contact: 'Contact & Links',
  content: 'Content & Writing',
  file: 'File',
}
const CATEGORY_ORDER = Object.keys(CATEGORY_META)

const FIELD_META = {
  email: { label: 'Email', Icon: Mail },
  phone: { label: 'Phone', Icon: Phone },
  linkedin: { label: 'LinkedIn', Icon: Linkedin },
  github: { label: 'GitHub', Icon: Github },
  name: { label: 'Name', Icon: User },
  dates: { label: 'Dates', Icon: Calendar },
  sections: { label: 'Sections', Icon: LayoutList },
  skills: { label: 'Skills', Icon: Wrench },
}

const CONFIDENCE_META = {
  high: { dot: 'bg-emerald-500', label: 'high confidence' },
  medium: { dot: 'bg-amber-400', label: 'AI-assisted' },
  low: { dot: 'bg-amber-500', label: 'low confidence' },
}

function StatTile({ count, label, tone }) {
  const tones = {
    pass: 'text-emerald-600 bg-emerald-50 border-emerald-100',
    warn: 'text-amber-600 bg-amber-50 border-amber-100',
    fail: 'text-red-600 bg-red-50 border-red-100',
  }
  const { Icon } = STATUS_META[tone]
  return (
    <div className={`flex-1 rounded-xl border px-4 py-3 ${tones[tone]}`}>
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4" />
        {/* proportional figures on tile values — no tabular-nums at display size */}
        <span className="text-2xl font-semibold text-gray-900">{count}</span>
      </div>
      <div className="text-xs text-gray-600 mt-0.5">{label}</div>
    </div>
  )
}

function SummaryPills({ summary }) {
  return (
    <div className="flex items-center gap-2 text-xs font-medium">
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 text-emerald-700 px-2 py-0.5">
        <CheckCircle className="w-3 h-3" /> {summary.passed}
      </span>
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 text-amber-700 px-2 py-0.5">
        <AlertTriangle className="w-3 h-3" /> {summary.warned}
      </span>
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 text-red-700 px-2 py-0.5">
        <XCircle className="w-3 h-3" /> {summary.failed}
      </span>
    </div>
  )
}

function CheckRow({ check }) {
  const meta = STATUS_META[check.status] || STATUS_META.warn
  const { Icon } = meta
  const needsAttention = check.status !== 'pass'
  return (
    <details
      className="group bg-white rounded-xl border border-gray-200"
      open={needsAttention}
    >
      <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
        <Icon className={`w-5 h-5 shrink-0 ${meta.text}`} />
        <span className="flex-1 text-sm font-medium text-gray-900">
          {CHECK_TITLES[check.id] || check.id}
        </span>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${meta.chip}`}>
          {meta.label}
        </span>
        <ChevronDown className="w-4 h-4 text-gray-400 transition-transform group-open:rotate-180" />
      </summary>
      <div className="px-4 pb-3 pl-12">
        <p className="text-sm text-gray-600">{check.reason}</p>
        {check.metric?.kind === 'ratio' && <ThresholdMeter metric={check.metric} />}
        {check.metric?.kind === 'band' && <BandGauge metric={check.metric} />}
        {needsAttention && check.fix && check.fix !== 'No action needed.' && (
          <p className="mt-1.5 text-sm text-gray-700">
            <span className="font-medium">Fix:</span> {check.fix}
          </p>
        )}
      </div>
    </details>
  )
}

// Bucket checks by category, keeping check order within each group. Groups
// with a warning/failure sort ahead of all-pass groups; within each tier the
// fixed CATEGORY_ORDER holds (Array.sort is stable). Unknown categories from
// older cached reports land in a trailing "Other" bucket instead of vanishing.
function groupByCategory(checks) {
  const groups = []
  for (const check of checks) {
    const category = check.category || 'other'
    let group = groups.find((g) => g.category === category)
    if (!group) {
      group = { category, checks: [] }
      groups.push(group)
    }
    group.checks.push(check)
  }
  const orderOf = (category) => {
    const index = CATEGORY_ORDER.indexOf(category)
    return index === -1 ? CATEGORY_ORDER.length : index
  }
  const needsAttention = (group) =>
    group.checks.some((c) => c.status === 'warn' || c.status === 'fail') ? 0 : 1
  return groups.sort(
    (a, b) =>
      needsAttention(a) - needsAttention(b) || orderOf(a.category) - orderOf(b.category)
  )
}

function CategoryGroup({ category, checks }) {
  // Open when anything inside needs a look (warn/fail/info); a group of
  // pure passes collapses to its summary row.
  const hasNonPass = checks.some((c) => c.status !== 'pass')
  return (
    <details className="group/cat" open={hasNonPass}>
      <summary className="flex items-center gap-3 px-1 py-1.5 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden">
        <span className="flex-1 text-sm font-semibold text-gray-900">
          {CATEGORY_META[category] || 'Other'}
        </span>
        <CategoryBar checks={checks} />
        <span className="text-xs text-gray-500">
          {checks.length} {checks.length === 1 ? 'check' : 'checks'}
        </span>
        <ChevronDown className="w-4 h-4 text-gray-400 transition-transform group-open/cat:rotate-180" />
      </summary>
      <div className="mt-2 space-y-3">
        {checks.map((check) => (
          <CheckRow key={check.id} check={check} />
        ))}
      </div>
    </details>
  )
}

function FieldCard({ field, result }) {
  const meta = FIELD_META[field] || { label: field, Icon: LayoutList }
  const conf = CONFIDENCE_META[result.confidence] || CONFIDENCE_META.low
  const notFound = result.value == null && !result.failed
  const value = Array.isArray(result.value) ? result.value : result.value

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-3.5">
      <div className="flex items-center gap-2 text-xs text-gray-500 mb-1.5">
        <meta.Icon className="w-3.5 h-3.5" />
        {meta.label}
        {!notFound && (
          <span className="ml-auto inline-flex items-center gap-1.5 text-gray-500">
            <span className={`w-2 h-2 rounded-full ${conf.dot}`} />
            {conf.label}
          </span>
        )}
      </div>
      {field === 'skills' && Array.isArray(value) ? (
        <div className="flex flex-wrap gap-1.5">
          {value.map((skill) => (
            <span
              key={skill}
              className="px-2 py-0.5 text-xs rounded-full bg-primary-50 text-primary-700 border border-primary-200"
            >
              {skill}
            </span>
          ))}
        </div>
      ) : value ? (
        <p className="text-sm text-gray-900 break-words">
          {Array.isArray(value) ? value.join(', ') : value}
        </p>
      ) : result.failed ? (
        <p className="flex items-center gap-1 text-sm text-red-600">
          <XCircle className="w-4 h-4 shrink-0" />
          couldn&apos;t parse
        </p>
      ) : (
        <p className="text-sm text-gray-400">not found</p>
      )}
    </div>
  )
}

/**
 * Visual parseability report, shared by the ATS page and the editor panel.
 * compact: summary pills + only non-pass checks, for the editor sidebar.
 */
export default function AtsReport({ report, compact = false }) {
  if (!report) return null
  const { summary, checks, extracted } = report
  const visibleChecks = compact
    ? checks.filter((c) => c.status !== 'pass')
    : checks

  return (
    <div className={compact ? 'space-y-2' : 'space-y-6'}>
      {compact ? (
        <SummaryPills summary={summary} />
      ) : (
        <div className="space-y-3">
          <div className="flex gap-3">
            <StatTile count={summary.passed} label="Passed" tone="pass" />
            <StatTile count={summary.warned} label="Warnings" tone="warn" />
            <StatTile count={summary.failed} label="Failed" tone="fail" />
          </div>
          <OutcomeBar summary={summary} />
        </div>
      )}

      {compact ? (
        <div className="space-y-2">
          {visibleChecks.map((check) => (
            <CheckRow key={check.id} check={check} />
          ))}
          {visibleChecks.length === 0 && (
            <p className="text-xs text-emerald-700 flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> All parseability checks pass
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {groupByCategory(checks).map((group) => (
            <CategoryGroup
              key={group.category}
              category={group.category}
              checks={group.checks}
            />
          ))}
        </div>
      )}

      {!compact && extracted && (
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-3">
            What an ATS would extract
          </h3>
          <div className="grid sm:grid-cols-2 gap-3">
            {Object.entries(extracted).map(([field, result]) => (
              <FieldCard key={field} field={field} result={result} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
