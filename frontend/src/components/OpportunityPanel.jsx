/**
 * OpportunityPanel — event-aware opportunity cards with decision badges.
 *
 * Each card now shows:
 *   - Decision badge (BUY / WATCH / HOLD) from the decision engine
 *   - AI score ring
 *   - Price + valuation label
 *   - Top reason
 *   - Event context (if any event is driving the signal)
 */

import { useNavigate } from 'react-router-dom'
import { formatCNY } from '../utils/formatters'

const RARITY_COLOR = {
  '违禁': '#e4ae39', '隐秘': '#eb4b4b', '保密': '#d32ce6',
  '受限': '#8847ff', '军规': '#4b69ff', '精工': '#5e98d9',
}
const REC_STYLES = {
  BUY:   { bg: '#22c55e', text: '买入', glow: 'rgba(34,197,94,0.3)' },
  WATCH: { bg: '#4a8ef5', text: '观望', glow: 'rgba(74,142,245,0.3)' },
  HOLD:  { bg: '#f5a623', text: '持有', glow: 'rgba(245,166,35,0.3)' },
  AVOID: { bg: '#ef4444', text: '规避', glow: 'rgba(239,68,68,0.3)' },
}
const VAL_COLOR = { '低估': '#22c55e', '合理': '#4a8ef5', '高估': '#ef4444' }

function scoreColor(s) {
  if (s >= 72) return '#22c55e'
  if (s >= 55) return '#4a8ef5'
  if (s >= 38) return '#f5a623'
  return '#ef4444'
}

function MiniRing({ score, size = 44 }) {
  const c    = scoreColor(score)
  const r    = (size - 6) / 2
  const circ = 2 * Math.PI * r
  const dash = (score / 100) * circ

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)', display: 'block' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="5" />
        <circle
          cx={size/2} cy={size/2} r={r}
          fill="none" stroke={c} strokeWidth="5" strokeLinecap="round"
          strokeDasharray={`${dash} ${circ}`}
          style={{ filter: `drop-shadow(0 0 5px ${c}80)` }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 11, fontWeight: 900, color: c, lineHeight: 1 }}>{score}</span>
      </div>
    </div>
  )
}

function CardImage({ iconUrl, name, rarity, size = 80 }) {
  const c   = RARITY_COLOR[rarity] || '#4a8ef5'
  const src = iconUrl
    ? (iconUrl.startsWith('http') ? iconUrl : `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`)
    : null

  return (
    <div style={{
      width: size, height: size, flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)`,
      borderRadius: 8, overflow: 'hidden',
    }}>
      {src ? (
        <img
          src={src} alt={name}
          style={{ maxWidth: '88%', maxHeight: '88%', objectFit: 'contain', filter: `drop-shadow(0 0 10px ${c}50)` }}
          onError={e => { e.currentTarget.style.display = 'none' }}
        />
      ) : (
        <span style={{ fontSize: 22, color: c, opacity: 0.5, fontFamily: 'monospace', fontWeight: 900 }}>
          {name?.[0] || '?'}
        </span>
      )}
    </div>
  )
}

function OpportunityCard({ opp }) {
  const navigate = useNavigate()
  const rc       = RARITY_COLOR[opp.rarity] || '#4a8ef5'
  const recStyle = REC_STYLES[opp.recommendation] || REC_STYLES.HOLD
  const isBuy    = opp.recommendation === 'BUY'

  return (
    <div
      onClick={() => navigate(`/item/${opp.item_id}`)}
      style={{
        flexShrink: 0, width: 252,
        background: '#0f1520',
        border: `1px solid ${isBuy ? recStyle.bg + '30' : 'rgba(255,255,255,0.07)'}`,
        borderRadius: 12,
        padding: '12px 12px 10px',
        cursor: 'pointer',
        transition: 'border-color 0.15s, transform 0.15s, box-shadow 0.15s',
        position: 'relative', overflow: 'hidden',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = recStyle.bg + '45'
        e.currentTarget.style.transform   = 'translateY(-3px)'
        e.currentTarget.style.boxShadow   = `0 12px 32px rgba(0,0,0,0.5), 0 0 0 1px ${recStyle.bg}20`
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = isBuy ? recStyle.bg + '30' : 'rgba(255,255,255,0.07)'
        e.currentTarget.style.transform   = 'translateY(0)'
        e.currentTarget.style.boxShadow   = 'none'
      }}
    >
      {/* left accent bar — colored by recommendation */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
        background: recStyle.bg, borderRadius: '12px 0 0 12px', opacity: 0.9,
      }} />

      {/* Top row: image + info */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 9, marginLeft: 6 }}>
        <CardImage iconUrl={opp.icon_url} name={opp.skin_name} rarity={opp.rarity} />
        <div style={{ flex: 1, minWidth: 0 }}>

          {/* Decision badge + confidence */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 5 }}>
            <span style={{
              fontSize: 10, fontWeight: 800, color: 'white', letterSpacing: '0.04em',
              background: recStyle.bg, borderRadius: 4, padding: '2px 7px',
              boxShadow: `0 0 8px ${recStyle.glow}`,
            }}>
              {recStyle.text}
            </span>
            {opp.confidence != null && (
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                {Math.round(opp.confidence * 100)}%
              </span>
            )}
            {opp.valuation_label && (
              <span style={{
                fontSize: 9, fontWeight: 600,
                color: VAL_COLOR[opp.valuation_label] || 'var(--text-dim)',
              }}>
                {opp.valuation_label}
              </span>
            )}
          </div>

          {/* Name */}
          <p style={{
            fontSize: 12, fontWeight: 700, color: 'white', lineHeight: 1.3, marginBottom: 2,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {opp.skin_name}
          </p>
          <p style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 7 }}>
            {opp.weapon_type}
            {opp.exterior ? ` · ${opp.exterior}` : ''}
            {opp.stattrak ? ' · ST™' : ''}
          </p>

          {/* Price + score */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <p style={{ fontSize: 9, color: 'var(--text-dim)', marginBottom: 2 }}>BUFF</p>
              <p className="price-display" style={{ fontSize: 15 }}>
                {opp.current_price != null ? formatCNY(opp.current_price) : '—'}
              </p>
            </div>
            <MiniRing score={opp.total_score} />
          </div>
        </div>
      </div>

      {/* Reason / rationale */}
      {(opp.rationale || opp.top_reason) && (
        <div style={{
          marginTop: 8, marginLeft: 6,
          paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.05)',
        }}>
          <p style={{
            fontSize: 10, color: 'var(--text-dim)', lineHeight: 1.45,
            overflow: 'hidden', display: '-webkit-box',
            WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
          }}>
            <span style={{ color: recStyle.bg, marginRight: 4 }}>◈</span>
            {opp.rationale || opp.top_reason}
          </p>
        </div>
      )}

      {/* Event context pill */}
      {opp.top_event_title && (
        <div style={{
          marginTop: 6, marginLeft: 6,
          display: 'inline-flex', alignItems: 'center', gap: 4,
          background: 'rgba(74,142,245,0.08)', border: '1px solid rgba(74,142,245,0.2)',
          borderRadius: 4, padding: '3px 7px',
        }}>
          <span style={{ fontSize: 9, color: '#4a8ef5' }}>⚡</span>
          <span style={{
            fontSize: 9, color: 'var(--text-dim)',
            overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
            maxWidth: 180,
          }}>
            {opp.top_event_title.length > 28
              ? opp.top_event_title.slice(0, 28) + '…'
              : opp.top_event_title}
            {opp.top_event_window && (
              <span style={{ color: '#4a8ef5', marginLeft: 4 }}>· {opp.top_event_window.split('(')[0].trim()}</span>
            )}
          </span>
        </div>
      )}
    </div>
  )
}

function SkeletonCard() {
  return (
    <div style={{
      flexShrink: 0, width: 252, height: 174,
      background: '#0f1520', border: '1px solid rgba(255,255,255,0.05)',
      borderRadius: 12, padding: 12, animation: 'pulse 1.6s ease infinite',
    }}>
      <div style={{ display: 'flex', gap: 9 }}>
        <div style={{ width: 80, height: 80, background: 'rgba(255,255,255,0.04)', borderRadius: 8 }} />
        <div style={{ flex: 1 }}>
          <div style={{ height: 20, width: 60, background: 'rgba(255,255,255,0.06)', borderRadius: 4, marginBottom: 8 }} />
          <div style={{ height: 13, background: 'rgba(255,255,255,0.04)', borderRadius: 4, marginBottom: 6 }} />
          <div style={{ height: 11, width: '70%', background: 'rgba(255,255,255,0.03)', borderRadius: 4, marginBottom: 10 }} />
          <div style={{ height: 16, width: '50%', background: 'rgba(255,255,255,0.04)', borderRadius: 4 }} />
        </div>
      </div>
    </div>
  )
}

export default function OpportunityPanel({ opportunities, loading }) {
  const items = opportunities || []

  return (
    <div style={{
      display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 8,
      scrollbarWidth: 'none', msOverflowStyle: 'none',
    }}>
      {loading
        ? [...Array(4)].map((_, i) => <SkeletonCard key={i} />)
        : items.length > 0
          ? items.map(opp => <OpportunityCard key={opp.item_id} opp={opp} />)
          : (
            <div style={{
              padding: '24px 32px',
              background: '#0f1520', border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 12, color: 'var(--text-dim)', fontSize: 13,
            }}>
              暂未发现明显机会，市场整体处于均衡区间
            </div>
          )
      }
    </div>
  )
}
