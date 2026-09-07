import { formatCNY } from '../utils/formatters'

function Plan({ label, amount, sub, recommended, platform, pros, cons }) {
  return (
    <div className={`p-5 ${recommended ? 'bg-[var(--accent-soft)]' : ''}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[var(--text-secondary)] font-semibold text-sm">{label}</span>
        {recommended && (
          <span className="text-xs rounded-[var(--radius-sm)] px-2 py-0.5" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)', border: '1px solid var(--accent-border)' }}>推荐</span>
        )}
      </div>
      <p className="price-display text-3xl">{amount != null ? formatCNY(amount) : '不可用'}</p>
      <p className="text-[var(--text-dim)] text-xs mt-1">{sub}</p>
      {platform && <p className="text-[var(--text-secondary)] text-xs mt-2">平台：{platform}</p>}
      <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] space-y-1">
        <p className="text-[var(--text-dim)] text-xs">优点：{pros}</p>
        <p className="text-[var(--text-dim)] text-xs">缺点：{cons}</p>
      </div>
    </div>
  )
}

export default function RentVsBuyCard({ rent_cost, buy_resale_loss, recommendation, explanation, days, rental_platform, buy_platform }) {
  return (
    <div className="surface-card overflow-hidden p-0">
      <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-subtle)]">
        <Plan
          label="租赁方案" amount={rent_cost} sub={`${days} 天租赁总费用`}
          recommended={recommendation === 'rent'} platform={rental_platform}
          pros="无需大额资金，用完即还" cons="无法保值，持续付费"
        />
        <Plan
          label="购买方案" amount={buy_resale_loss} sub={`${days} 天持有后转卖预估损耗`}
          recommended={recommendation === 'buy'} platform={buy_platform}
          pros="可保值，价格上涨可盈利" cons="需要较多前期资金"
        />
      </div>

      {explanation && (
        <div className="px-5 py-4 border-t border-[var(--border-subtle)]" style={{ background: 'rgba(0,0,0,0.2)' }}>
          <p className="text-[var(--text-dim)] text-xs font-medium uppercase tracking-wide mb-2">分析结论</p>
          <p className="text-[var(--text-primary)] text-sm leading-relaxed">{explanation}</p>
        </div>
      )}
    </div>
  )
}
