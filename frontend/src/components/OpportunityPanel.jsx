/**
 * OpportunityPanel — event-aware opportunity cards, decision-first.
 * Each card leads with the BUY/WATCH/HOLD/AVOID call, then score, price,
 * rationale, and the driving market event (if any).
 */

import { useNavigate } from 'react-router-dom'
import { Lightning } from '@phosphor-icons/react'
import { formatCNY } from '../utils/formatters'
import { RARITY_COLOR } from '../utils/constants'
import { ScoreRing } from './ui/Score'
import DecisionBadge, { DECISION_META } from './ui/Decision'
import Skeleton from './ui/Skeleton'

const VAL_COLOR = { '低估': 'var(--buy)', '合理': 'var(--accent-strong)', '高估': 'var(--avoid)' }

function CardImage({ iconUrl, name, rarity, size = 76 }) {
  const c = RARITY_COLOR[rarity] || 'var(--accent)'
  const src = iconUrl
    ? (iconUrl.startsWith('http') ? iconUrl : `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`)
    : null

  return (
    <div
      className="shrink-0 flex items-center justify-center rounded-[var(--radius-sm)] overflow-hidden"
      style={{ width: size, height: size, background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)` }}
    >
      {src ? (
        <img
          src={src} alt={name}
          className="max-w-[88%] max-h-[88%] object-contain"
          style={{ filter: `drop-shadow(0 0 10px ${c}50)` }}
          onError={e => { e.currentTarget.style.display = 'none' }}
        />
      ) : (
        <span className="font-mono font-black text-xl opacity-50" style={{ color: c }}>{name?.[0] || '?'}</span>
      )}
    </div>
  )
}

function OpportunityCard({ opp }) {
  const navigate = useNavigate()
  const meta = DECISION_META[opp.recommendation] || DECISION_META.HOLD
  const isBuy = opp.recommendation === 'BUY'

  return (
    <div
      onClick={() => navigate(`/item/${opp.item_id}`)}
      className="snap-start shrink-0 w-[256px] relative overflow-hidden rounded-[var(--radius-md)] p-3 cursor-pointer
        transition-all duration-150 hover:-translate-y-[3px]"
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${isBuy ? meta.color + '30' : 'var(--border-subtle)'}`,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = meta.color + '55'; e.currentTarget.style.boxShadow = 'var(--shadow-md)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = isBuy ? meta.color + '30' : 'var(--border-subtle)'; e.currentTarget.style.boxShadow = 'none' }}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-[var(--radius-md)] opacity-90" style={{ background: meta.color }} />

      {/* Decision badge leads — the whole point of the card */}
      <div className="flex items-center gap-1.5 mb-2.5 ml-1.5">
        <DecisionBadge recommendation={opp.recommendation} size="sm" />
        {opp.confidence != null && (
          <span className="text-[10px] text-[var(--text-dim)] font-tabular">{Math.round(opp.confidence * 100)}% 置信</span>
        )}
        {opp.valuation_label && (
          <span className="text-[9px] font-semibold ml-auto" style={{ color: VAL_COLOR[opp.valuation_label] || 'var(--text-dim)' }}>
            {opp.valuation_label}
          </span>
        )}
      </div>

      <div className="flex items-start gap-2.5 ml-1.5">
        <CardImage iconUrl={opp.icon_url} name={opp.skin_name} rarity={opp.rarity} />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-[var(--text-primary)] leading-snug mb-0.5 truncate">{opp.skin_name}</p>
          <p className="text-[10px] text-[var(--text-dim)] mb-2 truncate">
            {opp.weapon_type}{opp.exterior ? ` · ${opp.exterior}` : ''}{opp.stattrak ? ' · ST™' : ''}
          </p>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[9px] text-[var(--text-dim)] mb-0.5">BUFF</p>
              <p className="price-display text-[15px]">
                {opp.current_price != null ? formatCNY(opp.current_price) : '—'}
              </p>
            </div>
            <ScoreRing score={opp.total_score} size={40} variant="badge" showLabel={false} />
          </div>
        </div>
      </div>

      {(opp.rationale || opp.top_reason) && (
        <div className="mt-2 ml-1.5 pt-2 border-t border-[var(--border-subtle)]">
          <p className="text-[10px] text-[var(--text-dim)] leading-snug line-clamp-2">
            <span className="mr-1" style={{ color: meta.color }}>◈</span>
            {opp.rationale || opp.top_reason}
          </p>
        </div>
      )}

      {opp.top_event_title && (
        <div className="mt-1.5 ml-1.5 inline-flex items-center gap-1 rounded px-1.5 py-0.5 border" style={{ background: 'var(--gold-soft)', borderColor: 'var(--gold-border)' }}>
          <Lightning size={10} weight="fill" style={{ color: 'var(--gold)' }} />
          <span className="text-[9px] text-[var(--text-dim)] truncate max-w-[170px]">
            {opp.top_event_title.length > 26 ? opp.top_event_title.slice(0, 26) + '…' : opp.top_event_title}
            {opp.top_event_window && (
              <span style={{ color: 'var(--gold)' }} className="ml-1">· {opp.top_event_window.split('(')[0].trim()}</span>
            )}
          </span>
        </div>
      )}
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="snap-start shrink-0 w-[256px] h-[176px] surface-card p-3">
      <div className="flex gap-2.5">
        <Skeleton w={76} h={76} radius={10} />
        <div className="flex-1">
          <Skeleton h={20} w="60%" className="mb-2" />
          <Skeleton h={13} className="mb-1.5" />
          <Skeleton h={11} w="70%" className="mb-2.5" />
          <Skeleton h={16} w="50%" />
        </div>
      </div>
    </div>
  )
}

export default function OpportunityPanel({ opportunities, loading }) {
  const items = opportunities || []

  return (
    <div
      className="flex gap-2.5 overflow-x-auto no-scrollbar snap-x snap-mandatory pb-2 -mx-4 px-4 sm:mx-0 sm:px-0"
      style={{ maskImage: 'linear-gradient(90deg, black 92%, transparent)' }}
    >
      {loading
        ? [...Array(4)].map((_, i) => <SkeletonCard key={i} />)
        : items.length > 0
          ? items.map(opp => <OpportunityCard key={opp.item_id} opp={opp} />)
          : (
            <div className="surface-card px-8 py-6 text-[var(--text-dim)] text-sm">
              暂未发现明显机会，市场整体处于均衡区间
            </div>
          )
      }
    </div>
  )
}
