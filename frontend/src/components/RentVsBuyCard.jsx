import { formatCNY } from '../utils/formatters'

export default function RentVsBuyCard({ rent_cost, buy_resale_loss, recommendation, explanation, days, rental_platform, buy_platform }) {
  const isRent = recommendation === 'rent'
  const isBuy = recommendation === 'buy'

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <div className="grid grid-cols-2 divide-x divide-slate-700">
        <div className={`p-5 ${isRent ? 'bg-cyan-900/20' : ''}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-300 font-semibold text-sm">租赁方案</span>
            {isRent && (
              <span className="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-0.5 rounded-full border border-cyan-500/30">
                推荐
              </span>
            )}
          </div>
          <p className="text-3xl font-bold text-white">{rent_cost != null ? formatCNY(rent_cost) : '不可用'}</p>
          <p className="text-slate-500 text-xs mt-1">{days} 天租赁总费用</p>
          {rental_platform && (
            <p className="text-slate-400 text-xs mt-2">平台：{rental_platform}</p>
          )}
          <div className="mt-3 pt-3 border-t border-slate-700/50">
            <p className="text-slate-500 text-xs">优点：无需大额资金，用完即还</p>
            <p className="text-slate-500 text-xs mt-1">缺点：无法保值，持续付费</p>
          </div>
        </div>

        <div className={`p-5 ${isBuy ? 'bg-cyan-900/20' : ''}`}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-300 font-semibold text-sm">购买方案</span>
            {isBuy && (
              <span className="bg-cyan-500/20 text-cyan-300 text-xs px-2 py-0.5 rounded-full border border-cyan-500/30">
                推荐
              </span>
            )}
          </div>
          <p className="text-3xl font-bold text-white">{buy_resale_loss != null ? formatCNY(buy_resale_loss) : '—'}</p>
          <p className="text-slate-500 text-xs mt-1">{days} 天持有后转卖预估损耗</p>
          {buy_platform && (
            <p className="text-slate-400 text-xs mt-2">平台：{buy_platform}</p>
          )}
          <div className="mt-3 pt-3 border-t border-slate-700/50">
            <p className="text-slate-500 text-xs">优点：可保值，价格上涨可盈利</p>
            <p className="text-slate-500 text-xs mt-1">缺点：需要较多前期资金</p>
          </div>
        </div>
      </div>

      {explanation && (
        <div className="px-5 py-4 border-t border-slate-700 bg-slate-900/30">
          <p className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">分析结论</p>
          <p className="text-slate-200 text-sm leading-relaxed">{explanation}</p>
        </div>
      )}
    </div>
  )
}
