import QuoteSource from "../components/QuoteSource";
import useWatchlist from "../hooks/useWatchlist";
import ResearchBrief from "../components/ResearchBrief";
import SkinImage from "../components/SkinImage";
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { CaretRight } from "@phosphor-icons/react";
import TrendChart from "../components/TrendChart";
import RiskBadge from "../components/RiskBadge";
import { ScoreRing } from "../components/ui/Score";
import DecisionBadge from "../components/ui/Decision";
import Button from "../components/ui/Button";
import { CardHeader } from "../components/ui/Card";
import Skeleton from "../components/ui/Skeleton";
import ErrorState from "../components/ui/ErrorState";
import EmptyState from "../components/ui/EmptyState";
import {
  getItemOverview,
  getItemHistory,
  getItemCompare,
  getItemEvents,
  getItemDecision,
} from "../services/api";
import DecisionPanel from "../components/DecisionPanel";
import { formatCNY } from "../utils/formatters";
import { RARITY_COLOR } from "../utils/constants";
import PlatformComparisonTable from "../components/PlatformComparisonTable";
import EventTimeline from "../components/EventTimeline";


/* ── Big ambient skin display ── */
function Tag({
  children,
  color = "var(--bg-surface-raised)",
  text = "var(--text-secondary)",
  border = "var(--border-default)",
}) {
  return (
    <span
      className="text-[10px] font-semibold tracking-wide rounded px-2 py-0.5 border inline-block"
      style={{ color: text, background: color, borderColor: border }}
    >
      {children}
    </span>
  );
}

/* ── Platform price row ── */
function PlatformStrip({ platforms, bestPlatform }) {
  return <div className="platform-strip">{platforms.map(p => <div key={p.platform} className={`platform-quote ${p.platform === bestPlatform ? 'is-best' : ''}`}>
    <div className="flex items-center justify-between gap-2 mb-2"><span className="text-xs font-semibold">{p.platform}</span>
      {p.platform === bestPlatform && <span className="source-badge source-observed">最低参考价</span>}</div>
    <p className="price-display text-xl">{formatCNY(p.current_price)}</p>
    {p.return_7d != null && <p className="text-xs font-tabular mt-1" style={{ color: p.return_7d >= 0 ? 'var(--up)' : 'var(--down)' }}>
      {p.return_7d >= 0 ? '+' : ''}{(p.return_7d * 100).toFixed(2)}% <span className="text-[var(--text-dim)]">/ 7日</span></p>}
    <QuoteSource quote={p} />
  </div>)}</div>;
}

export default function ItemDetail() {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const id = Number(itemId);
  const { ids: saved, toggle: toggleSaved, error: saveError } = useWatchlist();

  const [overview, setOverview] = useState(null);
  const [history, setHistory] = useState([]);
  const [compare, setCompare] = useState(null);
  const [events, setEvents] = useState([]);
  const [decision, setDecision] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(true);
  const [platform, setPlatform] = useState("BUFF");
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reload, setReload] = useState(0);
  const [historyReload, setHistoryReload] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyFailed, setHistoryFailed] = useState(false);
  const [eventsFailed, setEventsFailed] = useState(false);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setDecisionLoading(true);
    setDecision(null);
    setError(null);
    Promise.all([getItemOverview(id), getItemCompare(id), getItemEvents(id, 60), getItemDecision(id)])
      .then(([ov, cmp, ev, result]) => {
        if (ignore) return;
        if (!ov) setError("饰品数据未找到");
        setOverview(ov);
        setCompare(cmp);
        setEventsFailed(ev == null);
        setEvents(Array.isArray(ev) ? ev : ev?.events || []);
        setDecision(result);
        if (ov?.platforms?.length && !ov.platforms.some(p => p.platform === platform)) {
          setPlatform(ov.platforms[0].platform);
        }
        setLoading(false);
        setDecisionLoading(false);
      });
    return () => { ignore = true; };
  }, [id, reload]);

  useEffect(() => {
    let ignore = false;
    setHistory([]);
    setHistoryLoading(true);
    setHistoryFailed(false);
    getItemHistory(id, days, platform).then(data => {
      if (!ignore) {
        setHistory(data?.history || data || []);
        setHistoryFailed(data == null);
        setHistoryLoading(false);
      }
    });
    return () => { ignore = true; };
  }, [id, platform, days, historyReload]);

  if (loading) return <div className="page-shell space-y-5" role="status" aria-label="正在载入饰品研究">
    <Skeleton w="35%" h={20} /><Skeleton h={280} /><Skeleton h={160} /><Skeleton h={300} />
  </div>;

  if (error || !overview)
    return (
      <div className="max-w-lg mx-auto">
        <ErrorState
          message={error || "加载失败"}
          onRetry={() => setReload(n => n + 1)}
        />
      </div>
    );

  const platforms = overview.platforms || [];
  const best = platforms.find(p => p.current_price > 0);
  const scores = decision?.score_summary;
  const rc = RARITY_COLOR[overview.rarity] || "var(--accent)";
  const displayName = overview.item_name || overview.skin_name;
  const riskLabels = [
    ...new Set(platforms.flatMap((p) => p.risk_labels || [])),
  ];

  return (
    <div className="bg-[var(--bg-page)] min-h-screen">
      {/* ══════════════ HERO — decision-first primary analysis moment ══════════════ */}
      <div
        className="relative overflow-hidden border-b"
        style={{
          background: "var(--bg-surface)",
          borderColor: `${rc}20`,
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 relative">
          <div className="py-3.5 flex items-center gap-1.5 text-xs">
            <button
              onClick={() => navigate("/")}
              className="text-[var(--text-dim)] hover:text-[var(--text-secondary)] transition-colors"
            >
              市场
            </button>
            <CaretRight size={11} className="text-[var(--text-dim)]" />
            <span className="text-[var(--text-secondary)] truncate">
              {displayName}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-[30%_1fr] gap-0 items-center pb-5 sm:min-h-[280px]">
            <div className="sm:pr-5 pb-2 sm:pb-4">
              <SkinImage
                iconUrl={overview.icon_url}
                name={overview.item_name}
                className="detail-skin-art"
              />
            </div>

            <div className="py-2 sm:py-4 sm:pl-2 flex flex-col gap-0">
              <div className="flex items-center gap-2 flex-wrap mb-2.5">
                {overview.rarity && (
                  <span
                    className="text-[11px] font-bold tracking-wide uppercase"
                    style={{ color: rc }}
                  >
                    {overview.rarity}
                  </span>
                )}
                {overview.weapon_type && (
                  <span className="text-[11px] text-[var(--text-dim)]">
                    · {overview.weapon_type}
                  </span>
                )}
                {overview.exterior && (
                  <Tag color={`${rc}15`} text={rc} border={`${rc}30`}>
                    {overview.exterior}
                  </Tag>
                )}
                {overview.stattrak && (
                  <Tag
                    color="var(--gold-soft)"
                    text="var(--gold)"
                    border="var(--gold-border)"
                  >
                    StatTrak™
                  </Tag>
                )}
              </div>

              <h1
                className="font-extrabold text-[var(--text-primary)] leading-tight tracking-tight mb-4"
                style={{ fontSize: "clamp(22px, 3vw, 34px)" }}
              >
                {displayName}
              </h1>

              {/* PRICE + DECISION — the two co-equal focal points */}
              <div className="flex flex-wrap items-end gap-x-7 gap-y-3 mb-3.5">
                {best && (
                  <div>
                    <p className="text-[10px] text-[var(--text-dim)] mb-1.5 uppercase tracking-widest">
                      {best.platform} · {best.is_stale ? '历史参考价' : '优先参考价'}
                    </p>
                    <p
                      className="price-display"
                      style={{
                        fontSize: "clamp(30px, 4vw, 46px)",
                        lineHeight: 1,
                      }}
                    >
                      {formatCNY(best.current_price)}
                    </p>
                    <QuoteSource quote={best} />
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-[var(--text-dim)] mb-1.5 uppercase tracking-widest">
                    规则信号
                  </p>
                  {decisionLoading ? (
                    <Skeleton w={84} h={30} radius={6} />
                  ) : decision ? (
                    <div className="flex items-center gap-2.5">
                      <DecisionBadge
                        recommendation={decision.recommendation}
                        size="lg"
                      />
                      <span className="text-xs text-[var(--text-dim)] font-tabular">
                        {Math.round(decision.confidence * 100)}% 信号强度
                      </span>
                    </div>
                  ) : (
                    <span className="text-xs text-[var(--text-dim)]">
                      暂无数据
                    </span>
                  )}
                </div>
                {scores && <ScoreRing score={scores.total} size={72} />}
              </div>

              <div className="flex items-center gap-2 flex-wrap mb-5">
                {best?.return_7d != null && (
                  <div
                    className="inline-flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1 border"
                    style={{
                      background:
                        best.return_7d >= 0
                          ? "var(--buy-soft)"
                          : "var(--avoid-soft)",
                      borderColor:
                        best.return_7d >= 0
                          ? "rgba(47,184,102,0.3)"
                          : "rgba(229,72,77,0.3)",
                    }}
                  >
                    <span
                      className="text-sm font-extrabold font-tabular"
                      style={{
                        color:
                          best.return_7d >= 0 ? "var(--up)" : "var(--down)",
                      }}
                    >
                      {best.return_7d >= 0 ? "▲" : "▼"}{" "}
                      {Math.abs(best.return_7d * 100).toFixed(2)}%
                    </span>
                    <span className="text-[10px] text-[var(--text-dim)]">
                      7日
                    </span>
                  </div>
                )}
                {best?.avg_30d && (
                  <div className="text-xs text-[var(--text-secondary)] font-tabular">
                    30日均价 {formatCNY(best.avg_30d)}
                  </div>
                )}
                {riskLabels.length > 0 && <RiskBadge labels={riskLabels} />}
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button variant="primary" onClick={() => navigate(`/research?item=${id}`)}>用 AI 继续研究</Button>
                <Button
                  onClick={() => toggleSaved(id)}
                  aria-pressed={saved.includes(id)}
                >
                  {saved.includes(id) ? "★ 已加入自选" : "☆ 加入自选"}
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => navigate(`/compare/${id}`)}
                >
                  平台对比
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => navigate(`/rent-vs-buy?item=${id}`)}
                >
                  租 vs 买
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {saveError && (
        <p role="alert" className="market-container py-3 text-[var(--avoid)]">
          {saveError}
        </p>
      )}
      {/* Platform strip */}
      {platforms.length > 0 && (
        <div className="border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
            <PlatformStrip platforms={platforms} bestPlatform={compare?.best_platform} />
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 pb-14">
        <nav className="section-jumps" aria-label="研究内容导航">
          <a href="#research">研究简报</a><a href="#history">价格走势</a><a href="#comparison">平台报价</a><a href="#signals">信号依据</a><a href="#events">市场事件</a>
        </nav>
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_340px] gap-5 items-start">
          <div className="flex flex-col gap-5 min-w-0">
            <div id="research" className="analysis-section"><ResearchBrief overview={overview} decision={decision} loading={decisionLoading} /></div>
            <section id="history" className="surface-card p-4 sm:p-5 analysis-section">
              <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                <h2 className="text-base font-semibold">价格走势</h2>
                <div className="flex gap-1 flex-wrap" aria-label="走势筛选">
                  {platforms.map(p => <button key={p.platform} onClick={() => setPlatform(p.platform)} aria-pressed={platform === p.platform}
                    className={`filter-tab ${platform === p.platform ? 'is-active' : ''}`}>{p.platform}</button>)}
                  <span className="w-px bg-[var(--border-default)] mx-1" />
                  {[7, 14, 30].map(d => <button key={d} onClick={() => setDays(d)} aria-pressed={days === d}
                    className={`filter-tab ${days === d ? 'is-active' : ''}`}>{d}天</button>)}
                </div>
              </div>
              <div className="mb-4"><p className="muted-copy">{platform} · 最近 {days} 天的已有快照</p><QuoteSource quote={platforms.find(p => p.platform === platform)} /></div>
              {historyLoading ? <div role="status" aria-label="正在载入走势"><Skeleton h={260} /></div> : historyFailed ?
                <ErrorState message="价格走势加载失败" onRetry={() => setHistoryReload(n => n + 1)} /> :
                <TrendChart data={history} avg7d={platforms.find(p => p.platform === platform)?.avg_7d} avg30d={platforms.find(p => p.platform === platform)?.avg_30d} />}
            </section>
            <section id="comparison" className="surface-card p-4 sm:p-5 analysis-section">
              <CardHeader title="平台报价" sub="核对来源、采集时间与费用后，再比较价格。" />
              {compare ? <PlatformComparisonTable platforms={compare.platforms} /> : <ErrorState message="平台报价加载失败" onRetry={() => setReload(n => n + 1)} />}
              <Button variant="ghost" className="mt-3" onClick={() => navigate(`/compare/${id}`)}>打开完整平台对比 →</Button>
            </section>
            <section id="events" className="surface-card p-4 sm:p-5 analysis-section">
              <details>
                <summary className="cursor-pointer text-sm font-semibold">市场事件与官方公告 <span className="text-[var(--text-dim)] font-normal">· {events.length} 条</span></summary>
                <p className="muted-copy mt-2 mb-4">官方公告为全局市场背景，对本饰品的价格影响仍待评估。</p>
                {eventsFailed ? <ErrorState message="市场事件加载失败" onRetry={() => setReload(n => n + 1)} /> : <EventTimeline events={events} compact />}
              </details>
            </section>
          </div>
          <aside className="analysis-sidebar min-w-0">
            <section id="signals" className="analysis-section">
              <h2 className="text-sm font-semibold mb-3">规则信号与依据</h2>
              {decision ? <DecisionPanel decision={decision} loading={decisionLoading} /> : !platforms.some(p => p.current_price > 0 && !p.is_stale) ? <EmptyState title="暂无可用研究信号" sub="报价已过期或数据不足，更新行情后再查看研究。" /> : <ErrorState message="研究信号暂时无法载入" onRetry={() => setReload(n => n + 1)} />}
            </section>
            <section><h2 className="text-sm font-semibold mb-3">AI 研究助手 <span className="text-xs font-normal text-[var(--text-dim)]">· 辅助参考</span></h2>
              <div className="surface-card p-5"><p className="muted-copy mb-4">带着当前饰品继续提问，核对最新数据、查看执行过程，并保存带来源的研究记录。</p><Button variant="primary" className="w-full" onClick={() => navigate(`/research?item=${id}`)}>开始研究 {displayName}</Button></div>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}
