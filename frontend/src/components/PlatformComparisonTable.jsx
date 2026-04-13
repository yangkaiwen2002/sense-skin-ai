import { useNavigate } from 'react-router-dom'
import { formatCNY } from '../utils/formatters'
import { PLATFORM_COLORS } from '../utils/constants'

export default function PlatformComparisonTable({ platforms = [], itemId }) {
  const navigate = useNavigate()

  if (!platforms.length) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 text-center text-slate-500 text-sm">
        暂无平台数据
      </div>
    )
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-700 bg-slate-900/50">
            <th className="text-left px-4 py-3 text-slate-400 font-medium">平台</th>
            <th className="text-right px-4 py-3 text-slate-400 font-medium">当前价格</th>
            <th className="text-right px-4 py-3 text-slate-400 font-medium">7日均价</th>
            <th className="text-right px-4 py-3 text-slate-400 font-medium">买卖价差</th>
            <th className="text-right px-4 py-3 text-slate-400 font-medium">流动性</th>
            <th className="text-right px-4 py-3 text-slate-400 font-medium">溢价</th>
            <th className="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          {platforms.map((p) => (
            <tr
              key={p.platform}
              className={`border-b border-slate-700/50 last:border-0 transition-colors ${
                p.is_best_price ? 'bg-cyan-900/10' : 'hover:bg-slate-750/30'
              }`}
            >
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: PLATFORM_COLORS[p.platform] || '#06b6d4' }} />
                  <span className="font-medium text-slate-200">{p.platform}</span>
                  {p.is_best_price && (
                    <span className="bg-cyan-500/20 text-cyan-300 text-xs px-1.5 py-0.5 rounded border border-cyan-500/30">
                      最优价
                    </span>
                  )}
                  {p.supports_rental && (
                    <span className="bg-purple-500/20 text-purple-300 text-xs px-1.5 py-0.5 rounded border border-purple-500/30">
                      支持租赁
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-right font-semibold text-white">
                {formatCNY(p.current_price)}
              </td>
              <td className="px-4 py-3 text-right text-slate-300">{formatCNY(p.avg_7d)}</td>
              <td className="px-4 py-3 text-right text-slate-300">{formatCNY(p.spread)}</td>
              <td className="px-4 py-3 text-right">
                <span className={
                  p.liquidity_score == null ? 'text-slate-500' :
                  p.liquidity_score > 60 ? 'text-green-400' :
                  p.liquidity_score < 40 ? 'text-red-400' : 'text-yellow-400'
                }>
                  {p.liquidity_score != null ? `${p.liquidity_score}` : '—'}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <span className={p.price_vs_best_pct > 0 ? 'text-orange-400' : 'text-slate-400'}>
                  {p.price_vs_best_pct != null ? (p.price_vs_best_pct === 0 ? '基准' : `+${p.price_vs_best_pct.toFixed(1)}%`) : '—'}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                {itemId && (
                  <button
                    onClick={() => navigate(`/item/${itemId}`)}
                    className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
                  >
                    详情
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
