/**
 * DecisionPanel — the product's differentiator, rendered as professional
 * market research: rationale, upside/risk factors, the full evidence log,
 * event context and the 7-dimension score breakdown are all visible by
 * default. Nothing that explains "why" sits behind a click.
 */

import { CaretUp, CaretDown, Diamond } from '@phosphor-icons/react'
import Skeleton from './ui/Skeleton'
import { ScoreBar } from './ui/Score'
import DecisionBadge, { DECISION_META } from './ui/Decision'

const SIGNAL_COLOR = { '+': 'var(--buy)', '-': 'var(--avoid)', '=': 'var(--text-dim)' }

const SUBSCORE_LABELS = {
  rarity: '稀有度', exterior: '外观品相', liquidity: '流动性',
  trend: '7日趋势', valuation: '估值空间', demand: '市场需求', event: '事件信号',
}

export default function DecisionPanel({ decision, loading }) {
  if (loading) {
    return (
      <div className="surface-card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <Skeleton w={90} h={28} radius={6} />
          <Skeleton w={50} h={28} radius={6} />
        </div>
        <Skeleton h={8} radius={4} />
        <Skeleton h={40} radius={6} />
        <Skeleton h={14} w="70%" />
      </div>
    )
  }

  if (!decision) return null

  const meta = DECISION_META[decision.recommendation] || DECISION_META.HOLD
  const conf = Math.round(decision.confidence * 100)
  const ss = decision.score_summary || {}

  return (
    <div className="rounded-[var(--radius-md)] border p-5 space-y-4" style={{ borderColor: meta.color + '40', background: meta.soft }}>

      {/* Header — the decision, unmissable */}
      <div className="flex items-center justify-between">
        <DecisionBadge recommendation={decision.recommendation} size="lg" />
        <div className="text-right">
          <div className="text-2xl font-extrabold font-tabular text-[var(--text-primary)] leading-none">{ss.total ?? '—'}</div>
          <div className="text-[10px] text-[var(--text-dim)] mt-1">综合评分</div>
        </div>
      </div>

      {/* Confidence */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-[var(--text-secondary)]">
          <span>决策置信度</span>
          <span className="font-tabular font-semibold" style={{ color: meta.color }}>{conf}%</span>
        </div>
        <div className="h-2 rounded-full bg-white/[0.07] overflow-hidden">
          <div className="h-full rounded-full transition-[width] duration-700" style={{ width: `${conf}%`, background: meta.color }} />
        </div>
      </div>

      {/* Rationale — the headline "why" */}
      <p className="text-sm text-[var(--text-primary)] leading-relaxed border-l-2 pl-3" style={{ borderColor: meta.color + '60' }}>
        {decision.rationale}
      </p>

      <div className="flex gap-5 text-xs">
        <span className="text-[var(--text-dim)]">估值：
          <span style={{ color: ss.valuation_label === '低估' ? 'var(--buy)' : ss.valuation_label === '高估' ? 'var(--avoid)' : 'var(--text-secondary)' }}>
            {' '}{ss.valuation_label}
          </span>
        </span>
        <span className="text-[var(--text-dim)]">信号净值：
          <span style={{ color: ss.net_signal >= 0 ? 'var(--buy)' : 'var(--avoid)' }} className="font-tabular">
            {' '}{ss.net_signal >= 0 ? '+' : ''}{ss.net_signal}
          </span>
        </span>
      </div>

      {/* Upside / Risk */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--buy)' }}>做多因素</div>
          {decision.upside_factors?.length ? decision.upside_factors.slice(0, 3).map((u, i) => (
            <div key={i} className="flex items-start gap-1.5 mb-1">
              <CaretUp size={11} weight="bold" className="mt-0.5 shrink-0" style={{ color: 'var(--buy)' }} />
              <span className="text-xs text-[var(--text-secondary)] leading-snug">{u}</span>
            </div>
          )) : <span className="text-xs text-[var(--text-dim)]">暂无</span>}
        </div>
        <div>
          <div className="text-xs font-semibold mb-1.5" style={{ color: 'var(--avoid)' }}>风险因素</div>
          {decision.risk_factors?.length ? decision.risk_factors.slice(0, 3).map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 mb-1">
              <CaretDown size={11} weight="bold" className="mt-0.5 shrink-0" style={{ color: 'var(--avoid)' }} />
              <span className="text-xs text-[var(--text-secondary)] leading-snug">{r}</span>
            </div>
          )) : <span className="text-xs text-[var(--text-dim)]">暂无</span>}
        </div>
      </div>

      {/* 7-dimension subscores — always visible */}
      {ss.total != null && (
        <div className="space-y-2 pt-1 border-t border-[var(--border-subtle)]">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-1">7维度评分</div>
          {Object.entries(SUBSCORE_LABELS).map(([key, label]) =>
            ss[key] !== undefined ? <ScoreBar key={key} label={label} value={ss[key]} /> : null
          )}
        </div>
      )}

      {/* Evidence log — visible by default, this IS the product */}
      {decision.supporting_signals?.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">
            决策证据链 ({decision.supporting_signals.length} 条信号)
          </div>
          <div className="space-y-1.5">
            {decision.supporting_signals.map((sig, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-xs font-bold shrink-0" style={{ color: SIGNAL_COLOR[sig.direction] }}>
                  {sig.direction === '+' ? <CaretUp size={11} weight="bold" /> : sig.direction === '-' ? <CaretDown size={11} weight="bold" /> : <Diamond size={9} weight="fill" />}
                </span>
                <div>
                  <span className="text-xs font-medium text-[var(--text-primary)]">{sig.label}</span>
                  {sig.points > 0 && (
                    <span className="ml-1.5 text-xs font-tabular" style={{ color: SIGNAL_COLOR[sig.direction] }}>
                      {sig.direction === '+' ? '+' : '-'}{sig.points}pt
                    </span>
                  )}
                  <p className="text-xs text-[var(--text-dim)] leading-snug mt-0.5">{sig.note}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event context — visible by default */}
      {decision.event_context?.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-3">
          <div className="text-xs font-semibold text-[var(--text-secondary)] mb-2">
            市场事件 ({decision.event_context.length} 个)
          </div>
          <div className="space-y-2">
            {decision.event_context.map((e, i) => (
              <div key={i} className="rounded-[var(--radius-sm)] p-2.5 space-y-0.5" style={{ background: 'rgba(0,0,0,0.2)' }}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-[var(--text-primary)] truncate">{e.title}</span>
                  <span
                    className="text-xs font-bold font-tabular shrink-0"
                    style={{ color: e.impact === 'positive' ? 'var(--buy)' : e.impact === 'negative' ? 'var(--avoid)' : 'var(--text-dim)' }}
                  >
                    {e.impact === 'positive' ? '▲' : e.impact === 'negative' ? '▼' : '◆'} {Math.round(e.strength * 100)}%
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-[var(--text-dim)]">
                  <span>{e.window_label}</span><span>·</span><span>{e.event_type}</span><span>·</span><span>相关性 {Math.round(e.relevance * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {decision.evidence_sources?.length > 0 && (
        <div className="border-t border-[var(--border-subtle)] pt-2">
          <div className="text-xs text-[var(--text-dim)]">数据来源：{decision.evidence_sources.join(' · ')}</div>
        </div>
      )}
    </div>
  )
}
