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
    }
  }
}

function scoreColor(s) {
  if (s >= 72) return '#22c55e'
  if (s >= 52) return '#f5a623'
  if (s >= 35) return '#f97316'
  return '#ef4444'
}

function scoreLabel(s) {
  if (s >= 80) return '强烈推荐'
  if (s >= 65) return '值得关注'
  if (s >= 50) return '中性观望'
  if (s >= 35) return '谨慎'
  return '风险较高'
}

/* ── Big score ring used in ItemDetail hero ── */
export function ScoreRing({ score, size = 110 }) {
  if (score == null) return null
  const c = scoreColor(score)
  const label = scoreLabel(score)
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const dash = (score / 100) * circ

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flexShrink: 0 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        {/* outer glow */}
        <div style={{
          position: 'absolute', inset: -8,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${c}22 0%, transparent 70%)`,
          pointerEvents: 'none',
        }} />
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)', display: 'block' }}>
          {/* track */}
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
          {/* fill */}
          <circle
            cx={size/2} cy={size/2} r={r}
            fill="none"
            stroke={c}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            style={{ filter: `drop-shadow(0 0 8px ${c}90)`, transition: 'stroke-dasharray 1s cubic-bezier(.16,1,.3,1)' }}
          />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: size * 0.28, fontWeight: 900, color: c, lineHeight: 1, letterSpacing: '-0.03em' }}>
            {score}
          </span>
          <span style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.08em', marginTop: 2 }}>
            AI SCORE
          </span>
        </div>
      </div>
      <span style={{ fontSize: 11, fontWeight: 600, color: c }}>
        {label}
      </span>
    </div>
  )
}

/* ── Compact 4-bar grid used below hero ── */
export function CompactScoreBars({ scores }) {
  if (!scores) return null
  const items = [
    { key: 'value',     label: '价值',  note: scores.notes?.value     },
    { key: 'liquidity', label: '流动性', note: scores.notes?.liquidity },
    { key: 'stability', label: '稳定性', note: scores.notes?.stability },
    { key: 'trend',     label: '趋势',  note: scores.notes?.trend     },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 20px' }}>
      {items.map(({ key, label, note }) => {
        const s = scores[key]
        const c = scoreColor(s)
        return (
          <div key={key}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{label}</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                {note && <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>{note}</span>}
                <span style={{ fontSize: 12, fontWeight: 700, color: c }}>{s}</span>
              </div>
            </div>
            <div style={{ height: 3, background: 'rgba(255,255,255,0.07)', borderRadius: 2, overflow: 'hidden' }}>
              <div
                className="score-bar-fill"
                style={{ height: '100%', width: `${s}%`, background: `linear-gradient(90deg, ${c}80, ${c})`, borderRadius: 2 }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

/* ── Full panel (for standalone use) ── */
export default function ScorePanel({ scores }) {
  if (!scores) return <p style={{ color: 'var(--text-dim)', fontSize: 12, textAlign: 'center', padding: 16 }}>暂无评分</p>
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 20 }}>
        <ScoreRing score={scores.overall} />
      </div>
      <CompactScoreBars scores={scores} />
    </div>
  )
}
