import { TrendUp, TrendDown, Eye, ShieldWarning } from '@phosphor-icons/react'

export const DECISION_META = {
  BUY: { label: '买入', color: 'var(--buy)', soft: 'var(--buy-soft)', Icon: TrendUp },
  WATCH: { label: '观望', color: 'var(--watch)', soft: 'var(--watch-soft)', Icon: Eye },
  HOLD: { label: '持有', color: 'var(--hold)', soft: 'var(--hold-soft)', Icon: TrendDown },
  AVOID: { label: '规避', color: 'var(--avoid)', soft: 'var(--avoid-soft)', Icon: ShieldWarning },
}

/** The BUY/WATCH/HOLD/AVOID badge — one implementation, used everywhere. */
export default function DecisionBadge({ recommendation, size = 'md', className = '' }) {
  const meta = DECISION_META[recommendation] || DECISION_META.HOLD
  const { Icon } = meta
  const sizeCls = size === 'lg'
    ? 'text-sm px-3.5 py-1.5 gap-2'
    : size === 'sm'
      ? 'text-[10px] px-2 py-0.5 gap-1'
      : 'text-xs px-2.5 py-1 gap-1.5'
  return (
    <span
      className={`inline-flex items-center font-bold rounded-[var(--radius-sm)] text-white ${sizeCls} ${className}`}
      style={{ background: meta.color }}
    >
      <Icon weight="bold" size={size === 'lg' ? 16 : 12} />
      {meta.label}
    </span>
  )
}
