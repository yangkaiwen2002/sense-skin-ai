/**
 * Score — the single, canonical score visualization used everywhere in the app.
 * Replaces three previously-duplicated implementations (grid-card badge,
 * item-detail hero ring, opportunity-card mini ring) that each carried their
 * own color thresholds.
 */

export function computeScores(platforms) {
  const best = platforms?.[0]
  if (!best) return null

  const liquidity = Math.round(Math.max(0, Math.min(100, best.liquidity_score ?? 40)))
  const vol = best.volatility_7d ?? 0.04
  const stability = Math.round(Math.max(0, Math.min(100, (1 - vol * 12) * 100)))
  const ret7d = best.return_7d ?? 0
  const trend = Math.round(Math.max(0, Math.min(100, 50 + ret7d * 300)))
  const cur = best.current_price ?? 0
  const avg30 = best.avg_30d ?? cur
  const valueDelta = avg30 > 0 ? (avg30 - cur) / avg30 : 0
  const value = Math.round(Math.max(0, Math.min(100, 50 + valueDelta * 300)))
  const overall = Math.round(0.3 * value + 0.25 * liquidity + 0.25 * stability + 0.2 * trend)

  return {
    overall, value, liquidity, stability, trend,
    notes: {
      value: cur && avg30 ? `${valueDelta >= 0 ? '低于' : '高于'}均价 ${Math.abs(valueDelta * 100).toFixed(1)}%` : '—',
      liquidity: best.liquidity_score != null ? `${best.liquidity_score.toFixed(0)}/100` : '—',
      stability: `波动率 ${(vol * 100).toFixed(1)}%`,
      trend: best.return_7d != null ? `7日 ${ret7d >= 0 ? '+' : ''}${(ret7d * 100).toFixed(1)}%` : '—',
    },
  }
}

export function scoreColor(s) {
  if (s == null) return 'var(--text-dim)'
  if (s >= 70) return 'var(--buy)'
  if (s >= 50) return 'var(--accent-strong)'
  if (s >= 35) return 'var(--gold)'
  return 'var(--avoid)'
}

export function scoreLabel(s) {
  if (s >= 80) return '强烈推荐'
  if (s >= 65) return '值得关注'
  if (s >= 50) return '中性观望'
  if (s >= 35) return '谨慎'
  return '风险较高'
}

/**
 * Circular score ring. One implementation, sized via `size`.
 * `variant="badge"` renders the compact filled-disc treatment used as a
 * corner overlay on grid cards; default renders the outlined ring used in
 * hero/detail contexts.
 */
export function ScoreRing({ score, size = 100, variant = 'ring', showLabel = true, className = '' }) {
  if (score == null) return null
  const c = scoreColor(score)
  const label = scoreLabel(score)
  const stroke = variant === 'badge' ? Math.max(3, size * 0.11) : Math.max(6, size * 0.075)
  const r = (size - stroke) / 2
  const circ = 2 * Math.PI * r
  const dash = (Math.max(0, Math.min(100, score)) / 100) * circ

  return (
    <div className={`flex flex-col items-center gap-1.5 shrink-0 ${className}`}>
      <div className="relative" style={{ width: size, height: size }}>
        {variant !== 'badge' && (
          <div
            className="absolute pointer-events-none rounded-full"
            style={{ inset: -8, background: `radial-gradient(circle, ${c}22 0%, transparent 70%)` }}
          />
        )}
        <svg width={size} height={size} className="block -rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke={variant === 'badge' ? 'rgba(0,0,0,0.55)' : 'rgba(255,255,255,0.07)'}
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke={c} strokeWidth={stroke} strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            style={{ transition: 'stroke-dasharray 0.8s var(--ease-standard)' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-tabular font-extrabold leading-none"
            style={{ fontSize: size * (variant === 'badge' ? 0.32 : 0.26), color: c, letterSpacing: '-0.02em' }}
          >
            {score}
          </span>
          {variant !== 'badge' && size >= 70 && (
            <span className="text-[9px] text-white/30 tracking-widest mt-1">AI SCORE</span>
          )}
        </div>
      </div>
      {showLabel && variant !== 'badge' && size >= 70 && (
        <span className="text-[11px] font-semibold" style={{ color: c }}>{label}</span>
      )}
    </div>
  )
}

/** Small filled score dot for tight spaces (search results, table rows). */
export function ScoreDot({ score, size = 8 }) {
  if (score == null) return null
  const c = scoreColor(score)
  return (
    <span
      className="inline-block rounded-full shrink-0"
      style={{ width: size, height: size, background: c, boxShadow: `0 0 6px ${c}80` }}
    />
  )
}

/** Horizontal score bar used in lists/rows. */
export function ScoreBar({ label, value, note }) {
  const c = scoreColor(value)
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[var(--text-secondary)]">{label}</span>
        <div className="flex items-center gap-1.5">
          {note && <span className="text-[10px] text-[var(--text-dim)]">{note}</span>}
          <span className="text-xs font-bold font-tabular" style={{ color: c }}>{value}</span>
        </div>
      </div>
      <div className="h-[3px] rounded-full bg-white/[0.07] overflow-hidden">
        <div
          className="score-bar-fill h-full rounded-full"
          style={{ width: `${value}%`, background: `linear-gradient(90deg, ${c}80, ${c})` }}
        />
      </div>
    </div>
  )
}

/** The compact 4-metric grid shown below the hero on ItemDetail. */
export function CompactScoreBars({ scores }) {
  if (!scores) return null
  const items = [
    { key: 'value', label: '价值', note: scores.notes?.value },
    { key: 'liquidity', label: '流动性', note: scores.notes?.liquidity },
    { key: 'stability', label: '稳定性', note: scores.notes?.stability },
    { key: 'trend', label: '趋势', note: scores.notes?.trend },
  ]
  return (
    <div className="grid grid-cols-2 gap-x-5 gap-y-2.5">
      {items.map(({ key, label, note }) => (
        <ScoreBar key={key} label={label} value={scores[key]} note={note} />
      ))}
    </div>
  )
}
