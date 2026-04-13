import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { searchItems, rentVsBuy } from '../services/api'
import RentVsBuyCard from '../components/RentVsBuyCard'

export default function RentVsBuy() {
  const navigate = useNavigate()

  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [selectedItem, setSelectedItem] = useState(null)
  const [days, setDays] = useState(7)
  const [budget, setBudget] = useState(1000)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!searchQuery.trim()) { setSuggestions([]); return }
    const t = setTimeout(async () => {
      const res = await searchItems(searchQuery)
      setSuggestions(res?.items || [])
    }, 300)
    return () => clearTimeout(t)
  }, [searchQuery])

  function selectItem(item) {
    setSelectedItem(item)
    setSearchQuery(item.skin_name || item.item_name)
    setSuggestions([])
    setResult(null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selectedItem) return
    setLoading(true)
    setError(null)
    setResult(null)
    const res = await rentVsBuy(selectedItem.id, { days, budget })
    setLoading(false)
    if (res) {
      setResult(res)
    } else {
      setError('计算失败，请稍后重试')
    }
  }

  const QUICK_DAYS = [3, 7, 14, 30]

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <button onClick={() => navigate('/')} className="hover:text-slate-300 transition-colors">首页</button>
        <span>/</span>
        <span className="text-slate-300">租赁 vs 购买</span>
      </div>

      <h1 className="text-2xl font-bold text-white mb-2">租赁 vs 购买分析</h1>
      <p className="text-slate-400 text-sm mb-8">输入使用天数，系统自动计算租赁费用与购买后转卖的成本差异</p>

      <form onSubmit={handleSubmit} className="space-y-6 mb-8">
        {/* Item search */}
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-2">饰品</label>
          <div className="relative">
            <input
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); if (!e.target.value) setSelectedItem(null) }}
              placeholder="搜索饰品..."
              className="w-full bg-slate-800 border border-slate-600 text-white placeholder-slate-500 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500"
            />
            {suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-xl overflow-hidden z-10 shadow-xl">
                {suggestions.map(s => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => selectItem(s)}
                    className="w-full text-left px-4 py-3 hover:bg-slate-700 border-b border-slate-700/50 last:border-0"
                  >
                    <p className="text-white text-sm">{s.skin_name || s.item_name}</p>
                    <p className="text-slate-400 text-xs">{s.weapon_type}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
          {selectedItem && (
            <p className="text-cyan-400 text-xs mt-1.5">
              已选择：{selectedItem.skin_name || selectedItem.item_name}
            </p>
          )}
        </div>

        {/* Days */}
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-2">使用天数</label>
          <div className="flex gap-2 mb-3">
            {QUICK_DAYS.map(d => (
              <button
                key={d}
                type="button"
                onClick={() => setDays(d)}
                className={`px-4 py-2 rounded-lg text-sm transition-colors ${
                  days === d ? 'bg-cyan-600 text-white' : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
                }`}
              >
                {d} 天
              </button>
            ))}
          </div>
          <input
            type="number"
            value={days}
            onChange={e => setDays(Math.max(1, Math.min(365, Number(e.target.value))))}
            min={1}
            max={365}
            className="w-32 bg-slate-800 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
          />
          <span className="text-slate-400 text-sm ml-2">天</span>
        </div>

        {/* Budget */}
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-2">预算上限（元）</label>
          <input
            type="number"
            value={budget}
            onChange={e => setBudget(Math.max(0, Number(e.target.value)))}
            min={0}
            step={100}
            className="w-40 bg-slate-800 border border-slate-600 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
          />
        </div>

        <button
          type="submit"
          disabled={!selectedItem || loading}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium px-8 py-3 rounded-xl transition-colors"
        >
          {loading ? '计算中...' : '开始分析'}
        </button>
      </form>

      {error && (
        <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-4 mb-6">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1 h-5 bg-cyan-500 rounded-full" />
            <h2 className="text-white font-semibold">{result.item_name} · {result.days} 天分析结果</h2>
          </div>
          <RentVsBuyCard
            rent_cost={result.rent_cost}
            buy_resale_loss={result.buy_resale_loss}
            recommendation={result.recommendation}
            explanation={result.explanation}
            days={result.days}
            rental_platform={result.rental_platform}
            buy_platform={result.buy_platform}
          />
          <div className="flex gap-3 mt-4">
            <button
              onClick={() => navigate(`/item/${selectedItem.id}`)}
              className="text-sm text-cyan-400 hover:text-cyan-300 border border-cyan-500/30 rounded-lg px-4 py-2 transition-colors"
            >
              查看价格详情
            </button>
            <button
              onClick={() => navigate(`/compare/${selectedItem.id}`)}
              className="text-sm text-slate-400 hover:text-slate-300 border border-slate-600 rounded-lg px-4 py-2 transition-colors"
            >
              平台对比
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
