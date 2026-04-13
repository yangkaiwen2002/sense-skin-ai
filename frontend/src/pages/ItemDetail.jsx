import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import TrendChart from '../components/TrendChart'
import PriceSummaryCard from '../components/PriceSummaryCard'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import EventTimeline from '../components/EventTimeline'
import AIReportPanel from '../components/AIReportPanel'
import RiskBadge from '../components/RiskBadge'
import { getItemOverview, getItemHistory, getItemCompare, getItemEvents } from '../services/api'
import { formatCNY } from '../utils/formatters'

const PLATFORM_OPTIONS = ['BUFF', 'Steam', '悠悠有品', 'IGXE']

export default function ItemDetail() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const id = Number(itemId)

  const [overview, setOverview] = useState(null)
  const [history, setHistory] = useState([])
  const [compare, setCompare] = useState(null)
  const [events, setEvents] = useState([])
  const [selectedPlatform, setSelectedPlatform] = useState('BUFF')
  const [historyDays, setHistoryDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!id) return
    loadAll()
  }, [id])

  useEffect(() => {
    loadHistory()
  }, [id, selectedPlatform, historyDays])

  async function loadAll() {
    setLoading(true)
    setError(null)
    const [ov, cmp, ev] = await Promise.all([
      getItemOverview(id),
      getItemCompare(id),
      getItemEvents(id, 60),
    ])
    if (!ov) {
      setError('饰品数据未找到')
      setLoading(false)
      return
    }
    setOverview(ov)
    setCompare(cmp)
    setEvents(ev?.events || [])
    setLoading(false)
  }

  async function loadHistory() {
    const data = await getItemHistory(id, historyDays, selectedPlatform)
    setHistory(data?.history || [])
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-10">
        <div className="flex items-center justify-center py-24">
          <div className="w-8 h-8 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (error || !overview) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-10 text-center">
        <p className="text-red-400 mb-4">{error || '数据加载失败'}</p>
        <button onClick={() => navigate('/')} className="text-cyan-400 text-sm hover:text-cyan-300 underline">
          返回首页
        </button>
      </div>
    )
  }

  const item = overview.item
  const platforms = overview.platforms || []
  const bestPlatform = platforms[0]

  const allRiskLabels = [...new Set(platforms.flatMap(p => p.risk_labels || []))]

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
        <button onClick={() => navigate('/')} className="hover:text-slate-300 transition-colors">首页</button>
        <span>/</span>
        <span className="text-slate-300">{item.skin_name || item.item_name}</span>
      </div>

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">{item.skin_name || item.item_name}</h1>
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-400">
            <span>{item.weapon_type}</span>
            {item.exterior && <><span>·</span><span>{item.exterior}</span></>}
            {item.rarity && <><span>·</span><span>{item.rarity}</span></>}
            {item.stattrak && <span className="text-orange-400 font-medium">StatTrak™</span>}
            {item.souvenir && <span className="text-yellow-400 font-medium">纪念品</span>}
          </div>
          {allRiskLabels.length > 0 && (
            <div className="mt-3">
              <RiskBadge labels={allRiskLabels} />
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate(`/compare/${id}`)}
            className="bg-slate-700 hover:bg-slate-600 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            平台对比
          </button>
          <button
            onClick={() => navigate('/rent-vs-buy')}
            className="bg-cyan-700 hover:bg-cyan-600 text-white text-sm px-4 py-2 rounded-lg transition-colors"
          >
            租 vs 买
          </button>
        </div>
      </div>

      {/* Best price banner */}
      {bestPlatform && (
        <div className="bg-gradient-to-r from-cyan-900/30 to-slate-800 border border-cyan-500/20 rounded-xl p-4 mb-8 flex flex-col sm:flex-row sm:items-center gap-4">
          <div>
            <p className="text-slate-400 text-xs mb-0.5">全平台最优价格</p>
            <p className="text-3xl font-bold text-white">{formatCNY(bestPlatform.current_price)}</p>
          </div>
          <div className="h-px sm:h-10 sm:w-px bg-slate-700" />
          <div>
            <p className="text-slate-400 text-xs mb-0.5">推荐平台</p>
            <p className="text-white font-semibold">{bestPlatform.platform}</p>
          </div>
          {bestPlatform.return_7d != null && (
            <>
              <div className="h-px sm:h-10 sm:w-px bg-slate-700" />
              <div>
                <p className="text-slate-400 text-xs mb-0.5">7 日涨跌</p>
                <p className={`font-semibold ${bestPlatform.return_7d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {bestPlatform.return_7d >= 0 ? '+' : ''}{(bestPlatform.return_7d * 100).toFixed(2)}%
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column — chart + events */}
        <div className="lg:col-span-2 space-y-6">
          {/* Chart controls */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex gap-2">
                {PLATFORM_OPTIONS.map(p => (
                  <button
                    key={p}
                    onClick={() => setSelectedPlatform(p)}
                    className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                      selectedPlatform === p
                        ? 'bg-cyan-600 text-white'
                        : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <div className="flex gap-1">
                {[7, 14, 30].map(d => (
                  <button
                    key={d}
                    onClick={() => setHistoryDays(d)}
                    className={`text-xs px-2.5 py-1.5 rounded-lg transition-colors ${
                      historyDays === d
                        ? 'bg-slate-600 text-white'
                        : 'bg-slate-800 text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {d}天
                  </button>
                ))}
              </div>
            </div>
            <TrendChart
              data={history}
              avg7d={platforms.find(p => p.platform === selectedPlatform)?.avg_7d}
              avg30d={platforms.find(p => p.platform === selectedPlatform)?.avg_30d}
            />
          </div>

          {/* Platform comparison table */}
          {compare && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="w-1 h-4 bg-slate-500 rounded-full" />
                <h3 className="text-slate-300 font-medium text-sm">平台价格对比</h3>
              </div>
              <PlatformComparisonTable platforms={compare.platforms} itemId={id} />
            </div>
          )}

          {/* Event timeline */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1 h-4 bg-slate-500 rounded-full" />
              <h3 className="text-slate-300 font-medium text-sm">近期市场事件</h3>
            </div>
            <EventTimeline events={events} />
          </div>
        </div>

        {/* Right column — platform cards + AI report */}
        <div className="space-y-4">
          {platforms.map(p => (
            <PriceSummaryCard key={p.platform} {...p} />
          ))}
          <AIReportPanel itemId={id} />
        </div>
      </div>
    </div>
  )
}
