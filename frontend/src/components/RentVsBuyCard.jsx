import { formatCNY } from '../utils/formatters'

function Plan({ label, amount, sub, recommended, platform, pros, cons, children }) {
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
      {children}
      <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] space-y-1">
        <p className="text-[var(--text-dim)] text-xs">优点：{pros}</p>
        <p className="text-[var(--text-dim)] text-xs">缺点：{cons}</p>
      </div>
    </div>
  )
}

export default function RentVsBuyCard({ rent_cost, buy_price, buy_affordable, rent_available, rent_affordable, deposit_required, buy_resale_loss, recommendation, explanation, days, rental_platform, buy_platform }) {
  return (
    <div className="surface-card overflow-hidden p-0">
      {explanation && (
        <div className="px-5 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-surface-raised)]">
          <h3 className="text-[var(--text-primary)] text-sm font-semibold mb-2">比较结论</h3>
          <p className="text-[var(--text-secondary)] text-sm leading-relaxed">{explanation}</p>
        </div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-subtle)]">
        <Plan
          label="租赁方案" amount={rent_cost} sub={`${days} 天租赁总费用`}
          recommended={recommendation === 'rent'} platform={rental_platform}
          pros="按使用期付租金" cons="可能需要押金，持续付费"
        >
          <p className="text-xs leading-5 mt-3 text-[var(--text-secondary)]">{!rent_available ? '暂无可用租赁报价' : deposit_required ? '需另行确认押金，预算是否足够尚不确定' : rent_affordable === false ? '租金已超出当前预算' : '请核对实际租金及押金要求'}</p>
        </Plan>
        <Plan
          label="购买方案" amount={buy_resale_loss} sub={`${days} 天持有后转卖预估损耗`}
          recommended={recommendation === 'buy'} platform={buy_platform}
          pros="拥有饰品，可自行决定出售时间" cons="占用本金，转卖价格不确定"
        >
          <p className="text-sm mt-3">购买本金 <strong className="font-tabular">{formatCNY(buy_price)}</strong></p>
          {buy_price != null && <p className="text-xs mt-1" style={{ color: buy_affordable ? 'var(--buy)' : 'var(--avoid)' }}>{buy_affordable ? '当前预算可覆盖购买本金' : '购买本金超出当前预算'}</p>}
        </Plan>
      </div>

    </div>
  )
}
