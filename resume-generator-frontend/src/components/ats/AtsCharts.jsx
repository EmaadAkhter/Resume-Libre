import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

/**
 * Tiny threshold-anchored charts for the parseability report.
 *
 * Product rule: no aggregate/blended score anywhere — every mark shows a
 * MEASURED value against its labeled thresholds. Design rules: thin marks,
 * 2px white gaps between adjacent filled segments, values and labels in
 * gray ink (never the series color), and status hues never appear without
 * an icon or text label beside them.
 */

const OUTCOME_SEGMENTS = [
  {
    key: 'passed',
    fill: 'bg-emerald-500',
    Icon: CheckCircle,
    iconColor: 'text-emerald-600',
    label: 'passed',
  },
  {
    key: 'warned',
    fill: 'bg-amber-400',
    Icon: AlertTriangle,
    iconColor: 'text-amber-600',
    label: 'warned',
  },
  {
    key: 'failed',
    fill: 'bg-red-500',
    Icon: XCircle,
    iconColor: 'text-red-600',
    label: 'failed',
  },
]

/**
 * Micro stacked bar for one category group's pass/warn/fail mix, sized to
 * sit inline in a group header. Informational checks are suggestions, not
 * outcomes, so they are excluded from the segments. The min-width keeps a
 * lone check visible; the group header text carries the accessible counts.
 */
export function CategoryBar({ checks }) {
  if (!checks?.length) return null
  const counts = { passed: 0, warned: 0, failed: 0 }
  for (const check of checks) {
    if (check.status === 'pass') counts.passed += 1
    else if (check.status === 'warn') counts.warned += 1
    else if (check.status === 'fail') counts.failed += 1
  }
  const total = counts.passed + counts.warned + counts.failed
  if (total === 0) return null
  return (
    <div
      className="flex gap-0.5 h-2 w-20 shrink-0 rounded-full overflow-hidden"
      role="img"
      aria-label={`${counts.passed} passed, ${counts.warned} warned, ${counts.failed} failed`}
    >
      {OUTCOME_SEGMENTS.filter((s) => counts[s.key] > 0).map((s) => (
        <div
          key={s.key}
          className={`h-full ${s.fill}`}
          style={{ flex: counts[s.key], minWidth: '0.375rem' }}
        />
      ))}
    </div>
  )
}

/** Stacked pass/warn/fail counts as one thin bar, legend beneath. */
export function OutcomeBar({ summary }) {
  if (!summary) return null
  const total = OUTCOME_SEGMENTS.reduce((sum, s) => sum + (summary[s.key] || 0), 0)
  if (total === 0) return null
  return (
    <div>
      <div
        className="flex gap-0.5 h-3 rounded-full overflow-hidden"
        role="img"
        aria-label={`${summary.passed} passed, ${summary.warned} warned, ${summary.failed} failed`}
      >
        {OUTCOME_SEGMENTS.filter((s) => summary[s.key] > 0).map((s) => (
          <div key={s.key} className={`h-full ${s.fill}`} style={{ flex: summary[s.key] }} />
        ))}
      </div>
      <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
        {OUTCOME_SEGMENTS.map(({ key, Icon, iconColor, label }) => (
          <span key={key} className="inline-flex items-center gap-1">
            <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
            {summary[key]} {label}
          </span>
        ))}
      </div>
    </div>
  )
}

// Shared frame: value label above, zoned track with a 2px gray-900 marker,
// tiny threshold tick labels underneath. Positions are fractions of the track.
function MeasureTrack({ zones, marker, ticks }) {
  const pct = (fraction) => `${Math.min(100, Math.max(0, fraction * 100))}%`
  // keep edge-hugging labels from clipping outside the track
  const labelLeft = (fraction) => `clamp(0.875rem, ${pct(fraction)}, calc(100% - 0.875rem))`
  return (
    <div className="mt-3 max-w-md">
      <div className="relative h-4">
        <span
          className="absolute -translate-x-1/2 whitespace-nowrap text-xs font-medium text-gray-900"
          style={{ left: labelLeft(marker.at) }}
        >
          {marker.label}
        </span>
      </div>
      <div className="relative">
        <div className="flex h-2.5 rounded overflow-hidden">
          {zones.map((zone) => (
            <div
              key={`${zone.from}-${zone.cls}`}
              className={zone.cls}
              style={{ width: pct(zone.to - zone.from) }}
            />
          ))}
        </div>
        <div
          className="absolute -top-0.5 -bottom-0.5 w-0.5 rounded-full bg-gray-900 -translate-x-1/2"
          style={{ left: pct(marker.at) }}
        />
      </div>
      <div className="relative h-3.5 mt-0.5">
        {ticks.map((tick) => (
          <span
            key={tick.label}
            className="absolute -translate-x-1/2 whitespace-nowrap text-[10px] text-gray-500"
            style={{ left: labelLeft(tick.at) }}
          >
            {tick.label}
          </span>
        ))}
      </div>
    </div>
  )
}

/**
 * Ratio metric (0–1) against its labeled thresholds.
 * warn_below/fail_below (agreement, completeness): red zone below fail,
 * amber up to warn, emerald above. warn_above (tiny-font): emerald below
 * the threshold, amber above it.
 */
export function ThresholdMeter({ metric }) {
  if (!metric || typeof metric.value !== 'number') return null
  let zones
  let ticks
  if (metric.warn_above != null) {
    zones = [
      { from: 0, to: metric.warn_above, cls: 'bg-emerald-100' },
      { from: metric.warn_above, to: 1, cls: 'bg-amber-100' },
    ]
    ticks = [{ at: metric.warn_above, label: metric.warn_above.toFixed(2) }]
  } else {
    const fail = metric.fail_below ?? 0
    zones = [
      fail > 0 && { from: 0, to: fail, cls: 'bg-red-100' },
      { from: fail, to: metric.warn_below, cls: 'bg-amber-100' },
      { from: metric.warn_below, to: 1, cls: 'bg-emerald-100' },
    ].filter(Boolean)
    ticks = [
      fail > 0 && { at: fail, label: fail.toFixed(2) },
      { at: metric.warn_below, label: metric.warn_below.toFixed(2) },
    ].filter(Boolean)
  }
  return (
    <MeasureTrack
      zones={zones}
      ticks={ticks}
      marker={{ at: metric.value, label: metric.value.toFixed(2) }}
    />
  )
}

/**
 * Band metric: measured count on a 0→max scale with the acceptable
 * [low, high] band shaded emerald.
 */
export function BandGauge({ metric }) {
  if (!metric || typeof metric.value !== 'number') return null
  // Scale to the band, not a fixed corpus: 4/3 of the upper bound keeps the
  // acceptable band at ~75% of the track for words (900 → 1200, unchanged
  // from the original constant) and MB (2 → 2.67) alike.
  const max = Math.max((metric.high || 1) * (4 / 3), metric.value * 1.1)
  const at = (v) => Math.min(1, Math.max(0, v / max))
  const unit = metric.unit ? ` ${metric.unit}` : ''
  const zones = [
    { from: 0, to: at(metric.low), cls: 'bg-gray-100' },
    { from: at(metric.low), to: at(metric.high), cls: 'bg-emerald-100' },
    { from: at(metric.high), to: 1, cls: 'bg-gray-100' },
  ]
  const ticks = [
    { at: at(metric.low), label: String(metric.low) },
    { at: at(metric.high), label: String(metric.high) },
  ]
  return (
    <MeasureTrack
      zones={zones}
      ticks={ticks}
      marker={{ at: at(metric.value), label: `${metric.value}${unit}` }}
    />
  )
}
