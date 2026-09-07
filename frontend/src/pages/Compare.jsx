import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { MagnifyingGlass, CaretRight } from '@phosphor-icons/react'
import { getItemCompare, getItemOverview, searchItems } from '../services/api'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import EmptyState from '../components/ui/EmptyState'
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

  useEffect(() => {
    if (itemId) load(Number(itemId))
  }, [itemId])

  useEffect(() => {
    if (!searchQuery.trim()) { setSuggestions([]); return }
    const t = setTimeout(async () => {
      const res = await searchItems(searchQuery)
      setSuggestions(res?.items || res || [])
    }, 300)
    return () => clearTimeout(t)
  }, [searchQuery])

  async function load(id) {
    setLoading(true)
    const [cmp, ov] = await Promise.all([getItemCompare(id), getItemOverview(id)])
    setCompare(cmp)
    setItem(ov?.item || ov || null)
    setLoading(false)
  }

  const maxPrice = compare?.platforms?.reduce((m, p) => Math.max(m, p.current_price || 0), 0) || 1

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center gap-1.5 text-xs text-[var(--text-dim)] mb-5">
        <button onClick={() => navigate('/')} className="hover:text-[var(--text-secondary)] transition-colors">首页</button>
        <CaretRight size={11} />
        <span className="text-[var(--text-secondary)]">平台价格对比</span>
      </div>

      <h1 className="text-xl font-bold text-[var(--text-primary)] mb-6">平台价格对比</h1>

      {/* Search */}
      <div className="relative max-w-lg mb-8">
        <div className="relative">
          <MagnifyingGlass size={16} weight="bold" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-dim)]" />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="搜索饰品进行对比..."
            className="w-full min-h-[44px] bg-white/[0.05] border border-[var(--border-default)] text-[var(--text-primary)]
              placeholder:text-[var(--text-dim)] rounded-[var(--radius-md)] pl-10 pr-4 py-3 text-sm outline-none
              focus:border-[var(--accent-border)] transition-colors duration-150"
          />
        </div>
        {suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 rounded-[var(--radius-md)] border border-[var(--border-default)] overflow-hidden z-10"
            style={{ background: 'var(--bg-surface-raised)', boxShadow: 'var(--shadow-lg)' }}>
            {suggestions.map(s => (
              <button
                key={s.id}
                onClick={() => { navigate(`/compare/${s.id}`); setSearchQuery(''); setSuggestions([]) }}
                className="w-full text-left min-h-[52px] px-4 py-2.5 hover:bg-white/[0.05] border-b border-white/[0.04] last:border-0 transition-colors"
              >
                <p className="text-[var(--text-primary)] text-sm font-medium">{s.skin_name || s.item_name}</p>
                <p className="text-[var(--text-dim)] text-xs mt-0.5">{s.weapon_type}</p>
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--accent-border)', borderTopColor: 'var(--accent)' }} />
        </div>
      )}

      {!loading && !compare && !itemId && (
        <EmptyState icon={MagnifyingGlass} title="开始价格比较" sub="搜索饰品，查看跨平台价格差异" />
      )}

      {compare && item && !loading && (
        <>
          <div className="mb-6">
            <h2 className="text-lg font-bold text-[var(--text-primary)]">{item.skin_name || item.item_name}</h2>
            <p className="text-[var(--text-dim)] text-sm mt-1">
              {item.weapon_type}{item.exterior ? ` · ${item.exterior}` : ''}{item.rarity ? ` · ${item.rarity}` : ''}
            </p>
          </div>

          <div className="surface-card p-5 mb-6">
            <p className="text-[var(--text-dim)] text-[11px] font-medium uppercase tracking-wide mb-4">当前价格可视化对比</p>
            <div className="space-y-3">
              {compare.platforms.map(p => {
                const pct = maxPrice > 0 ? ((p.current_price || 0) / maxPrice) * 100 : 0
                const color = PLATFORM_COLORS[p.platform] || 'var(--accent)'
                return (
                  <div key={p.platform} className="flex items-center gap-3">
                    <span className="text-[var(--text-secondary)] text-sm w-20 shrink-0 truncate">{p.platform}</span>
                    <div className="flex-1 bg-white/[0.06] rounded-full h-6 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color + '40', border: `1px solid ${color}60` }}
                      />
                    </div>
                    <span className="price-display text-sm w-24 text-right shrink-0">
                      {p.current_price != null ? formatCNY(p.current_price) : '—'}
                    </span>
                    {p.is_best_price && (
                      <span className="text-xs rounded-[var(--radius-sm)] px-2 py-0.5 shrink-0" style={{ background: 'var(--accent-soft)', color: 'var(--accent-strong)', border: '1px solid var(--accent-border)' }}>最优</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="surface-card p-5">
            <PlatformComparisonTable platforms={compare.platforms} />
          </div>

          {compare.best_platform && (
            <p className="text-[var(--text-secondary)] text-sm mt-4 text-center">
              推荐在 <span className="font-semibold" style={{ color: 'var(--accent-strong)' }}>{compare.best_platform}</span> 购买以获得最优价格
            </p>
          )}
        </>
      )}
    </div>
  )
}
