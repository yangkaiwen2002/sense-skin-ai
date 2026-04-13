import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getItemCompare, getItemOverview, searchItems } from '../services/api'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import { formatCNY } from '../utils/formatters'
import { PLATFORM_COLORS } from '../utils/constants'

export default function Compare() {
  const { itemId } = useParams()
  const navigate = useNavigate()

  const [compare, setCompare] = useState(null)
  const [item, setItem] = useState(null)
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [searching, setSearching] = useState(false)

  useEffect(() => {
    if (itemId) load(Number(itemId))
  }, [itemId])

  useEffect(() => {
    if (!searchQuery.trim()) { setSuggestions([]); return }
    const t = setTimeout(async () => {
      setSearching(true)
      const res = await searchItems(searchQuery)
      setSuggestions(res?.items || [])
      setSearching(false)
    }, 300)
    return () => clearTimeout(t)
  }, [searchQuery])

  async function load(id) {
    setLoading(true)
    const [cmp, ov] = await Promise.all([getItemCompare(id), getItemOverview(id)])
    setCompare(cmp)
    setItem(ov?.item || null)
    setLoading(false)
  }

  const maxPrice = compare?.platforms?.reduce((m, p) => Math.max(m, p.current_price || 0), 0) || 1

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <button onClick={() => navigate('/')} className="hover:text-slate-300 transition-colors">首页</button>
        <span>/</span>
        <span className="text-slate-300">平台价格对比</span>
      </div>

      <h1 className="text-2xl font-bold text-white mb-6">平台价格对比</h1>

      {/* Search */}
      <div className="relative max-w-lg mb-8">
        <input
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="搜索饰品进行对比..."
          className="w-full bg-slate-800 border border-slate-600 text-white placeholder-slate-500 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-cyan-500"
        />
        {suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-600 rounded-xl overflow-hidden z-10 shadow-xl">
            {suggestions.map(s => (
              <button
                key={s.id}
                onClick={() => { navigate(`/compare/${s.id}`); setSearchQuery(''); setSuggestions([]) }}
                className="w-full text-left px-4 py-3 hover:bg-slate-700 border-b border-slate-700/50 last:border-0"
              >
                <p className="text-white text-sm">{s.skin_name || s.item_name}</p>
                <p className="text-slate-400 text-xs">{s.weapon_type}</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
        </div>
      )}

      {!loading && !compare && !itemId && (
        <div className="text-center py-16 text-slate-500">
          <p className="text-4xl mb-4">🔍</p>
          <p>搜索饰品开始跨平台价格比较</p>
        </div>
      )}

      {compare && item && !loading && (
        <>
          {/* Item header */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-white">{item.skin_name || item.item_name}</h2>
            <p className="text-slate-400 text-sm mt-1">
              {item.weapon_type}{item.exterior ? ` · ${item.exterior}` : ''}{item.rarity ? ` · ${item.rarity}` : ''}
            </p>
          </div>

          {/* Visual bar chart */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6">
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-4">当前价格可视化对比</p>
            <div className="space-y-3">
              {compare.platforms.map(p => {
                const pct = maxPrice > 0 ? ((p.current_price || 0) / maxPrice) * 100 : 0
                const color = PLATFORM_COLORS[p.platform] || '#06b6d4'
                return (
                  <div key={p.platform} className="flex items-center gap-3">
                    <span className="text-slate-300 text-sm w-20 flex-shrink-0">{p.platform}</span>
                    <div className="flex-1 bg-slate-700 rounded-full h-6 overflow-hidden">
                      <div
                        className="h-full rounded-full flex items-center px-3 transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color + '40', border: `1px solid ${color}60` }}
                      />
                    </div>
                    <span className="text-white font-semibold text-sm w-24 text-right flex-shrink-0">
                      {p.current_price != null ? formatCNY(p.current_price) : '—'}
                    </span>
                    {p.is_best_price && (
                      <span className="text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded-full px-2 py-0.5 flex-shrink-0">最优</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Detail table */}
          <PlatformComparisonTable platforms={compare.platforms} itemId={item.id} />

          {compare.best_platform && (
            <p className="text-slate-400 text-sm mt-4 text-center">
              推荐在 <span className="text-cyan-300 font-medium">{compare.best_platform}</span> 购买以获得最优价格
            </p>
          )}
        </>
      )}
    </div>
  )
}
