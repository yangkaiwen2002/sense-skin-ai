/**
 * AnalysisSummary
 *
 * Displays the backend-computed AI decision analysis for a single skin:
 *   - Valuation label (低估 / 合理 / 高估) with colour coding
 *   - Confidence bar
 *   - Reasons to consider (green)
 *   - Risk factors (amber/red)
 *   - Sub-score breakdown (6 dimensions)
 *
 * Props:
 *   score  — result from GET /api/items/{id}/score
 *   loading — bool
 */

const VALUATION_META = {
  '低估': { color: '#22c55e', bg: 'rgba(34,197,94,0.1)',  border: 'rgba(34,197,94,0.25)',  icon: '▲', desc: '当前价格低于历史均值' },
  '合理': { color: '#4a8ef5', bg: 'rgba(74,142,245,0.1)', border: 'rgba(74,142,245,0.25)', icon: '◈', desc: '价格处于合理区间'       },
  '高估': { color: '#ef4444', bg: 'rgba(239,68,68,0.1)',  border: 'rgba(239,68,68,0.25)',  icon: '▼', desc: '当前价格高于历史均值' },
}

const SUBSCORE_META = {
  rarity:    { label: '稀有度', icon: '◆' },
  exterior:  { label: '品相',   icon: '◇' },
  liquidity: { label: '流动性', icon: '⇌' },
  trend:     { label: '趋势',   icon: '↗' },
  valuation: { label: '估值',   icon: '◎' },
  demand:    { label: '需求',   icon: '◉' },
}

function scoreColor(s) {
  if (s >= 72) return '#22c55e'
  if (s >= 55) return '#4a8ef5'
  if (s >= 38) return '#f5a623'
  return '#ef4444'
}

function SkeletonLine({ w = '100%', h = 12 }) {
  return (
    <div style={{
      width: w, height: h,
      background: 'rgba(255,255,255,0.05)',
      borderRadius: 4,
      animation: 'pulse 1.6s ease infinite',
    }} />
  )
}

export default function AnalysisSummary({ score, loading }) {
  /* ── Loading skeleton ─────────────────────────────── */
  if (loading) {
    return (
      <div style={cardStyle}>
        <SectionHeader />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
          <SkeletonLine />
          <SkeletonLine w="80%" />
          <SkeletonLine w="60%" h={32} />
          <SkeletonLine />
          <SkeletonLine w="90%" />
        </div>
      </div>
    )
  }

  /* ── No data ──────────────────────────────────────── */
  if (!score) {
    return (
      <div style={cardStyle}>
        <SectionHeader />
        <p style={{ fontSize: 12, color: 'var(--text-dim)', textAlign: 'center', padding: '20px 0' }}>
          暂无分析数据
        </p>
      </div>
    )
  }

  const vm     = VALUATION_META[score.valuation_label] || VALUATION_META['合理']
  const confPct = Math.round(score.confidence * 100)

  return (
    <div style={cardStyle}>
      <SectionHeader />

      {/* ── Valuation pill ─────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 14,
      }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          background: vm.bg, border: `1px solid ${vm.border}`,
          borderRadius: 8, padding: '7px 14px',
        }}>
          <span style={{ fontSize: 14, color: vm.color, fontWeight: 800 }}>{vm.icon}</span>
          <div>
            <p style={{ fontSize: 14, fontWeight: 800, color: vm.color, lineHeight: 1 }}>
              {score.valuation_label}
            </p>
            <p style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 2 }}>{vm.desc}</p>
          </div>
        </div>

        {/* Confidence */}
        <div style={{ textAlign: 'right' }}>
          <p style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>置信度</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'flex-end' }}>
            <div style={{
              width: 56, height: 4,
              background: 'rgba(255,255,255,0.07)', borderRadius: 2,
              overflow: 'hidden',
            }}>
              <div style={{
                width: `${confPct}%`, height: '100%',
                background: `linear-gradient(90deg, ${vm.color}80, ${vm.color})`,
                borderRadius: 2, transition: 'width 0.8s ease',
              }} />
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: vm.color }}>{confPct}%</span>
          </div>
        </div>
      </div>

      {/* ── Sub-score grid ─────────────────────────────── */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
        gap: '6px 8px', marginBottom: 16,
        background: 'rgba(0,0,0,0.25)', borderRadius: 8, padding: '10px 12px',
        border: '1px solid rgba(255,255,255,0.05)',
      }}>
        {Object.entries(SUBSCORE_META).map(([key, meta]) => {
          const val = score.subscores?.[key] ?? 0
          const c   = scoreColor(val)
          return (
            <div key={key}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                  {meta.icon} {meta.label}
                </span>
                <span style={{ fontSize: 10, fontWeight: 700, color: c }}>{val}</span>
              </div>
              <div style={{ height: 2, background: 'rgba(255,255,255,0.06)', borderRadius: 1 }}>
                <div style={{
                  height: '100%', width: `${val}%`,
                  background: `linear-gradient(90deg, ${c}70, ${c})`,
                  borderRadius: 1, transition: 'width 0.8s ease',
                }} />
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Reasons ────────────────────────────────────── */}
      {score.reasons_to_buy?.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#22c55e', marginBottom: 7, letterSpacing: '0.04em' }}>
            ✓ 买入理由
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {score.reasons_to_buy.map((r, i) => (
              <div key={i} style={{ display: 'flex', gap: 7, alignItems: 'flex-start' }}>
                <span style={{
                  flexShrink: 0, marginTop: 1,
                  width: 4, height: 4, borderRadius: '50%',
                  background: '#22c55e', display: 'inline-block',
                  boxShadow: '0 0 4px #22c55e80',
                }} />
                <span style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Risks ──────────────────────────────────────── */}
      {score.risks?.length > 0 && (
        <div>
          <p style={{ fontSize: 11, fontWeight: 600, color: '#f5a623', marginBottom: 7, letterSpacing: '0.04em' }}>
            ⚠ 风险因素
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            {score.risks.map((r, i) => (
              <div key={i} style={{ display: 'flex', gap: 7, alignItems: 'flex-start' }}>
                <span style={{
                  flexShrink: 0, marginTop: 1,
                  width: 4, height: 4, borderRadius: '50%',
                  background: '#f5a623', display: 'inline-block',
                }} />
                <span style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Sub-components ──────────────────────────────────── */
function SectionHeader() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
      <div style={{
        width: 24, height: 24, borderRadius: 6,
        background: 'linear-gradient(135deg, rgba(74,142,245,0.2), rgba(139,92,246,0.2))',
        border: '1px solid rgba(74,142,245,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 12,
      }}>◎</div>
      <div>
        <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
          AI 决策分析
        </p>
        <p style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 2 }}>
          6 维度综合评估
        </p>
      </div>
      <div style={{
        marginLeft: 'auto',
        fontSize: 9, color: '#4a8ef5',
        background: 'rgba(74,142,245,0.08)', border: '1px solid rgba(74,142,245,0.18)',
        borderRadius: 4, padding: '2px 7px', letterSpacing: '0.04em', fontWeight: 600,
      }}>
        SENSE AI
      </div>
    </div>
  )
}

const cardStyle = {
  background: '#0f1520',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 12,
  padding: '16px 16px 18px',
}
