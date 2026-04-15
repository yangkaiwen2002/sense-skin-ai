import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import { getItems, seedDatabase, refreshPrices } from '../services/api'
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

function SkinImage({ iconUrl, name, rarity }) {
  const c = RARITY_COLOR[rarity] || '#4a8ef5'
  const src = iconUrl.startsWith('http')
    ? iconUrl
    : `https://community.cloudflare.steamstatic.com/economy/image/${iconUrl}`
  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)`,
    }}>
      <img
        src={src}
        alt={name}
        style={{
          maxWidth: '88%', maxHeight: 120, objectFit: 'contain',
          filter: `drop-shadow(0 0 14px ${c}60)`,
        }}
        onError={e => { e.currentTarget.style.display = 'none' }}
      />
    </div>
  )
}

function SkinPlaceholder({ weaponType, rarity, size = 120 }) {
  const abbr = WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')
  const c = RARITY_COLOR[rarity] || '#4a8ef5'
  return (
    <div style={{
      width: '100%', height: size,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
      background: `radial-gradient(ellipse at center, ${c}18 0%, transparent 70%)`,
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse at 50% 50%, ${c}12 0%, transparent 65%)`,
      }} />
      <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
        <div style={{
          fontSize: size * 0.32, fontWeight: 900, color: c, opacity: 0.65,
          fontFamily: 'monospace', lineHeight: 1,
          textShadow: `0 0 30px ${c}80`,
          filter: `drop-shadow(0 0 12px ${c}60)`,
        }}>{abbr}</div>
      </div>
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
        width: 28, height: 28, borderRadius: '50%',
        background: '#0d1320',
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
  // Support both full platform analytics (overview) and flat list response
  const best = item.platforms?.[0] ?? {
    current_price: item.current_price,
    platform: item.platform,
    return_7d: null,
  }
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
      {/* Image zone */}
      <div style={{ position: 'relative', height: 140, overflow: 'hidden', background: '#080c14' }}>
        {item.icon_url ? (
          <SkinImage iconUrl={item.icon_url} name={item.skin_name || item.item_name} rarity={item.rarity} />
        ) : (
          <SkinPlaceholder weaponType={item.weapon_type} rarity={item.rarity} size={140} />
        )}
        <ScoreBadge score={scores?.overall} />
        {item.stattrak && (
          <div style={{
            position: 'absolute', bottom: 6, left: 8, zIndex: 2,
            fontSize: 9, fontWeight: 700, color: '#f5a623',
            background: 'rgba(245,166,35,0.15)', border: '1px solid rgba(245,166,35,0.3)',
            borderRadius: 3, padding: '1px 5px', letterSpacing: '0.04em',
          }}>ST</div>
        )}
      </div>

      {/* Info */}
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
          {item.weapon_type}
          {item.exterior ? ` · ${item.exterior}` : ''}
        </p>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <p style={{ fontSize: 9, color: 'var(--text-dim)', marginBottom: 1 }}>
              {best?.platform || 'BUFF'}
            </p>
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

export default function Home() {
  const navigate = useNavigate()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshResult, setRefreshResult] = useState(null)

  useEffect(() => { loadItems() }, [])

  async function loadItems() {
    setLoading(true)
    const data = await getItems(50)
    setItems(data || [])
    setLoading(false)
  }

  async function handleSeed() {
    setSeeding(true)
    await seedDatabase()
    setSeeding(false)
    loadItems()
  }

  async function handleRefresh() {
    setRefreshing(true)
    const res = await refreshPrices()
    setRefreshing(false)
    setRefreshResult(res)
    setTimeout(() => { loadItems(); setRefreshResult(null) }, 2500)
  }

  const noData = !loading && items.length === 0

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-page)' }}>

      {/* ── Hero ── */}
      <div style={{
        background: 'radial-gradient(ellipse 120% 80% at 50% -10%, rgba(74,142,245,0.12) 0%, transparent 60%)',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        paddingBottom: 40,
      }}>
        <div style={{ maxWidth: 900, margin: '0 auto', padding: '56px 20px 0', textAlign: 'center' }}>

          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'rgba(74,142,245,0.08)', border: '1px solid rgba(74,142,245,0.18)',
            borderRadius: 100, padding: '4px 14px', marginBottom: 22,
          }}>
            <span className="glow-pulse" style={{
              display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
              background: '#4a8ef5', boxShadow: '0 0 6px #4a8ef5',
            }} />
            <span style={{ fontSize: 11, color: '#4a8ef5', fontWeight: 500, letterSpacing: '0.04em' }}>
              实时数据 · AI 智能评分
            </span>
          </div>

          <h1 style={{
            fontSize: 'clamp(28px, 5vw, 48px)', fontWeight: 900,
            color: 'white', lineHeight: 1.1, letterSpacing: '-0.03em', marginBottom: 14,
          }}>
            CS2 饰品
            <span style={{
              background: 'linear-gradient(135deg, #4a8ef5, #8b5cf6)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}> 智能分析</span>
          </h1>
          <p style={{ fontSize: 15, color: 'var(--text-secondary)', marginBottom: 32 }}>
            AI 综合评分 · 价格趋势 · 多平台对比 · 投资参考
          </p>

          <div style={{ maxWidth: 580, margin: '0 auto' }}>
            <SearchBar />
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '32px 20px' }}>

        {/* Empty / seed state */}
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

        {/* Section header */}
        {(loading || items.length > 0) && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 3, height: 18, background: 'linear-gradient(180deg, #4a8ef5, #8b5cf6)', borderRadius: 2 }} />
              <span style={{ fontSize: 15, fontWeight: 700, color: 'white' }}>热门饰品</span>
              <span style={{ fontSize: 12, color: 'var(--text-dim)' }}>AI 评分排行</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {refreshResult && (
                <span style={{ fontSize: 11, color: '#22c55e' }}>✓ 已更新 {refreshResult.fetched} 个</span>
              )}
              <button onClick={handleRefresh} disabled={refreshing}
                style={{
                  fontSize: 11, color: '#4a8ef5',
                  background: 'rgba(74,142,245,0.08)', border: '1px solid rgba(74,142,245,0.18)',
                  borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
                  opacity: refreshing ? 0.5 : 1,
                }}>
                {refreshing ? '拉取中…' : '刷新价格'}
              </button>
              <button onClick={handleSeed} disabled={seeding}
                style={{
                  fontSize: 11, color: 'var(--text-dim)',
                  background: 'transparent', border: '1px solid rgba(255,255,255,0.07)',
                  borderRadius: 6, padding: '5px 12px', cursor: 'pointer',
                }}>
                {seeding ? '重置中…' : '重置数据'}
              </button>
            </div>
          </div>
        )}

        {/* Grid */}
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

        {/* Bottom feature strip */}
        {items.length > 0 && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 10, marginTop: 48,
            paddingTop: 32, borderTop: '1px solid rgba(255,255,255,0.05)',
          }}>
            {[
              {
                icon: '◎', label: 'AI 评分系统',
                desc: '价值 · 流动性 · 稳定性 · 趋势 四维评分',
                color: '#4a8ef5',
                path: items[0] ? `/item/${items[0].id}` : '/item/1',
              },
              {
                icon: '↗', label: '价格趋势',
                desc: '30 天历史走势与多平台均线对比',
                color: '#22c55e',
                path: items[0] ? `/item/${items[0].id}` : '/item/1',
              },
              {
                icon: '⇌', label: '租 vs 买',
                desc: '精确计算短期使用的最优方案',
                color: '#f5a623',
                path: '/rent-vs-buy',
              },
            ].map(f => (
              <div
                key={f.label}
                onClick={() => navigate(f.path)}
                style={{
                  background: '#0f1520', border: '1px solid rgba(255,255,255,0.06)',
                  borderRadius: 10, padding: '18px 16px', cursor: 'pointer',
                  transition: 'border-color 0.15s, transform 0.15s',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = `${f.color}30`
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.06)'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <span style={{ fontSize: 20, color: f.color, display: 'block', marginBottom: 10 }}>{f.icon}</span>
                <p style={{ fontWeight: 600, color: 'white', marginBottom: 4, fontSize: 13 }}>{f.label}</p>
                <p style={{ fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.5 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
