import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import { getItemOverview, seedDatabase, refreshPrices } from '../services/api'
import { formatCNY, formatPercent } from '../utils/formatters'
import { EVENT_TYPE_LABELS, EVENT_TYPE_COLORS } from '../utils/constants'

const HOT_ITEM_IDS = [1, 2, 3, 4, 5, 6]

function HotItemCard({ item, onClick }) {
  const returnPos = item.return_7d != null && item.return_7d >= 0
  return (
    <div
      onClick={onClick}
      className="bg-slate-800 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-cyan-500/50 hover:bg-slate-750 transition-all group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <p className="text-white font-semibold text-sm truncate group-hover:text-cyan-300 transition-colors">
            {item.skin_name || item.item_name}
          </p>
          <p className="text-slate-500 text-xs mt-0.5 truncate">{item.weapon_type}</p>
        </div>
        {item.return_7d != null && (
          <span className={`ml-2 text-sm font-bold flex-shrink-0 ${returnPos ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(item.return_7d)}
          </span>
        )}
      </div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-slate-400 text-xs">最优价格</p>
          <p className="text-xl font-bold text-white">
            {item.best_price != null ? formatCNY(item.best_price) : '—'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-slate-500 text-xs">{item.best_platform || '—'}</p>
        </div>
      </div>
    </div>
  )
}

function RecentEventItem({ event }) {
  const colors = EVENT_TYPE_COLORS[event.event_type] || EVENT_TYPE_COLORS.game_update
  return (
    <div className={`flex gap-3 p-3 rounded-lg border ${colors.bg}`}>
      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${colors.dot}`} />
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <span className={`text-xs font-medium ${colors.text}`}>
            {EVENT_TYPE_LABELS[event.event_type] || event.event_type}
          </span>
          <span className="text-slate-500 text-xs">{event.event_date}</span>
        </div>
        <p className="text-white text-sm font-medium truncate">{event.title}</p>
        {event.summary && (
          <p className="text-slate-400 text-xs mt-0.5 line-clamp-2">{event.summary}</p>
        )}
      </div>
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const [hotItems, setHotItems] = useState([])
  const [recentEvents, setRecentEvents] = useState([])
  const [seeding, setSeeding] = useState(false)
  const [seedDone, setSeedDone] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshResult, setRefreshResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHotItems()
  }, [])

  async function loadHotItems() {
    setLoading(true)
    const results = await Promise.all(
      HOT_ITEM_IDS.map(id =>
        getItemOverview(id).then(data => {
          if (!data) return null
          const best = data.platforms?.[0]
          return {
            id,
            item_name: data.item?.item_name,
            skin_name: data.item?.skin_name,
            weapon_type: data.item?.weapon_type,
            best_price: best?.current_price,
            best_platform: best?.platform,
            return_7d: best?.return_7d,
          }
        })
      )
    )
    const valid = results.filter(Boolean)
    setHotItems(valid)

    // Collect recent events from all items
    const allEvents = []
    results.filter(Boolean).forEach(item => {
      // Events will be loaded separately if needed; for now just show items
    })
    setLoading(false)
  }

  async function handleSeed() {
    setSeeding(true)
    const res = await seedDatabase()
    setSeeding(false)
    if (res) {
      setSeedDone(true)
      setTimeout(() => {
        loadHotItems()
        setSeedDone(false)
      }, 1500)
    }
  }

  async function handleRefresh() {
    setRefreshing(true)
    setRefreshResult(null)
    const res = await refreshPrices()
    setRefreshing(false)
    if (res) {
      setRefreshResult(res)
      setTimeout(() => {
        loadHotItems()
        setRefreshResult(null)
      }, 3000)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-10">
      {/* Hero */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-4 py-1.5 mb-6">
          <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-cyan-400 text-xs font-medium">实时市场数据 · AI 智能分析</span>
        </div>
        <h1 className="text-4xl font-bold text-white mb-3">
          CS2 饰品市场<span className="text-cyan-400">智能助手</span>
        </h1>
        <p className="text-slate-400 text-lg mb-8 max-w-xl mx-auto">
          多平台价格对比、租买决策分析、AI 市场报告，一站式 CS2 饰品投资工具
        </p>
        <div className="max-w-xl mx-auto">
          <SearchBar />
        </div>
      </div>

      {/* Seed button */}
      {!loading && hotItems.length === 0 && (
        <div className="text-center mb-10">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 max-w-md mx-auto">
            <p className="text-slate-300 text-sm mb-4">数据库为空，请先初始化示例数据</p>
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-sm font-medium px-6 py-2.5 rounded-lg transition-colors"
            >
              {seeding ? '初始化中...' : seedDone ? '初始化成功！' : '初始化示例数据'}
            </button>
          </div>
        </div>
      )}

      {/* Action buttons */}
      {hotItems.length > 0 && (
        <div className="flex items-center justify-end gap-2 mb-6">
          {refreshResult && (
            <span className="text-xs text-green-400 mr-2">
              ✓ 已更新 {refreshResult.fetched} 个饰品的实时价格
            </span>
          )}
          <button
            onClick={handleRefresh}
            disabled={refreshing || seeding}
            className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 border border-cyan-500/30 hover:border-cyan-400/50 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
          >
            {refreshing ? (
              <>
                <div className="w-3 h-3 border border-cyan-400/40 border-t-cyan-400 rounded-full animate-spin" />
                拉取中... (约15秒)
              </>
            ) : '拉取实时价格'}
          </button>
          <button
            onClick={handleSeed}
            disabled={seeding || refreshing}
            className="text-xs text-slate-500 hover:text-slate-400 border border-slate-700 rounded-lg px-3 py-1.5 transition-colors disabled:opacity-50"
          >
            {seeding ? '重置中...' : seedDone ? '完成！' : '重置示例数据'}
          </button>
        </div>
      )}

      {/* Hot items grid */}
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-5 bg-cyan-500 rounded-full" />
          <h2 className="text-white font-semibold">热门饰品</h2>
          <span className="text-slate-500 text-sm">/ 快速查看市场动态</span>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-4 h-28 animate-pulse" />
            ))}
          </div>
        ) : hotItems.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {hotItems.map(item => (
              <HotItemCard
                key={item.id}
                item={item}
                onClick={() => navigate(`/item/${item.id}`)}
              />
            ))}
          </div>
        ) : null}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          {
            title: '价格走势',
            desc: '查看 30 天历史价格，7/30 日均线参考',
            icon: '📈',
            path: hotItems[0] ? `/item/${hotItems[0].id}` : '/item/1',
          },
          {
            title: '租 vs 买',
            desc: '输入使用天数，计算最优方案',
            icon: '⚖️',
            path: '/rent-vs-buy',
          },
          {
            title: '平台比较',
            desc: '多平台价格对比，找到最优购买渠道',
            icon: '🔍',
            path: hotItems[0] ? `/compare/${hotItems[0].id}` : '/item/1',
          },
        ].map(f => (
          <div
            key={f.title}
            onClick={() => navigate(f.path)}
            className="bg-slate-800 border border-slate-700 rounded-xl p-5 cursor-pointer hover:border-slate-500 transition-colors group"
          >
            <span className="text-2xl mb-3 block">{f.icon}</span>
            <p className="text-white font-semibold mb-1 group-hover:text-cyan-300 transition-colors">{f.title}</p>
            <p className="text-slate-400 text-sm">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
