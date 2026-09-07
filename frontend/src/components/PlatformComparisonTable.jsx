import { formatCNY } from '../utils/formatters'
import { PLATFORM_COLORS } from '../utils/constants'
import EmptyState from './ui/EmptyState'
import { Table } from '@phosphor-icons/react'

const HEADERS = ['平台', '当前价格', '7日均价', '买卖价差', '流动性', '溢价']

export default function PlatformComparisonTable({ platforms = [] }) {
  if (!platforms.length) {
    return <EmptyState icon={Table} sub="暂无平台对比数据" />
  }

  return (
    <div className="overflow-x-auto -mx-1 px-1">
      <table className="w-full text-[13px] border-collapse min-w-[420px]">
        <thead>
          <tr className="border-b border-[var(--border-subtle)]">
            {HEADERS.map(h => (
              <th
                key={h}
                className={`px-3 py-2 font-medium text-[11px] uppercase tracking-wide whitespace-nowrap text-[var(--text-dim)] ${h === '平台' ? 'text-left' : 'text-right'}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {platforms.map((p, i) => (
            <tr
              key={p.platform}
              className={i < platforms.length - 1 ? 'border-b border-white/[0.04]' : ''}
              style={{ background: p.is_best_price ? 'var(--accent-soft)' : 'transparent' }}
            >
              <td className="px-3 py-2.5">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <div className="w-[7px] h-[7px] rounded-full shrink-0" style={{ background: PLATFORM_COLORS[p.platform] || 'var(--accent)' }} />
                  <span className="font-medium text-[var(--text-primary)]">{p.platform}</span>
                  {p.is_best_price && (
                    <span className="text-[10px] rounded px-1 py-px" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)', border: '1px solid var(--accent-border)' }}>最优</span>
                  )}
                  {p.supports_rental && (
                    <span className="text-[10px] rounded px-1 py-px border border-[var(--border-default)] text-[var(--text-secondary)]">租赁</span>
                  )}
                </div>
              </td>
              <td className="px-3 py-2.5 text-right price-display">{formatCNY(p.current_price)}</td>
              <td className="px-3 py-2.5 text-right text-[var(--text-secondary)] font-tabular">{formatCNY(p.avg_7d)}</td>
              <td className="px-3 py-2.5 text-right text-[var(--text-secondary)] font-tabular">{formatCNY(p.spread)}</td>
              <td className="px-3 py-2.5 text-right font-tabular font-semibold" style={{
                color: p.liquidity_score == null ? 'var(--text-dim)' : p.liquidity_score > 60 ? 'var(--buy)' : p.liquidity_score < 40 ? 'var(--avoid)' : 'var(--gold)',
              }}>
                {p.liquidity_score != null ? p.liquidity_score.toFixed(0) : '—'}
              </td>
              <td className="px-3 py-2.5 text-right font-tabular" style={{ color: p.price_vs_best_pct > 0 ? 'var(--gold)' : 'var(--text-dim)', fontWeight: p.price_vs_best_pct > 0 ? 600 : 400 }}>
                {p.price_vs_best_pct != null ? (p.price_vs_best_pct === 0 ? '基准' : `+${p.price_vs_best_pct.toFixed(1)}%`) : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
