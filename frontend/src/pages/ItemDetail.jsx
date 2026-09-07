import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { CaretRight } from '@phosphor-icons/react'
import TrendChart from '../components/TrendChart'
import AIChat from '../components/AIChat'
import RiskBadge from '../components/RiskBadge'
import { ScoreRing, CompactScoreBars, computeScores } from '../components/ui/Score'
import DecisionBadge from '../components/ui/Decision'
import Button from '../components/ui/Button'
import { CardHeader } from '../components/ui/Card'
import Skeleton from '../components/ui/Skeleton'
import ErrorState from '../components/ui/ErrorState'
import { getItemOverview, getItemHistory, getItemCompare, getItemEvents, getItemDecision } from '../services/api'
import DecisionPanel from '../components/DecisionPanel'
import { formatCNY } from '../utils/formatters'
import { RARITY_COLOR, WEAPON_ABBR } from '../utils/constants'
import PlatformComparisonTable from '../components/PlatformComparisonTable'
import EventTimeline from '../components/EventTimeline'

const PLATFORM_OPTIONS = ['BUFF', 'Steam', '悠悠有品', 'IGXE']

/* ── Big ambient skin display ── */
function SkinHeroImage({ weaponType, rarity, skinName, iconUrl }) {
  const abbr = WEAPON_ABBR[weaponType] || (weaponType?.[0] || '?')
  const c = RARITY_COLOR[rarity] || 'var(--accent)'

  return (
    <div className="w-full h-full min-h-[260px] sm:min-h-[340px] flex items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0" style={{ background: `radial-gradient(ellipse 70% 60% at 50% 55%, ${c}22 0%, transparent 70%)` }} />
      <div className="absolute inset-0" style={{ background: `radial-gradient(ellipse 40% 40% at 50% 55%, ${c}18 0%, transparent 60%)` }} />

      {iconUrl ? (
        <img
          src={iconUrl.startsWith('http') ? iconUrl : `https://community.fastly.steamstatic.com/economy/image/${iconUrl}/360fx360f`}
          alt={skinName}
          className="max-w-[82%] max-h-[200px] sm:max-h-[260px] object-contain relative z-[1]"
          style={{ filter: `drop-shadow(0 0 32px ${c}70) drop-shadow(0 4px 16px rgba(0,0,0,0.8))` }}
          onError={e => { e.target.style.display = 'none' }}
        />
      ) : (
        <div className="relative z-[1] text-center">
          <div
            className="font-mono font-black leading-none text-[72px] sm:text-[96px]"
            style={{ color: c, opacity: 0.55, filter: `drop-shadow(0 0 40px ${c}80)`, textShadow: `0 0 60px ${c}60` }}
          >
            {abbr}
          </div>
          {skinName && (
            <p className="text-xs text-white/25 mt-2.5 tracking-widest uppercase">{skinName}</p>
          )}
        </div>
      )}
    </div>
  )
}

function Tag({ children, color = 'rgba(255,255,255,0.1)', text = 'rgba(255,255,255,0.55)', border = 'rgba(255,255,255,0.12)' }) {
  return (
    <span
      className="text-[10px] font-semibold tracking-wide rounded px-2 py-0.5 border inline-block"
      style={{ color: text, background: color, borderColor: border }}
    >
      {children}
    </span>
  )
}

/* ── Platform price row ── */
function PlatformStrip({ platforms }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {platforms.map((p, i) => (
        <div
          key={p.platform}
          className="rounded-[var(--radius-sm)] border px-3.5 py-2 min-w-[108px]"
          style={{
            background: i === 0 ? 'var(--accent-soft)' : 'rgba(255,255,255,0.04)',
            borderColor: i === 0 ? 'var(--accent-border)' : 'var(--border-subtle)',
          }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[10px] font-medium" style={{ color: i === 0 ? 'var(--accent-strong)' : 'var(--text-dim)' }}>{p.platform}</span>
            {i === 0 && <span className="text-[9px] rounded px-1 py-px" style={{ color: 'var(--accent-strong)', background: 'var(--accent-soft)' }}>最优</span>}
          </div>
          <p className="price-display text-base">{p.current_price != null ? formatCNY(p.current_price) : '—'}</p>
          {p.return_7d != null && (
            <p className="text-[10px] mt-0.5 font-tabular" style={{ color: p.return_7d >= 0 ? 'var(--up)' : 'var(--down)' }}>
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
  const [decision, setDecision] = useState(null)
  const [decisionLoading, setDecisionLoading] = useState(true)
  const [platform, setPlatform] = useState('BUFF')
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { if (id) loadAll() }, [id])
  useEffect(() => { loadHistory() }, [id, platform, days])

  async function loadAll() {
    setLoading(true)
    setDecisionLoading(true)
    setError(null)
    const [ov, cmp, ev] = await Promise.all([
      getItemOverview(id),
      getItemCompare(id),
      getItemEvents(id, 60),
    ])
    if (!ov) { setError('饰品数据未找到'); setLoading(false); setDecisionLoading(false); return }
    setOverview(ov)
    setCompare(cmp)
    setEvents(Array.isArray(ev) ? ev : (ev?.events || []))
    setLoading(false)
    getItemDecision(id).then(d => { setDecision(d); setDecisionLoading(false) })
  }

  async function loadHistory() {
    const data = await getItemHistory(id, days, platform)
    setHistory(data?.history || data || [])
  }

  if (loading) return (
    <div className="flex justify-center items-center min-h-[60vh]">
      <div className="w-10 h-10 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--accent-border)', borderTopColor: 'var(--accent)' }} />
    </div>
  )

  if (error || !overview) return (
    <div className="max-w-lg mx-auto">
      <ErrorState message={error || '加载失败'} onRetry={() => navigate('/')} retryLabel="← 返回市场" />
    </div>
  )

  const platforms = overview.platforms || []
  const best = platforms[0]
  const scores = computeScores(platforms)
  const rc = RARITY_COLOR[overview.rarity] || 'var(--accent)'
  const displayName = overview.skin_name || overview.item_name
  const riskLabels = [...new Set(platforms.flatMap(p => p.risk_labels || []))]

  return (
    <div className="bg-[var(--bg-page)] min-h-screen">

      {/* ══════════════ HERO — decision-first primary analysis moment ══════════════ */}
      <div
        className="relative overflow-hidden border-b"
        style={{
          background: `radial-gradient(ellipse 55% 80% at 21% 50%, ${rc}10 0%, transparent 65%), linear-gradient(180deg, #0a0b0e 0%, #08090b 100%)`,
          borderColor: `${rc}20`,
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 relative">

          <div className="py-3.5 flex items-center gap-1.5 text-xs">
            <button onClick={() => navigate('/')} className="text-[var(--text-dim)] hover:text-[var(--text-secondary)] transition-colors">市场</button>
            <CaretRight size={11} className="text-[var(--text-dim)]" />
            <span className="text-[var(--text-secondary)] truncate">{displayName}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[38%_1fr] gap-0 items-center pb-8 sm:min-h-[380px]">

            <div className="sm:pr-5 pb-2 sm:pb-8">
              <SkinHeroImage weaponType={overview.weapon_type} rarity={overview.rarity} skinName={overview.skin_name} iconUrl={overview.icon_url} />
            </div>

            <div className="py-2 sm:py-8 sm:pl-2 flex flex-col gap-0">

              <div className="flex items-center gap-2 flex-wrap mb-2.5">
                {overview.rarity && <span className="text-[11px] font-bold tracking-wide uppercase" style={{ color: rc }}>{overview.rarity}</span>}
                {overview.weapon_type && <span className="text-[11px] text-[var(--text-dim)]">· {overview.weapon_type}</span>}
                {overview.exterior && <Tag color={`${rc}15`} text={rc} border={`${rc}30`}>{overview.exterior}</Tag>}
                {overview.stattrak && <Tag color="var(--gold-soft)" text="var(--gold)" border="var(--gold-border)">StatTrak™</Tag>}
              </div>

              <h1 className="font-extrabold text-white leading-tight tracking-tight mb-4" style={{ fontSize: 'clamp(22px, 3vw, 34px)' }}>
                {displayName}
              </h1>

              {/* PRICE + DECISION — the two co-equal focal points */}
              <div className="flex flex-wrap items-end gap-x-7 gap-y-3 mb-3.5">
                {best && (
                  <div>
                    <p className="text-[10px] text-[var(--text-dim)] mb-1.5 uppercase tracking-widest">{best.platform} · 最优价格</p>
                    <p className="price-display" style={{ fontSize: 'clamp(30px, 4vw, 46px)', lineHeight: 1 }}>{formatCNY(best.current_price)}</p>
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-[var(--text-dim)] mb-1.5 uppercase tracking-widest">AI 决策</p>
                  {decisionLoading ? (
                    <Skeleton w={84} h={30} radius={6} />
                  ) : decision ? (
                    <div className="flex items-center gap-2.5">
                      <DecisionBadge recommendation={decision.recommendation} size="lg" />
                      <span className="text-xs text-[var(--text-dim)] font-tabular">{Math.round(decision.confidence * 100)}% 置信</span>
                    </div>
                  ) : (
                    <span className="text-xs text-[var(--text-dim)]">暂无数据</span>
                  )}
                </div>
                {scores && <ScoreRing score={scores.overall} size={72} />}
              </div>

              <div className="flex items-center gap-2 flex-wrap mb-5">
                {best?.return_7d != null && (
                  <div
                    className="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1 border"
                    style={{
                      background: best.return_7d >= 0 ? 'var(--buy-soft)' : 'var(--avoid-soft)',
                      borderColor: best.return_7d >= 0 ? 'rgba(47,184,102,0.3)' : 'rgba(229,72,77,0.3)',
                    }}
                  >
                    <span className="text-sm font-extrabold font-tabular" style={{ color: best.return_7d >= 0 ? 'var(--up)' : 'var(--down)' }}>
                      {best.return_7d >= 0 ? '▲' : '▼'} {Math.abs(best.return_7d * 100).toFixed(2)}%
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)]">7日</span>
                  </div>
                )}
                {best?.avg_30d && <div className="text-xs text-[var(--text-secondary)] font-tabular">均价 {formatCNY(best.avg_30d)}</div>}
                {riskLabels.length > 0 && <RiskBadge labels={riskLabels} />}
              </div>

              {scores && (
                <div className="mb-5 max-w-[420px]">
                  <CompactScoreBars scores={scores} />
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => navigate(`/compare/${id}`)}>平台对比</Button>
                <Button variant="primary" onClick={() => navigate('/rent-vs-buy')}>租 vs 买</Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Platform strip */}
      {platforms.length > 0 && (
        <div className="border-b border-[var(--border-subtle)] bg-black/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <PlatformStrip platforms={platforms} />
          </div>
        </div>
      )}

      {/* ══════════════ PROGRESSIVE DISCLOSURE ══════════════
          price history → decision evidence (score dims + evidence chain +
          event signals) → item event history → market comparison → AI analyst
      ══════════════════════════════════════════════════════ */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-14">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5 items-start">

          {/* ── MAIN: analytical content ── */}
          <div className="flex flex-col gap-4 min-w-0">

            <div className="surface-card p-4 sm:p-5">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                <p className="text-sm font-semibold text-[var(--text-primary)]">价格走势</p>
                <div className="flex gap-1.5 flex-wrap">
                  {PLATFORM_OPTIONS.map(p => (
                    <button
                      key={p} onClick={() => setPlatform(p)}
                      className="text-[11px] px-2.5 py-1 rounded-[var(--radius-sm)] font-medium transition-colors"
                      style={{ background: platform === p ? 'var(--accent)' : 'rgba(255,255,255,0.05)', color: platform === p ? 'white' : 'var(--text-dim)' }}
                    >
                      {p}
                    </button>
                  ))}
                  <div className="w-px bg-[var(--border-default)] mx-1" />
                  {[7, 14, 30].map(d => (
                    <button
                      key={d} onClick={() => setDays(d)}
                      className="text-[11px] px-2 py-1 rounded-[var(--radius-sm)]"
                      style={{ background: days === d ? 'rgba(255,255,255,0.1)' : 'transparent', color: days === d ? 'white' : 'var(--text-dim)' }}
                    >
                      {d}天
                    </button>
                  ))}
                </div>
              </div>
              <TrendChart data={history} avg7d={platforms.find(p => p.platform === platform)?.avg_7d} avg30d={platforms.find(p => p.platform === platform)?.avg_30d} />
            </div>

            {/* Decision & evidence — the differentiator, full width, visible by default */}
            <DecisionPanel decision={decision} loading={decisionLoading} />

            {events.length > 0 && (
              <div className="surface-card p-4 sm:p-5">
                <CardHeader title="近期市场事件" sub="影响该饰品评分的历史与近期信号" />
                <EventTimeline events={events} />
              </div>
            )}
          </div>

          {/* ── SIDEBAR: market comparison + supportive AI analyst ── */}
          <div className="flex flex-col gap-4">
            {compare && (
              <div className="surface-card p-4 sm:p-5">
                <CardHeader title="平台价格对比" />
                <PlatformComparisonTable platforms={compare.platforms} />
              </div>
            )}

            <div>
              <p className="text-[11px] font-semibold text-[var(--text-dim)] uppercase tracking-wide mb-2 px-0.5">深度 AI 分析 · 辅助参考</p>
              <div className="surface-card overflow-hidden">
                <AIChat itemId={id} itemName={displayName} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
