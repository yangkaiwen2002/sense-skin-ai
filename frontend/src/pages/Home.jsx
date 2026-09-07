import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Cube, Gauge, TrendUp, ChartLineUp, Lightning, Target, BookOpen,
  CalendarBlank, ArrowsClockwise, ArrowClockwise, MagnifyingGlass,
} from '@phosphor-icons/react'
import SearchBar from '../components/SearchBar'
import OpportunityPanel from '../components/OpportunityPanel'
import AskSense from '../components/AskSense'
import Button from '../components/ui/Button'
import EmptyState from '../components/ui/EmptyState'
import Skeleton from '../components/ui/Skeleton'
import { ScoreRing } from '../components/ui/Score'
import {
  getItems, getOpportunities, getMarketSummary, getMarketEvents,
  seedDatabase, refreshPrices,
} from '../services/api'
import { formatCNY } from '../utils/formatters'
import { RARITY_COLOR, RARITY_CLASS, WEAPON_ABBR } from '../utils/constants'

// ─── Skin visual (image or weapon-abbr placeholder) ───────────────────────────
function SkinVisual({ iconUrl, name, weaponType, rarity }) {
  const c = RARITY_COLOR[rarity] || 'var(--accent)'
  const src = iconUrl?.startsWith('http')
    ? iconUrl
    : iconUrl ? `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f` : null

  return (
    <div
      className="w-full h-full flex items-center justify-center"
      style={{ background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)` }}
    >
      {src ? (
        <img
          src={src} alt={name}
          className="max-w-[88%] max-h-[120px] object-contain"
          style={{ filter: `drop-shadow(0 0 14px ${c}60)` }}
          onError={e => { e.currentTarget.style.display = 'none' }}
        />
      ) : (
        <span
          className="font-mono font-black leading-none"
          style={{ fontSize: 44, color: c, opacity: 0.65, textShadow: `0 0 30px ${c}80` }}
        >
          {WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')}
        </span>
      )}
    </div>
  )
}

function HotItemCard({ item, onClick }) {
  const scores = { overall: computeOverall(item) }
  const best = item.platforms?.[0] ?? { current_price: item.current_price, platform: item.platform, return_7d: null }
  const up = best?.return_7d != null && best.return_7d >= 0
  const rc = RARITY_COLOR[item.rarity] || 'var(--accent)'

  return (
    <div
      className={`skin-card group ${RARITY_CLASS[item.rarity] || ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={e => { if (e.key === 'Enter') onClick() }}
    >
      <div className="relative h-[130px] sm:h-[140px] overflow-hidden bg-[var(--bg-surface-sunken)]">
        <SkinVisual iconUrl={item.icon_url} name={item.skin_name || item.item_name} weaponType={item.weapon_type} rarity={item.rarity} />
        {scores.overall != null && (
          <div className="absolute top-2 right-2 z-[2]">
            <ScoreRing score={scores.overall} size={34} variant="badge" showLabel={false} />
          </div>
        )}
        {item.stattrak && (
          <div className="absolute bottom-1.5 left-2 z-[2] text-[9px] font-bold text-[var(--gold)] bg-[var(--gold-soft)] border border-[var(--gold-border)] rounded px-1.5 py-px">
            ST
          </div>
        )}
      </div>
      <div className="p-2.5 pb-3">
        <p className="text-xs font-bold text-[var(--text-primary)] truncate mb-0.5 group-hover:text-white transition-colors">
          {item.skin_name || item.item_name}
        </p>
        <p className="text-[10px] text-[var(--text-dim)] mb-2 truncate">
          {item.weapon_type}{item.exterior ? ` · ${item.exterior}` : ''}
        </p>
        <div className="flex justify-between items-end">
          <div>
            <p className="text-[9px] text-[var(--text-dim)] mb-0.5">{best?.platform || 'BUFF'}</p>
            <p className="price-display text-[17px]">
              {best?.current_price != null ? formatCNY(best.current_price) : '—'}
            </p>
          </div>
          {best?.return_7d != null && (
            <span
              className={`text-[11px] font-bold font-tabular px-1.5 py-0.5 rounded border
                ${up ? 'text-[var(--up)] bg-[var(--buy-soft)] border-[var(--buy)]/25' : 'text-[var(--down)] bg-[var(--avoid-soft)] border-[var(--avoid)]/25'}`}
            >
              {up ? '▲' : '▼'} {Math.abs(best.return_7d * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

// Lightweight overall-score approximation for grid cards (full 7-dim score
// lives server-side; this mirrors the same value/liquidity/trend blend used
// across the app for a consistent badge at a glance).
function computeOverall(item) {
  const best = item.platforms?.[0]
  if (!best) return null
  const liquidity = Math.max(0, Math.min(100, best.liquidity_score ?? 40))
  const vol = best.volatility_7d ?? 0.04
  const stability = Math.max(0, Math.min(100, (1 - vol * 12) * 100))
  const ret7d = best.return_7d ?? 0
  const trend = Math.max(0, Math.min(100, 50 + ret7d * 300))
  const cur = best.current_price ?? 0
  const avg30 = best.avg_30d ?? cur
  const valueDelta = avg30 > 0 ? (avg30 - cur) / avg30 : 0
  const value = Math.max(0, Math.min(100, 50 + valueDelta * 300))
  return Math.round(0.3 * value + 0.25 * liquidity + 0.25 * stability + 0.2 * trend)
}

function SkeletonCard() {
  return (
    <div className="surface-card overflow-hidden">
      <Skeleton h={130} radius={0} />
      <div className="p-2.5 pb-3">
        <Skeleton h={12} className="mb-1.5" />
        <Skeleton h={9} w="60%" className="mb-3" />
        <Skeleton h={18} w="50%" />
      </div>
    </div>
  )
}

// ─── Stat tile ────────────────────────────────────────────────────────────────
function StatTile({ icon: Icon, label, value, color, sub }) {
  return (
    <div className="surface-card flex items-center gap-3 py-3 px-3.5">
      <div
        className="w-9 h-9 rounded-[var(--radius-sm)] shrink-0 flex items-center justify-center border"
        style={{ background: `${color}16`, borderColor: `${color}30` }}
      >
        <Icon size={16} weight="bold" style={{ color }} />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] text-[var(--text-dim)] mb-0.5 truncate">{label}</p>
        <p className="text-base font-bold font-tabular leading-none" style={{ color }}>{value}</p>
        {sub && <p className="text-[10px] text-[var(--text-dim)] mt-1 truncate">{sub}</p>}
      </div>
    </div>
  )
}

// ─── Market event card ────────────────────────────────────────────────────────
function EventCard({ evt }) {
  const isActive = evt.timing_class === 'active'
  const isImminent = evt.timing_class === 'imminent'
  const accentColor = isActive || isImminent ? evt.direction_color : evt.type_color
  const typeLabels = { tournament: '赛事', update: '版本更新', seasonal: '季节性', market: '市场事件' }

  return (
    <div
      className="snap-start shrink-0 w-[248px] sm:w-[260px] relative overflow-hidden rounded-[var(--radius-md)] p-3"
      style={{
        background: 'var(--bg-card)',
        border: `1px solid ${isImminent || isActive ? accentColor + '35' : 'var(--border-subtle)'}`,
      }}
    >
      <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-[var(--radius-md)] opacity-85" style={{ background: accentColor }} />
      <div className="pl-1.5">
        <div className="flex items-center justify-between mb-1.5">
          <span
            className="text-[9px] font-bold tracking-wide rounded px-1.5 py-0.5 border"
            style={{ color: evt.type_color, background: `${evt.type_color}15`, borderColor: `${evt.type_color}30` }}
          >
            {typeLabels[evt.event_type] || evt.event_type}
          </span>
          <span className="text-[10px] font-semibold flex items-center gap-1" style={{ color: isActive ? 'var(--buy)' : isImminent ? 'var(--gold)' : 'var(--text-dim)' }}>
            {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[var(--buy)] shadow-[0_0_6px_var(--buy)]" />}
            {evt.timing_label}
          </span>
        </div>
        <p className="text-xs font-bold text-[var(--text-primary)] leading-snug mb-1.5 line-clamp-2">{evt.title}</p>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-semibold" style={{ color: evt.direction_color }}>
            {evt.impact_direction === 'positive' ? '▲' : evt.impact_direction === 'negative' ? '▼' : '◆'}{' '}
            {evt.impact_direction === 'positive' ? '正面' : evt.impact_direction === 'negative' ? '负面' : '混合'}
          </span>
          <div className="flex-1 h-[3px] bg-white/[0.06] rounded-full overflow-hidden">
            <div className="h-full rounded-full opacity-75" style={{ background: evt.direction_color, width: `${Math.round(evt.impact_strength * 100)}%` }} />
          </div>
          <span className="text-[9px] text-[var(--text-dim)] font-tabular">{Math.round(evt.impact_strength * 100)}%</span>
        </div>
      </div>
    </div>
  )
}

function ScrollRail({ children, className = '' }) {
  return (
    <div
      className={`flex gap-2.5 overflow-x-auto no-scrollbar snap-x snap-mandatory pb-1.5 -mx-4 px-4 sm:mx-0 sm:px-0 ${className}`}
      style={{ maskImage: 'linear-gradient(90deg, black 92%, transparent)' }}
    >
      {children}
    </div>
  )
}

// ─── Section header ───────────────────────────────────────────────────────────
function SectionLabel({ accent, title, sub, action }) {
  return (
    <div className="flex items-center justify-between gap-3 mb-3.5 flex-wrap">
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="w-[3px] h-[18px] rounded-full shrink-0" style={{ background: accent || 'var(--accent)' }} />
        <span className="text-[15px] font-bold text-[var(--text-primary)] truncate">{title}</span>
        {sub && <span className="text-[11px] text-[var(--text-dim)] hidden sm:inline">{sub}</span>}
      </div>
      {action}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Home() {
  const navigate = useNavigate()

  const [items, setItems] = useState([])
  const [opportunities, setOpp] = useState([])
  const [marketSummary, setSum] = useState(null)
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [oppLoading, setOppLoading] = useState(true)
  const [eventsLoading, setEvtLoad] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshResult, setRefResult] = useState(null)

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    setLoading(true)
    setOppLoading(true)
    setEvtLoad(true)

    const data = await getItems(50)
    setItems(data || [])
    setLoading(false)

    const [opps, summary, evtData] = await Promise.all([
      getOpportunities(8),
      getMarketSummary(),
      getMarketEvents(),
    ])
    setOpp(opps?.opportunities || [])
    setSum(summary || null)
    setEvents(evtData?.events || [])
    setOppLoading(false)
    setEvtLoad(false)
  }

  async function handleSeed() {
    setSeeding(true)
    await seedDatabase()
    setSeeding(false)
    loadAll()
  }

  async function handleRefresh() {
    setRefreshing(true)
    const res = await refreshPrices()
    setRefreshing(false)
    setRefResult(res)
    setTimeout(() => { loadAll(); setRefResult(null) }, 2500)
  }

  const noData = !loading && items.length === 0
  const nextMajor = events.find(e => e.event_type === 'tournament' && e.days_delta > 0)
  const activeEvt = events.find(e => e.timing_class === 'active')
  const featuredEvt = activeEvt || nextMajor

  const FEATURES = [
    {
      icon: ChartLineUp, label: '7维评分引擎', color: 'var(--accent-strong)',
      desc: '稀有度 · 品相 · 流动性 · 趋势 · 估值 · 需求 · 事件信号',
      onClick: () => items[0] && navigate(`/item/${items[0].id}`),
    },
    {
      icon: Lightning, label: '事件驱动信号', color: 'var(--gold)',
      desc: '22个市场事件实时影响评分，赛事 / 版本 / 季节性信号',
      onClick: () => {},
    },
    {
      icon: Target, label: '决策引擎', color: 'var(--buy)',
      desc: '买入 / 观望 / 持有 / 规避 — 证据链可追溯',
      onClick: () => items[0] && navigate(`/item/${items[0].id}`),
    },
    {
      icon: BookOpen, label: '知识库问答', color: 'var(--accent-strong)',
      desc: 'RAG 混合检索 · 市场知识 · 策略分析',
      onClick: () => document.getElementById('ask-sense-section')?.scrollIntoView({ behavior: 'smooth' }),
    },
  ]

  return (
    <div className="min-h-screen bg-[var(--bg-page)]">

      {/* ══════════ HEADER ══════════ */}
      <div className="border-b border-[var(--border-subtle)]" style={{ background: 'linear-gradient(180deg, rgba(46,86,232,0.06) 0%, transparent 100%)' }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-6 sm:pt-7 pb-6">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:gap-5 mb-5">
            <div className="flex-1 min-w-0">
              <h1 className="text-lg sm:text-xl font-extrabold text-[var(--text-primary)] tracking-tight mb-1">
                什么皮肤现在值得关注？
              </h1>
              <p className="text-xs text-[var(--text-dim)] leading-relaxed">
                CS2 皮肤市场决策系统 · 7维评分 · 事件驱动 · 实时信号
              </p>
            </div>

            {featuredEvt && (
              <div
                className="flex items-center gap-2.5 rounded-[var(--radius-sm)] px-3.5 py-2 border shrink-0"
                style={{
                  background: featuredEvt.timing_class === 'active' ? 'var(--buy-soft)' : 'var(--accent-soft)',
                  borderColor: featuredEvt.timing_class === 'active' ? 'rgba(47,184,102,0.3)' : 'var(--accent-border)',
                }}
              >
                {featuredEvt.timing_class === 'active'
                  ? <span className="w-[7px] h-[7px] rounded-full bg-[var(--buy)] shrink-0 shadow-[0_0_6px_var(--buy)]" />
                  : <CalendarBlank size={14} weight="bold" className="text-[var(--accent-strong)] shrink-0" />
                }
                <div className="min-w-0">
                  <p className="text-[11px] font-bold text-[var(--text-primary)] leading-tight truncate max-w-[220px]">
                    {featuredEvt.title}
                  </p>
                  <p className="text-[10px] text-[var(--text-dim)]">{featuredEvt.timing_label}</p>
                </div>
              </div>
            )}
          </div>

          <div className="max-w-xl mb-5">
            <SearchBar />
          </div>

          {!loading && items.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
              <StatTile icon={Cube} label="收录饰品" color="var(--accent-strong)" value={`${items.length} 件`} />
              <StatTile
                icon={Gauge} label="市场情绪" color={marketSummary?.mood_color || 'var(--accent-strong)'}
                value={marketSummary?.market_mood || '—'}
                sub={marketSummary ? `↑${marketSummary.trend_ups} ↓${marketSummary.trend_downs}` : undefined}
              />
              <StatTile
                icon={TrendUp} label="买入信号" color="var(--buy)"
                value={marketSummary?.buy_signals != null ? `${marketSummary.buy_signals} 件` : '—'}
                sub={marketSummary?.watch_signals != null ? `观望 ${marketSummary.watch_signals} 件` : undefined}
              />
              <StatTile
                icon={ChartLineUp} label="平均评分" color="var(--accent-strong)"
                value={marketSummary?.avg_score != null ? `${marketSummary.avg_score}` : '—'} sub="/ 100"
              />
              <StatTile
                icon={Lightning} label="活跃事件" color="var(--gold)"
                value={`${events.length} 个`}
                sub={nextMajor ? `下届 Major ${nextMajor.days_delta}天后` : undefined}
              />
            </div>
          )}
        </div>
      </div>

      {/* ══════════ BODY ══════════ */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-16">

        {noData && (
          <EmptyState
            icon={MagnifyingGlass}
            title="数据库为空"
            sub="初始化示例数据以开始探索市场机会"
            className="max-w-sm mx-auto surface-card"
            action={
              <Button variant="primary" onClick={handleSeed} loading={seeding}>
                {seeding ? '初始化中…' : '初始化示例数据'}
              </Button>
            }
          />
        )}

        {(eventsLoading || events.length > 0) && items.length > 0 && (
          <div className="mb-8">
            <SectionLabel accent="var(--gold)" title="市场事件监控" sub={`${events.length} 个活跃信号`}
              action={<span className="text-[10px] text-[var(--text-dim)] hidden sm:inline">实时影响评分权重</span>} />
            {eventsLoading ? (
              <div className="flex gap-2.5">
                {[...Array(4)].map((_, i) => <Skeleton key={i} w={252} h={96} className="shrink-0" />)}
              </div>
            ) : (
              <ScrollRail>
                {events.slice(0, 8).map(evt => <EventCard key={evt.id} evt={evt} />)}
              </ScrollRail>
            )}
          </div>
        )}

        {(oppLoading || items.length > 0) && (
          <div className="mb-9">
            <SectionLabel accent="var(--buy)" title="机会扫描器" sub="AI决策引擎 · 事件感知评分"
              action={<span className="text-[11px] text-[var(--text-dim)] hidden sm:inline">已扫描 {items.length} 件饰品</span>} />
            <OpportunityPanel opportunities={opportunities} loading={oppLoading} />
          </div>
        )}

        {(loading || items.length > 0) && (
          <div className="mb-9">
            <SectionLabel accent="var(--accent)" title="全部饰品" sub="7维评分排行"
              action={
                <div className="flex gap-2 items-center">
                  {refreshResult && (
                    <span className="text-[11px] text-[var(--buy)] hidden sm:inline">✓ 已更新 {refreshResult.fetched} 个</span>
                  )}
                  <Button variant="secondary" size="sm" onClick={handleRefresh} loading={refreshing}>
                    <ArrowsClockwise size={13} weight="bold" />
                    {refreshing ? '拉取中…' : '刷新价格'}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={handleSeed} loading={seeding}>
                    <ArrowClockwise size={13} weight="bold" />
                    {seeding ? '重置中…' : '重置数据'}
                  </Button>
                </div>
              } />
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
              {loading
                ? [...Array(10)].map((_, i) => <SkeletonCard key={i} />)
                : items.map(item => (
                  <HotItemCard key={item.id} item={item} onClick={() => navigate(`/item/${item.id}`)} />
                ))
              }
            </div>
          </div>
        )}

        {items.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 mb-12 pt-6 border-t border-[var(--border-subtle)]">
            {FEATURES.map(f => (
              <div
                key={f.label}
                onClick={f.onClick}
                className="surface-card p-4 cursor-pointer transition-all duration-150 hover:-translate-y-0.5 hover:border-[var(--border-default)]"
              >
                <f.icon size={18} weight="bold" style={{ color: f.color }} className="block mb-2" />
                <p className="font-semibold text-[var(--text-primary)] mb-1 text-[13px]">{f.label}</p>
                <p className="text-[11px] text-[var(--text-dim)] leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        )}

        <div id="ask-sense-section" className="pt-6 border-t border-[var(--border-subtle)]">
          <SectionLabel accent="var(--accent)" title="Ask Sense" sub="知识库检索 · AI问答" />
          <AskSense />
        </div>

      </div>
    </div>
  )
}
