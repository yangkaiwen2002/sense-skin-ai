import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import OpportunityPanel from '../components/OpportunityPanel'
import AskSense from '../components/AskSense'
import {
  getItems, getOpportunities, getMarketSummary, getMarketEvents,
  seedDatabase, refreshPrices,
} from '../services/api'
import { formatCNY } from '../utils/formatters'
import { computeScores } from '../components/ScorePanel'

const RARITY_COLOR = {
  '违禁': '#e4ae39', '隐秘': '#eb4b4b', '保密': '#d32ce6',
  '受限': '#8847ff', '军规': '#4b69ff', '精工': '#5e98d9',
}
const RARITY_CLASS = {
  '违禁': 'rarity-contraband', '隐秘': 'rarity-covert', '保密': 'rarity-classified',
  '受限': 'rarity-restricted', '军规': 'rarity-milspec', '精工': 'rarity-industrial',
}
const WEAPON_ABBR = {
  '步枪': 'AR', '狙击枪': 'SNP', '手枪': 'PST', '刀': 'KNF',
  '霰弹枪': 'SHT', '冲锋枪': 'SMG', '机枪': 'MG', '手套': 'GLV',
}

function scoreColor(s) {
  if (s >= 72) return '#22c55e'
  if (s >= 52) return '#f5a623'
  if (s >= 35) return '#f97316'
  return '#ef4444'
}

// ─── Skin image ───────────────────────────────────────────────────────────────
function SkinImage({ iconUrl, name, rarity }) {
  const c   = RARITY_COLOR[rarity] || '#4a8ef5'
  const src = iconUrl?.startsWith('http')
    ? iconUrl
    : `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`
  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)`,
    }}>
      <img
        src={src} alt={name}
        style={{ maxWidth: '88%', maxHeight: 120, objectFit: 'contain', filter: `drop-shadow(0 0 14px ${c}60)` }}
        onError={e => { e.currentTarget.style.display = 'none' }}
      />
    </div>
  )
}

function SkinPlaceholder({ weaponType, rarity, size = 120 }) {
  const abbr = WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')
  const c    = RARITY_COLOR[rarity] || '#4a8ef5'
  return (
    <div style={{
      width: '100%', height: size,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)`,
    }}>
      <div style={{
        fontSize: size * 0.32, fontWeight: 900, color: c, opacity: 0.65,
        fontFamily: 'monospace', lineHeight: 1, textShadow: `0 0 30px ${c}80`,
      }}>{abbr}</div>
    </div>
  )
}

function ScoreBadge({ score }) {
  if (score == null) return null
  const c = scoreColor(score)
  return (
    <div style={{
      position: 'absolute', top: 8, right: 8, zIndex: 2,
      width: 36, height: 36, borderRadius: '50%',
      background: `conic-gradient(${c} ${score * 3.6}deg, rgba(0,0,0,0.6) 0deg)`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      boxShadow: `0 0 12px ${c}50`,
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%', background: '#0d1320',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 10, fontWeight: 800, color: c }}>{score}</span>
      </div>
    </div>
  )
}

function HotItemCard({ item, onClick }) {
  const [hov, setHov] = useState(false)
  const scores = computeScores(item.platforms)
  const best   = item.platforms?.[0] ?? { current_price: item.current_price, platform: item.platform, return_7d: null }
  const up = best?.return_7d != null && best.return_7d >= 0
  const rc = RARITY_COLOR[item.rarity] || '#4a8ef5'

  return (
    <div
      className={`skin-card ${RARITY_CLASS[item.rarity] || ''}`}
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        boxShadow: hov ? `0 20px 48px rgba(0,0,0,0.7), 0 0 0 1px ${rc}30` : 'none',
        borderColor: hov ? `${rc}35` : 'rgba(255,255,255,0.07)',
      }}
    >
      <div style={{ position: 'relative', height: 140, overflow: 'hidden', background: '#080c14' }}>
        {item.icon_url
          ? <SkinImage iconUrl={item.icon_url} name={item.skin_name || item.item_name} rarity={item.rarity} />
          : <SkinPlaceholder weaponType={item.weapon_type} rarity={item.rarity} size={140} />
        }
        <ScoreBadge score={scores?.overall} />
        {item.stattrak && (
          <div style={{
            position: 'absolute', bottom: 6, left: 8, zIndex: 2,
            fontSize: 9, fontWeight: 700, color: '#f5a623',
            background: 'rgba(245,166,35,0.15)', border: '1px solid rgba(245,166,35,0.3)',
            borderRadius: 3, padding: '1px 5px',
          }}>ST</div>
        )}
      </div>
      <div style={{ padding: '10px 11px 12px' }}>
        <p style={{
          fontSize: 12, fontWeight: 700,
          color: hov ? 'white' : 'var(--text-primary)',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          marginBottom: 2, transition: 'color 0.15s',
        }}>
          {item.skin_name || item.item_name}
        </p>
        <p style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 8 }}>
          {item.weapon_type}{item.exterior ? ` · ${item.exterior}` : ''}
        </p>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <p style={{ fontSize: 9, color: 'var(--text-dim)', marginBottom: 1 }}>{best?.platform || 'BUFF'}</p>
            <p className="price-display" style={{ fontSize: 17 }}>
              {best?.current_price != null ? formatCNY(best.current_price) : '—'}
            </p>
          </div>
          {best?.return_7d != null && (
            <span style={{
              fontSize: 11, fontWeight: 700,
              color: up ? '#22c55e' : '#ef4444',
              background: up ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              border: `1px solid ${up ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
              padding: '2px 6px', borderRadius: 4,
            }}>
              {up ? '▲' : '▼'} {Math.abs(best.return_7d * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div style={{
      background: '#0f1520', border: '1px solid rgba(255,255,255,0.05)',
      borderRadius: 10, overflow: 'hidden', animation: 'pulse 1.6s ease infinite',
    }}>
      <div style={{ height: 140, background: 'rgba(255,255,255,0.03)' }} />
      <div style={{ padding: '10px 11px 12px' }}>
        <div style={{ height: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 4, marginBottom: 6 }} />
        <div style={{ height: 9, width: '60%', background: 'rgba(255,255,255,0.03)', borderRadius: 4, marginBottom: 12 }} />
        <div style={{ height: 18, width: '50%', background: 'rgba(255,255,255,0.05)', borderRadius: 4 }} />
      </div>
    </div>
  )
}

// ─── Stat tile ────────────────────────────────────────────────────────────────
function StatTile({ icon, label, value, color, sub }) {
  return (
    <div style={{
      background: '#0f1520', border: '1px solid rgba(255,255,255,0.07)',
      borderRadius: 10, padding: '14px 16px',
      display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
        background: `${color}14`, border: `1px solid ${color}25`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 15, color,
      }}>{icon}</div>
      <div style={{ minWidth: 0 }}>
        <p style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 2 }}>{label}</p>
        <p style={{ fontSize: 16, fontWeight: 700, color, lineHeight: 1 }}>{value}</p>
        {sub && <p style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 2 }}>{sub}</p>}
      </div>
    </div>
  )
}

// ─── Market event card ────────────────────────────────────────────────────────
function EventCard({ evt }) {
  const isUpcoming = evt.days_delta > 0
  const isActive   = evt.timing_class === 'active'
  const isImminent = evt.timing_class === 'imminent'

  const accentColor = isActive || isImminent ? evt.direction_color : evt.type_color
  const typeLabels  = { tournament: '赛事', update: '版本更新', seasonal: '季节性', market: '市场事件' }

  return (
    <div style={{
      background: '#0f1520',
      border: `1px solid ${isImminent || isActive ? accentColor + '35' : 'rgba(255,255,255,0.07)'}`,
      borderRadius: 10,
      padding: '12px 14px',
      flexShrink: 0,
      width: 260,
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* accent line */}
      <div style={{
        position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
        background: accentColor, borderRadius: '10px 0 0 10px', opacity: 0.85,
      }} />

      <div style={{ paddingLeft: 6 }}>
        {/* type badge + timing */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.05em',
            color: evt.type_color, background: `${evt.type_color}15`,
            border: `1px solid ${evt.type_color}30`, borderRadius: 3, padding: '2px 6px',
          }}>
            {typeLabels[evt.event_type] || evt.event_type}
          </span>
          <span style={{
            fontSize: 10, fontWeight: 600,
            color: isActive ? '#22c55e' : isImminent ? '#f5a623' : 'var(--text-dim)',
          }}>
            {isActive && <span style={{ color: '#22c55e', marginRight: 4 }}>●</span>}
            {evt.timing_label}
          </span>
        </div>

        {/* title */}
        <p style={{
          fontSize: 12, fontWeight: 700, color: 'white', lineHeight: 1.3,
          marginBottom: 6,
          overflow: 'hidden', display: '-webkit-box',
          WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
        }}>
          {evt.title}
        </p>

        {/* impact bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 10, color: evt.direction_color, fontWeight: 600 }}>
            {evt.impact_direction === 'positive' ? '▲' : evt.impact_direction === 'negative' ? '▼' : '◆'}
            {' '}{evt.impact_direction === 'positive' ? '正面' : evt.impact_direction === 'negative' ? '负面' : '混合'}
          </span>
          <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.06)', borderRadius: 2 }}>
            <div style={{
              height: 3, borderRadius: 2, background: evt.direction_color,
              width: `${Math.round(evt.impact_strength * 100)}%`, opacity: 0.75,
            }} />
          </div>
          <span style={{ fontSize: 9, color: 'var(--text-dim)' }}>
            {Math.round(evt.impact_strength * 100)}%
          </span>
        </div>
      </div>
    </div>
  )
}

function EventsSkeleton() {
  return (
    <div style={{ display: 'flex', gap: 10 }}>
      {[...Array(4)].map((_, i) => (
        <div key={i} style={{
          flexShrink: 0, width: 260, height: 96,
          background: '#0f1520', border: '1px solid rgba(255,255,255,0.05)',
          borderRadius: 10, animation: 'pulse 1.6s ease infinite',
        }} />
      ))}
    </div>
  )
}

// ─── Section header ───────────────────────────────────────────────────────────
function SectionLabel({ accent, title, sub, action }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 3, height: 18, borderRadius: 2, background: accent || '#4a8ef5' }} />
        <span style={{ fontSize: 15, fontWeight: 700, color: 'white' }}>{title}</span>
        {sub && <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>{sub}</span>}
      </div>
      {action}
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Home() {
  const navigate = useNavigate()

  const [items, setItems]             = useState([])
  const [opportunities, setOpp]       = useState([])
  const [marketSummary, setSum]       = useState(null)
  const [events, setEvents]           = useState([])
  const [loading, setLoading]         = useState(true)
  const [oppLoading, setOppLoading]   = useState(true)
  const [eventsLoading, setEvtLoad]   = useState(true)
  const [seeding, setSeeding]         = useState(false)
  const [refreshing, setRefreshing]   = useState(false)
  const [refreshResult, setRefResult] = useState(null)

  useEffect(() => { loadAll() }, [])

  async function loadAll() {
    setLoading(true)
    setOppLoading(true)
    setEvtLoad(true)

    // Items first so grid renders immediately
    const data = await getItems(50)
    setItems(data || [])
    setLoading(false)

    // Remaining in parallel
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

  // Derive key event for the header pill
  const nextMajor = events.find(e => e.event_type === 'tournament' && e.days_delta > 0)
  const activeEvt = events.find(e => e.timing_class === 'active')
  const featuredEvt = activeEvt || nextMajor

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-page)' }}>

      {/* ══════════════════════════════════════════════
          HEADER — compact, intelligence-first
      ══════════════════════════════════════════════ */}
      <div style={{
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        background: 'linear-gradient(180deg, rgba(74,142,245,0.06) 0%, transparent 100%)',
      }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '28px 20px 24px' }}>

          {/* Top row: brand + search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 220 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <span style={{
                  fontSize: 20, fontWeight: 900, color: 'white', letterSpacing: '-0.02em',
                }}>SenseSkin</span>
                <span style={{
                  fontSize: 10, fontWeight: 600, color: '#4a8ef5', letterSpacing: '0.08em',
                  background: 'rgba(74,142,245,0.12)', border: '1px solid rgba(74,142,245,0.25)',
                  borderRadius: 4, padding: '2px 6px',
                }}>INTELLIGENCE</span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.5 }}>
                CS2 皮肤市场决策系统 · 7维评分 · 事件驱动 · 实时信号
              </p>
            </div>

            {/* Featured event pill */}
            {featuredEvt && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: featuredEvt.timing_class === 'active'
                  ? 'rgba(34,197,94,0.08)' : 'rgba(74,142,245,0.08)',
                border: `1px solid ${featuredEvt.timing_class === 'active'
                  ? 'rgba(34,197,94,0.2)' : 'rgba(74,142,245,0.2)'}`,
                borderRadius: 8, padding: '8px 14px',
              }}>
                {featuredEvt.timing_class === 'active'
                  ? <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', flexShrink: 0, boxShadow: '0 0 6px #22c55e' }} />
                  : <span style={{ fontSize: 13 }}>📅</span>
                }
                <div>
                  <p style={{ fontSize: 11, fontWeight: 700, color: 'white', lineHeight: 1.2 }}>
                    {featuredEvt.title.length > 40 ? featuredEvt.title.slice(0, 40) + '…' : featuredEvt.title}
                  </p>
                  <p style={{ fontSize: 10, color: 'var(--text-dim)' }}>{featuredEvt.timing_label}</p>
                </div>
              </div>
            )}

            <div style={{ width: '100%', maxWidth: 400 }}>
              <SearchBar />
            </div>
          </div>

          {/* Stats row */}
          {!loading && items.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8 }}>
              <StatTile
                icon="◈" label="收录饰品" color="#4a8ef5"
                value={`${items.length} 件`}
              />
              <StatTile
                icon="◉" label="市场情绪" color={marketSummary?.mood_color || '#f5a623'}
                value={marketSummary?.market_mood || '—'}
                sub={marketSummary ? `↑${marketSummary.trend_ups} ↓${marketSummary.trend_downs}` : undefined}
              />
              <StatTile
                icon="▲" label="买入信号" color="#22c55e"
                value={marketSummary?.buy_signals != null ? `${marketSummary.buy_signals} 件` : '—'}
                sub={marketSummary?.watch_signals != null ? `观望 ${marketSummary.watch_signals} 件` : undefined}
              />
              <StatTile
                icon="◎" label="平均评分" color="#8b5cf6"
                value={marketSummary?.avg_score != null ? `${marketSummary.avg_score}` : '—'}
                sub="/ 100"
              />
              <StatTile
                icon="⚡" label="活跃事件" color="#f5a623"
                value={`${events.length} 个`}
                sub={nextMajor ? `下届 Major ${nextMajor.days_delta}天后` : undefined}
              />
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════
          DASHBOARD BODY
      ══════════════════════════════════════════════ */}
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 20px 64px' }}>

        {/* ── Empty state ─────────────────────────── */}
        {noData && (
          <div style={{
            textAlign: 'center', padding: '60px 20px',
            background: '#0f1520', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 16, maxWidth: 400, margin: '0 auto',
          }}>
            <p style={{ fontSize: 32, marginBottom: 12 }}>🎯</p>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: 14 }}>
              数据库为空，初始化示例数据开始
            </p>
            <button
              onClick={handleSeed} disabled={seeding}
              style={{
                background: 'linear-gradient(135deg, #4a8ef5, #6366f1)',
                border: 'none', borderRadius: 8, padding: '10px 28px',
                color: 'white', fontSize: 13, fontWeight: 600,
                cursor: seeding ? 'not-allowed' : 'pointer', opacity: seeding ? 0.6 : 1,
              }}
            >
              {seeding ? '初始化中…' : '初始化示例数据'}
            </button>
          </div>
        )}

        {/* ── Active market events ─────────────────── */}
        {(eventsLoading || events.length > 0) && items.length > 0 && (
          <div style={{ marginBottom: 36 }}>
            <SectionLabel
              accent="#f5a623"
              title="市场事件监控"
              sub={`${events.length} 个活跃信号`}
              action={
                <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                  实时影响评分权重
                </span>
              }
            />
            {eventsLoading ? (
              <EventsSkeleton />
            ) : (
              <div style={{
                display: 'flex', gap: 10, overflowX: 'auto',
                paddingBottom: 6, scrollbarWidth: 'none', msOverflowStyle: 'none',
              }}>
                {events.slice(0, 8).map(evt => (
                  <EventCard key={evt.id} evt={evt} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Opportunity scanner ──────────────────── */}
        {(oppLoading || items.length > 0) && (
          <div style={{ marginBottom: 40 }}>
            <SectionLabel
              accent="linear-gradient(180deg, #22c55e, #4a8ef5)"
              title="机会扫描器"
              sub="AI决策引擎 · 事件感知评分"
              action={
                <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>
                  已扫描 {items.length} 件饰品
                </span>
              }
            />
            <OpportunityPanel opportunities={opportunities} loading={oppLoading} />
          </div>
        )}

        {/* ── Full skin grid ───────────────────────── */}
        {(loading || items.length > 0) && (
          <div style={{ marginBottom: 40 }}>
            <SectionLabel
              accent="linear-gradient(180deg, #4a8ef5, #8b5cf6)"
              title="全部饰品"
              sub="7维评分排行"
              action={
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  {refreshResult && (
                    <span style={{ fontSize: 11, color: '#22c55e' }}>
                      ✓ 已更新 {refreshResult.fetched} 个
                    </span>
                  )}
                  <button
                    onClick={handleRefresh} disabled={refreshing}
                    style={{
                      fontSize: 11, color: '#4a8ef5',
                      background: 'rgba(74,142,245,0.08)', border: '1px solid rgba(74,142,245,0.18)',
                      borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
                      opacity: refreshing ? 0.5 : 1,
                    }}>
                    {refreshing ? '拉取中…' : '刷新价格'}
                  </button>
                  <button
                    onClick={handleSeed} disabled={seeding}
                    style={{
                      fontSize: 11, color: 'var(--text-dim)',
                      background: 'transparent', border: '1px solid rgba(255,255,255,0.07)',
                      borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
                    }}>
                    {seeding ? '重置中…' : '重置数据'}
                  </button>
                </div>
              }
            />
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(175px, 1fr))',
              gap: 14,
            }}>
              {loading
                ? [...Array(8)].map((_, i) => <SkeletonCard key={i} />)
                : items.map(item => (
                    <HotItemCard
                      key={item.id}
                      item={item}
                      onClick={() => navigate(`/item/${item.id}`)}
                    />
                  ))
              }
            </div>
          </div>
        )}

        {/* ── System architecture strip ─────────────── */}
        {items.length > 0 && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
            gap: 10, marginBottom: 48,
            paddingTop: 28, borderTop: '1px solid rgba(255,255,255,0.05)',
          }}>
            {[
              {
                icon: '◎',
                label: '7维评分引擎',
                desc: '稀有度 · 品相 · 流动性 · 趋势 · 估值 · 需求 · 事件信号',
                color: '#4a8ef5',
                onClick: () => navigate(`/item/${items[0]?.id}`),
              },
              {
                icon: '⚡',
                label: '事件驱动信号',
                desc: '22个市场事件实时影响评分，赛事 / 版本 / 季节性信号',
                color: '#f5a623',
                onClick: () => {},
              },
              {
                icon: '◈',
                label: '决策引擎',
                desc: '买入 / 观望 / 持有 / 规避 — 证据链可追溯',
                color: '#22c55e',
                onClick: () => navigate(`/item/${items[0]?.id}`),
              },
              {
                icon: '⬡',
                label: '知识库问答',
                desc: 'TF-IDF检索 · 市场知识 · 策略分析',
                color: '#8b5cf6',
                onClick: () => document.getElementById('ask-sense-section')?.scrollIntoView({ behavior: 'smooth' }),
              },
            ].map(f => (
              <div
                key={f.label}
                onClick={f.onClick}
                style={{
                  background: '#0f1520', border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 10, padding: '16px 14px', cursor: 'pointer',
                  transition: 'border-color 0.15s, transform 0.15s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = `${f.color}30`
                  e.currentTarget.style.transform   = 'translateY(-2px)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
                  e.currentTarget.style.transform   = 'translateY(0)'
                }}
              >
                <span style={{ fontSize: 18, color: f.color, display: 'block', marginBottom: 8 }}>{f.icon}</span>
                <p style={{ fontWeight: 600, color: 'white', marginBottom: 4, fontSize: 13 }}>{f.label}</p>
                <p style={{ fontSize: 11, color: 'var(--text-dim)', lineHeight: 1.5 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── Ask Sense ───────────────────────────── */}
        <div id="ask-sense-section" style={{ paddingTop: 28, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <SectionLabel
            accent="linear-gradient(180deg, #8b5cf6, #4a8ef5)"
            title="Ask Sense"
            sub="知识库检索 · AI问答"
          />
          <AskSense />
        </div>

      </div>
    </div>
  )
}
