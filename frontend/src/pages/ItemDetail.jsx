import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import TrendChart from '../components/TrendChart'
import AIChat from '../components/AIChat'
import RiskBadge from '../components/RiskBadge'
import { ScoreRing, CompactScoreBars, computeScores } from '../components/ScorePanel'
import { getItemOverview, getItemHistory, getItemCompare, getItemEvents } from '../services/api'
import { formatCNY } from '../utils/formatters'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import EventTimeline from '../components/EventTimeline'

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
const PLATFORM_OPTIONS = ['BUFF', 'Steam', '悠悠有品', 'IGXE']

/* ── Big ambient skin display ── */
function SkinHeroImage({ weaponType, rarity, skinName, iconUrl }) {
  const abbr = WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')
  const c = RARITY_COLOR[rarity] || '#4a8ef5'

  return (
    <div style={{
      width: '100%', height: '100%', minHeight: 340,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* layered glow rings */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse 70% 60% at 50% 55%, ${c}22 0%, transparent 70%)`,
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        background: `radial-gradient(ellipse 40% 40% at 50% 55%, ${c}18 0%, transparent 60%)`,
      }} />

      {iconUrl ? (
        <img
          src={iconUrl.startsWith('http') ? iconUrl : `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`}
          alt={skinName}
          style={{
            maxWidth: '82%', maxHeight: 260, objectFit: 'contain',
            position: 'relative', zIndex: 1,
            filter: `drop-shadow(0 0 32px ${c}70) drop-shadow(0 4px 16px rgba(0,0,0,0.8))`,
          }}
          onError={e => { e.target.style.display = 'none' }}
        />
      ) : (
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <div style={{
            fontSize: 96, fontWeight: 900, color: c, opacity: 0.55,
            fontFamily: 'monospace', lineHeight: 1,
            filter: `drop-shadow(0 0 40px ${c}80)`,
            textShadow: `0 0 60px ${c}60`,
          }}>{abbr}</div>
          {skinName && (
            <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.25)', marginTop: 10, letterSpacing: '0.12em', textTransform: 'uppercase' }}>
              {skinName}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

/* ── Tag pill ── */
function Tag({ children, color = 'rgba(255,255,255,0.1)', text = 'rgba(255,255,255,0.55)', border = 'rgba(255,255,255,0.12)' }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 600, letterSpacing: '0.05em',
      color: text, background: color, border: `1px solid ${border}`,
      borderRadius: 4, padding: '3px 8px', display: 'inline-block',
    }}>{children}</span>
  )
}

/* ── Platform price row ── */
function PlatformStrip({ platforms }) {
  return (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      {platforms.map((p, i) => (
        <div key={p.platform} style={{
          background: i === 0 ? 'rgba(74,142,245,0.08)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${i === 0 ? 'rgba(74,142,245,0.2)' : 'rgba(255,255,255,0.07)'}`,
          borderRadius: 8, padding: '8px 14px', minWidth: 110,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 4 }}>
            <span style={{ fontSize: 10, color: i === 0 ? '#4a8ef5' : 'var(--text-dim)', fontWeight: 500 }}>
              {p.platform}
            </span>
            {i === 0 && (
              <span style={{ fontSize: 9, color: '#4a8ef5', background: 'rgba(74,142,245,0.15)', borderRadius: 3, padding: '1px 4px' }}>最优</span>
            )}
          </div>
          <p className="price-display" style={{ fontSize: 16 }}>
            {p.current_price != null ? formatCNY(p.current_price) : '—'}
          </p>
          {p.return_7d != null && (
            <p style={{ fontSize: 10, color: p.return_7d >= 0 ? '#22c55e' : '#ef4444', marginTop: 2 }}>
              {p.return_7d >= 0 ? '+' : ''}{(p.return_7d * 100).toFixed(1)}%
            </p>
          )}
        </div>
      ))}
    </div>
  )
}

export default function ItemDetail() {
  const { itemId } = useParams()
  const navigate = useNavigate()
  const id = Number(itemId)

  const [overview, setOverview] = useState(null)
  const [history, setHistory] = useState([])
  const [compare, setCompare] = useState(null)
  const [events, setEvents] = useState([])
  const [platform, setPlatform] = useState('BUFF')
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { if (id) loadAll() }, [id])
  useEffect(() => { loadHistory() }, [id, platform, days])

  async function loadAll() {
    setLoading(true)
    setError(null)
    const [ov, cmp, ev] = await Promise.all([
      getItemOverview(id),
      getItemCompare(id),
      getItemEvents(id, 60),
    ])
    if (!ov) { setError('饰品数据未找到'); setLoading(false); return }
    setOverview(ov)
    setCompare(cmp)
    setEvents(Array.isArray(ev) ? ev : (ev?.events || []))
    setLoading(false)
  }

  async function loadHistory() {
    const data = await getItemHistory(id, days, platform)
    setHistory(data?.history || data || [])
  }

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
      <div style={{
        width: 40, height: 40, borderRadius: '50%',
        border: '2px solid rgba(74,142,245,0.15)',
        borderTopColor: '#4a8ef5',
        animation: 'spin 0.8s linear infinite',
      }} />
    </div>
  )

  if (error || !overview) return (
    <div style={{ textAlign: 'center', padding: '80px 16px' }}>
      <p style={{ color: '#ef4444', marginBottom: 16 }}>{error || '加载失败'}</p>
      <button onClick={() => navigate('/')} style={{ color: '#4a8ef5', background: 'none', border: 'none', cursor: 'pointer' }}>
        ← 返回
      </button>
    </div>
  )

  const platforms = overview.platforms || []
  const best = platforms[0]
  const scores = computeScores(platforms)
  const rc = RARITY_COLOR[overview.rarity] || '#4a8ef5'
  const displayName = overview.skin_name || overview.item_name
  const riskLabels = [...new Set(platforms.flatMap(p => p.risk_labels || []))]

  return (
    <div style={{ background: 'var(--bg-page)', minHeight: '100vh' }}>

      {/* ════════════════════════════════════════════════
          HERO — full-width immersive section
          Left 42%: big skin image with ambient glow
          Right 58%: name / price / score / tags / bars
      ════════════════════════════════════════════════ */}
      <div style={{
        position: 'relative', overflow: 'hidden',
        background: `
          radial-gradient(ellipse 55% 80% at 21% 50%, ${rc}10 0%, transparent 65%),
          linear-gradient(180deg, #090d18 0%, #080c14 100%)
        `,
        borderBottom: `1px solid ${rc}20`,
      }}>
        {/* very subtle mesh overlay */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.015) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }} />

        <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', position: 'relative' }}>

          {/* Breadcrumb */}
          <div style={{ padding: '16px 0', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)', padding: 0 }}>
              市场
            </button>
            <span style={{ color: 'var(--text-dim)' }}>/</span>
            <span style={{ color: 'var(--text-secondary)' }}>{displayName}</span>
          </div>

          {/* Two-column hero */}
          <div style={{ display: 'grid', gridTemplateColumns: '42% 1fr', gap: 0, minHeight: 380, alignItems: 'center' }}>

            {/* ── LEFT: skin image ── */}
            <div style={{ paddingRight: 20, paddingBottom: 32 }}>
              <SkinHeroImage
                weaponType={overview.weapon_type}
                rarity={overview.rarity}
                skinName={overview.skin_name}
                iconUrl={overview.icon_url}
              />
            </div>

            {/* ── RIGHT: info stack ── */}
            <div style={{ padding: '32px 0 40px 8px', display: 'flex', flexDirection: 'column', gap: 0 }}>

              {/* Layer 1: rarity + weapon */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                {overview.rarity && (
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: rc, letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}>{overview.rarity}</span>
                )}
                {overview.weapon_type && (
                  <span style={{ fontSize: 11, color: 'var(--text-dim)' }}>· {overview.weapon_type}</span>
                )}
                {overview.exterior && (
                  <Tag color={`${rc}15`} text={rc} border={`${rc}30`}>{overview.exterior}</Tag>
                )}
                {overview.stattrak && (
                  <Tag color="rgba(245,166,35,0.12)" text="#f5a623" border="rgba(245,166,35,0.28)">StatTrak™</Tag>
                )}
              </div>

              {/* Layer 1: name */}
              <h1 style={{
                fontSize: 'clamp(22px, 3vw, 36px)', fontWeight: 900,
                color: 'white', lineHeight: 1.1, letterSpacing: '-0.02em',
                marginBottom: 4,
              }}>
                {displayName}
              </h1>
              {overview.skin_name && (
                <p style={{ fontSize: 12, color: 'var(--text-dim)', marginBottom: 24 }}>
                  {overview.item_name}
                </p>
              )}

              {/* Layer 1: PRICE + SCORE (the stars of the page) */}
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 28, marginBottom: 18 }}>
                {best && (
                  <div>
                    <p style={{
                      fontSize: 10, color: 'var(--text-dim)', marginBottom: 6,
                      textTransform: 'uppercase', letterSpacing: '0.1em',
                    }}>
                      {best.platform} · 最优价格
                    </p>
                    <p className="price-display" style={{ fontSize: 'clamp(32px, 4vw, 50px)', lineHeight: 1 }}>
                      {formatCNY(best.current_price)}
                    </p>
                  </div>
                )}
                <ScoreRing score={scores?.overall} size={100} />
              </div>

              {/* Layer 2: return badge + risk */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 22, flexWrap: 'wrap' }}>
                {best?.return_7d != null && (
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                    padding: '5px 12px', borderRadius: 6,
                    background: best.return_7d >= 0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
                    border: `1px solid ${best.return_7d >= 0 ? 'rgba(34,197,94,0.25)' : 'rgba(239,68,68,0.25)'}`,
                  }}>
                    <span style={{ fontSize: 14, fontWeight: 800, color: best.return_7d >= 0 ? '#22c55e' : '#ef4444' }}>
                      {best.return_7d >= 0 ? '▲' : '▼'} {Math.abs(best.return_7d * 100).toFixed(2)}%
                    </span>
                    <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>7日</span>
                  </div>
                )}
                {best?.avg_30d && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    均价 {formatCNY(best.avg_30d)}
                  </div>
                )}
                {riskLabels.length > 0 && <RiskBadge labels={riskLabels} />}
              </div>

              {/* Layer 3: compact 4-score bars */}
              {scores && (
                <div style={{ marginBottom: 24, maxWidth: 420 }}>
                  <CompactScoreBars scores={scores} />
                </div>
              )}

              {/* Actions */}
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => navigate(`/compare/${id}`)}
                  style={{
                    padding: '8px 18px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
                    borderRadius: 7, color: 'var(--text-primary)', transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
                >
                  平台对比
                </button>
                <button
                  onClick={() => navigate('/rent-vs-buy')}
                  style={{
                    padding: '8px 18px', fontSize: 12, fontWeight: 600, cursor: 'pointer',
                    background: 'rgba(74,142,245,0.12)', border: '1px solid rgba(74,142,245,0.3)',
                    borderRadius: 7, color: '#4a8ef5', transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(74,142,245,0.2)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(74,142,245,0.12)'}
                >
                  租 vs 买
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════
          PLATFORM STRIP — below hero
      ════════════════════════════════════════════════ */}
      {platforms.length > 0 && (
        <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
          <div style={{ maxWidth: 1280, margin: '0 auto', padding: '16px 24px' }}>
            <PlatformStrip platforms={platforms} />
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════
          BODY — chart left, AI chat right
      ════════════════════════════════════════════════ */}
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '24px 24px 48px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 20, alignItems: 'start' }}>

          {/* ── LEFT column ── */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Trend chart */}
            <div style={{
              background: '#0f1520', border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 12, padding: 20,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>价格走势</p>
                <div style={{ display: 'flex', gap: 6 }}>
                  {PLATFORM_OPTIONS.map(p => (
                    <button key={p} onClick={() => setPlatform(p)} style={{
                      fontSize: 11, padding: '3px 9px', borderRadius: 4, border: 'none', cursor: 'pointer',
                      background: platform === p ? '#4a8ef5' : 'rgba(255,255,255,0.05)',
                      color: platform === p ? 'white' : 'var(--text-dim)',
                      fontWeight: platform === p ? 600 : 400,
                    }}>{p}</button>
                  ))}
                  <div style={{ width: 1, background: 'rgba(255,255,255,0.08)', margin: '0 4px' }} />
                  {[7, 14, 30].map(d => (
                    <button key={d} onClick={() => setDays(d)} style={{
                      fontSize: 11, padding: '3px 7px', borderRadius: 4, border: 'none', cursor: 'pointer',
                      background: days === d ? 'rgba(255,255,255,0.1)' : 'transparent',
                      color: days === d ? 'white' : 'var(--text-dim)',
                    }}>{d}天</button>
                  ))}
                </div>
              </div>
              <TrendChart
                data={history}
                avg7d={platforms.find(p => p.platform === platform)?.avg_7d}
                avg30d={platforms.find(p => p.platform === platform)?.avg_30d}
              />
            </div>

            {/* Platform compare table */}
            {compare && (
              <div style={{
                background: '#0f1520', border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: 12, padding: 20,
              }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
                  平台价格对比
                </p>
                <PlatformComparisonTable platforms={compare.platforms} />
              </div>
            )}

            {/* Events */}
            {events.length > 0 && (
              <div style={{
                background: '#0f1520', border: '1px solid rgba(255,255,255,0.07)',
                borderRadius: 12, padding: 20,
              }}>
                <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 14 }}>
                  近期市场事件
                </p>
                <EventTimeline events={events} />
              </div>
            )}
          </div>

          {/* ── RIGHT: AI chat ── */}
          <div style={{ position: 'sticky', top: 16 }}>
            <div style={{
              background: '#0f1520', border: '1px solid rgba(255,255,255,0.07)',
              borderRadius: 12, overflow: 'hidden',
            }}>
              <AIChat itemId={id} itemName={displayName} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
