import { formatCNY, formatPercent } from '../utils/formatters'
import { PLATFORM_COLORS } from '../utils/constants'
import RiskBadge from './RiskBadge'

function StatRow({ label, value, valueClass = '' }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-slate-700/40 last:border-0">
      <span className="text-slate-400 text-xs">{label}</span>
      <span className={`text-sm font-medium ${valueClass || 'text-slate-200'}`}>{value}</span>
    </div>
  )
}

export default function PriceSummaryCard({ platform, current_price, avg_7d, avg_30d, return_7d, volatility_7d, spread, liquidity_score, risk_labels }) {
  const platformColor = PLATFORM_COLORS[platform] || '#06b6d4'
  const returnPositive = return_7d != null && return_7d >= 0

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: platformColor }} />
          <span className="font-semibold text-white text-sm">{platform}</span>
        </div>
        {risk_labels && risk_labels.length > 0 && (
          <RiskBadge labels={risk_labels} />
        )}
      </div>

      <div>
        <p className="text-slate-400 text-xs mb-0.5">当前价格</p>
        <p className="text-3xl font-bold text-white">{formatCNY(current_price)}</p>
      </div>

      <div className="space-y-0.5">
        <StatRow label="7日均价" value={formatCNY(avg_7d)} />
        <StatRow label="30日均价" value={formatCNY(avg_30d)} />
        <StatRow
          label="7日涨跌"
          value={formatPercent(return_7d)}
          valueClass={returnPositive ? 'text-green-400' : 'text-red-400'}
        />
        <StatRow
          label="波动率"
          value={volatility_7d != null ? (volatility_7d * 100).toFixed(2) + '%' : '—'}
          valueClass={
            volatility_7d == null ? '' :
            volatility_7d > 0.08 ? 'text-red-400' :
            volatility_7d < 0.04 ? 'text-green-400' : 'text-yellow-400'
          }
        />
        <StatRow label="买卖价差" value={formatCNY(spread)} />
        <StatRow
          label="流动性评分"
          value={liquidity_score != null ? `${liquidity_score}/100` : '—'}
          valueClass={
            liquidity_score == null ? '' :
            liquidity_score > 60 ? 'text-green-400' :
            liquidity_score < 40 ? 'text-red-400' : 'text-yellow-400'
          }
        />
      </div>
    </div>
  )
}
