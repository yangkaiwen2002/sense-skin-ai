import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { CaretRight } from '@phosphor-icons/react'
import { searchItems, rentVsBuy } from '../services/api'
import RentVsBuyCard from '../components/RentVsBuyCard'
import Button from '../components/ui/Button'

const QUICK_DAYS = [3, 7, 14, 30]

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
      setSuggestions(res?.items || res || [])
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
    if (res) setResult(res)
    else setError('计算失败，请稍后重试')
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-1.5 text-xs text-[var(--text-dim)] mb-5">
        <button onClick={() => navigate('/')} className="hover:text-[var(--text-secondary)] transition-colors">首页</button>
        <CaretRight size={11} />
        <span className="text-[var(--text-secondary)]">租赁 vs 购买</span>
      </div>

      <h1 className="text-xl font-bold text-[var(--text-primary)] mb-2">租赁 vs 购买分析</h1>
      <p className="text-[var(--text-dim)] text-sm mb-7 leading-relaxed">输入使用天数，系统自动计算租赁费用与购买后转卖的成本差异</p>

      <form onSubmit={handleSubmit} className="space-y-6 mb-8">
        <div>
          <label className="block text-[var(--text-secondary)] text-sm font-medium mb-2">饰品</label>
          <div className="relative">
            <input
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); if (!e.target.value) setSelectedItem(null) }}
              placeholder="搜索饰品..."
              className="w-full min-h-[44px] bg-white/[0.05] border border-[var(--border-default)] text-[var(--text-primary)]
                placeholder:text-[var(--text-dim)] rounded-[var(--radius-md)] px-4 py-3 text-sm outline-none
                focus:border-[var(--accent-border)] transition-colors duration-150"
            />
            {suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 rounded-[var(--radius-md)] border border-[var(--border-default)] overflow-hidden z-10"
                style={{ background: 'var(--bg-surface-raised)', boxShadow: 'var(--shadow-lg)' }}>
                {suggestions.map(s => (
                  <button
                    key={s.id} type="button" onClick={() => selectItem(s)}
                    className="w-full text-left min-h-[52px] px-4 py-2.5 hover:bg-white/[0.05] border-b border-white/[0.04] last:border-0 transition-colors"
                  >
                    <p className="text-[var(--text-primary)] text-sm font-medium">{s.skin_name || s.item_name}</p>
                    <p className="text-[var(--text-dim)] text-xs mt-0.5">{s.weapon_type}</p>
                  </button>
                ))}
              </div>
            )}
          </div>
          {selectedItem && (
            <p className="text-xs mt-1.5" style={{ color: 'var(--accent-strong)' }}>已选择：{selectedItem.skin_name || selectedItem.item_name}</p>
          )}
        </div>

        <div>
          <label className="block text-[var(--text-secondary)] text-sm font-medium mb-2">使用天数</label>
          <div className="flex gap-2 mb-3 flex-wrap">
            {QUICK_DAYS.map(d => (
              <button
                key={d} type="button" onClick={() => setDays(d)}
                className="min-h-[40px] px-4 rounded-[var(--radius-sm)] text-sm transition-colors duration-150"
                style={{
                  background: days === d ? 'var(--accent)' : 'rgba(255,255,255,0.06)',
                  color: days === d ? 'white' : 'var(--text-secondary)',
                }}
              >
                {d} 天
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number" value={days}
              onChange={e => setDays(Math.max(1, Math.min(365, Number(e.target.value))))}
              min={1} max={365}
              className="w-28 min-h-[40px] bg-white/[0.05] border border-[var(--border-default)] text-[var(--text-primary)] rounded-[var(--radius-sm)] px-3 py-2 text-sm outline-none focus:border-[var(--accent-border)]"
            />
            <span className="text-[var(--text-dim)] text-sm">天</span>
          </div>
        </div>

        <div>
          <label className="block text-[var(--text-secondary)] text-sm font-medium mb-2">预算上限（元）</label>
          <input
            type="number" value={budget}
            onChange={e => setBudget(Math.max(0, Number(e.target.value)))}
            min={0} step={100}
            className="w-36 min-h-[40px] bg-white/[0.05] border border-[var(--border-default)] text-[var(--text-primary)] rounded-[var(--radius-sm)] px-3 py-2 text-sm outline-none focus:border-[var(--accent-border)]"
          />
        </div>

        <Button type="submit" variant="primary" disabled={!selectedItem || loading} loading={loading}>
          {loading ? '计算中…' : '开始分析'}
        </Button>
      </form>

      {error && (
        <div className="rounded-[var(--radius-md)] p-4 mb-6" style={{ background: 'var(--avoid-soft)', border: '1px solid rgba(229,72,77,0.3)' }}>
          <p className="text-sm" style={{ color: '#f5a3a6' }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1 h-5 rounded-full" style={{ background: 'var(--accent)' }} />
            <h2 className="text-[var(--text-primary)] font-semibold">{result.item_name} · {result.days} 天分析结果</h2>
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
          <div className="flex gap-2 mt-4 flex-wrap">
            <Button variant="secondary" onClick={() => navigate(`/item/${selectedItem.id}`)}>查看价格详情</Button>
            <Button variant="ghost" onClick={() => navigate(`/compare/${selectedItem.id}`)}>平台对比</Button>
          </div>
        </div>
      )}
    </div>
  )
}
