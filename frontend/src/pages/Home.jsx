import { useState, useEffect, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  ArrowsClockwise,
  MagnifyingGlass,
  ChartLineUp,
  Lightning,
} from "@phosphor-icons/react";
import QuoteSource from "../components/QuoteSource";
import SearchBar from "../components/SearchBar";
import SkinImage from "../components/SkinImage";
import OpportunityPanel from "../components/OpportunityPanel";
import NewsPanel from "../components/NewsPanel";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import ErrorState from "../components/ui/ErrorState";
import {
  getItems,
  getOpportunities,
  getMarketSummary,
  getMarketEvents,
  seedDatabase,
  refreshPrices,
  refreshEvents,
  getMarketNews,
} from "../services/api";
import { formatCNY } from "../utils/formatters";
import { RARITY_COLOR } from "../utils/constants";

function ItemCard({ item, onClick }) {
  return (
    <button className="skin-card" onClick={onClick}>
      <div className="market-item-art">
        <span className="wear-tag">{item.exterior || "标准"}</span>
        {item.stattrak && <span className="st-tag">ST™</span>}
        <SkinImage iconUrl={item.icon_url} name={item.item_name} />
        <i
          className="rarity-line"
          style={{ background: RARITY_COLOR[item.rarity] || "var(--accent)" }}
        />
      </div>
      <div className="market-item-info">
        <h3 title={item.item_name}>{item.item_name?.replace(/ \([^)]*\)$/, "") || item.skin_name}</h3>
        <p>
          {item.weapon_type} <span>·</span> {item.rarity}
        </p>
        <div className="market-item-bottom">
          <strong className="price-display">
            {item.current_price != null ? formatCNY(item.current_price) : "—"}
          </strong>
          <span>{item.platform || "参考价"}</span>
        </div>
        <QuoteSource quote={item} compact />
        <div className="market-item-link">
          查看行情与分析 <ArrowRight size={12} />
        </div>
      </div>
    </button>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]),
    [opportunities, setOpp] = useState([]);
  const [news, setNews] = useState([]);
  const [newsFailed, setNewsFailed] = useState(false);
  const [newsLoading, setNewsLoading] = useState(false);
  const [opportunitiesFailed, setOpportunitiesFailed] = useState(false);
  const [eventsFailed, setEventsFailed] = useState(false);
  const [sourceFilter, setSourceFilter] = useState("all");
  const [actionNote, setActionNote] = useState("");
  const loadVersion = useRef(0);
  const [summary, setSummary] = useState(null),
    [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true),
    [loadError, setLoadError] = useState(false);
  const [busy, setBusy] = useState(""),
    [actionError, setActionError] = useState("");
  const [category, setCategory] = useState("all"),
    [exterior, setExterior] = useState("all"),
    [sort, setSort] = useState("default");
  const categories = useMemo(
    () => [...new Set(items.map((i) => i.weapon_type).filter(Boolean))],
    [items],
  );
  const exteriors = useMemo(
    () => [...new Set(items.map((i) => i.exterior).filter(Boolean))],
    [items],
  );
  const visible = useMemo(() => {
    const result = items.filter(
      (i) =>
        (category === "all" || i.weapon_type === category) &&
        (exterior === "all" || i.exterior === exterior) &&
        (sourceFilter === "all" || (sourceFilter === "legacy_unknown" ? !["observed", "demo"].includes(i.price_kind) : i.price_kind === sourceFilter)),
    );
    return sort === "default"
      ? result
      : [...result].sort((a, b) =>
          a.current_price == null
            ? b.current_price == null
              ? 0
              : 1
            : b.current_price == null
              ? -1
              : sort === "price-asc"
                ? a.current_price - b.current_price
                : b.current_price - a.current_price,
        );
  }, [items, category, exterior, sort, sourceFilter]);
  useEffect(() => {
    load();
    return () => { loadVersion.current++; };
  }, []);
  async function load(initial = true) {
    const version = ++loadVersion.current;
    if (initial) setLoading(true);
    const [data, opp, sum, evt, official] = await Promise.all([
      getItems(50),
      getOpportunities(8),
      getMarketSummary(),
      getMarketEvents(),
      getMarketNews(),
    ]);
    if (version !== loadVersion.current) return;
    setLoadError(data === null);
    setNewsFailed(official === null);
    if (data) setItems(data);
    setOpportunitiesFailed(opp === null);
    if (opp) setOpp(opp.opportunities || []);
    if (sum) setSummary(sum);
    setEventsFailed(evt === null);
    if (evt) setEvents(evt.events || []);
    if (official) setNews(official.events || []);
    setLoading(false);
  }
  async function reloadNews() {
    setNewsLoading(true);
    const official = await getMarketNews();
    setNewsFailed(official === null);
    if (official) setNews(official.events || []);
    setNewsLoading(false);
  }
  async function act(kind, fn) {
    setBusy(kind);
    setActionError("");
    setActionNote("");
    try {
      const result = await fn();
      if (!result || ["error", "busy", "partial"].includes(result.status)) {
        setActionError(!result ? '操作暂时失败，请检查连接后重试。' : result.message || `部分来源未更新：成功 ${result.fetched || 0}，失败 ${result.failed || 0}。`);
      } else {
        setActionNote(kind === 'seed' ? '示例数据已载入，报价已标注为演示数据。'
          : `已完成${kind === 'news' ? '新闻同步' : '价格刷新'}：${result.fetched ?? 0} 条，跳过 ${result.skipped ?? 0} 条。`);
      }
      if (kind === 'news') await reloadNews();
      else await load(false);
    } finally { setBusy(""); }
  }
  const research = () => navigate('/research');
  return (
    <div className="market-page">
      <div className="market-container">
        <div className="workspace-heading">
          <div><span className="eyebrow">COUNTER-STRIKE 2 / MARKET RESEARCH</span><h1>饰品市场</h1><p>浏览行情，核对来源，形成自己的判断。</p></div>
          <div className="workspace-search"><SearchBar /><button className="text-action" onClick={research}><BookOpen size={15} />打开研究助手 <ArrowRight size={14} /></button></div>
        </div>
        <div className="market-context"><div className="market-pulse">
          <span className="pulse-heading">
            <ChartLineUp size={17} />
            市场概览
          </span>
          <span>
            收录饰品 <b>{loading || (loadError && !items.length) ? "—" : items.length}</b>
          </span>
          <span>
            市场情绪 <b>{summary?.market_mood || "—"}</b>
          </span>
          <span>
            平均评分 <b>{summary?.avg_score ?? "—"}</b>
          </span>
          <span>
            活跃事件 <b>{loading || eventsFailed ? "—" : events.length}</b>
          </span>
          <small>研究原型 · 请核对报价来源与时间</small>
        </div>
        <NewsPanel news={news} loading={loading || newsLoading} failed={newsFailed} syncing={busy === 'news'} disabled={Boolean(busy) || newsLoading} onSync={() => act('news', refreshEvents)} onRetry={reloadNews} />
        </div>
        {loadError && (
          <ErrorState
            message="暂时无法载入市场数据，请稍后重试。"
            onRetry={() => load()}
          />
        )}
        {actionError && (
          <p role="alert" className="notice notice-error">
            {actionError}
          </p>
        )}
        {actionNote && <p role="status" className="notice notice-success">{actionNote}</p>}
        {!loading && !loadError && !items.length && (
          <EmptyState
            icon={MagnifyingGlass}
            title="还没有饰品数据"
            sub="载入示例数据，体验行情与研究功能。"
            action={
              <Button
                variant="primary"
                loading={busy === "seed"} disabled={Boolean(busy)}
                onClick={() => act("seed", seedDatabase)}
              >
                初始化示例数据
              </Button>
            }
          />
        )}
        <section id="market-catalog" className="catalog-section">
          <div className="catalog-tabs">
            <h2>全部饰品</h2>
            <span>{visible.length} 件饰品</span>
            <Button
              size="sm"
              variant="ghost"
              loading={busy === "prices"} disabled={Boolean(busy) || !items.length}
              onClick={() => act("prices", refreshPrices)}
            >
              <ArrowsClockwise size={14} />
              {busy === "prices" ? "正在刷新价格…" : "刷新价格"}
            </Button>
          </div>
          <div className="catalog-filters">
            <div className="filter-row">
              <span className="filter-label">类型</span>
              <div role="group" aria-label="饰品类型">
                {["all", ...categories].map((c) => (
                  <button
                    key={c}
                    onClick={() => setCategory(c)}
                    aria-pressed={category === c}
                    className={`filter-tab ${category === c ? "is-active" : ""}`}
                  >
                    {c === "all" ? "全部" : c}
                  </button>
                ))}
              </div>
            </div>
            <div className="filter-row">
              <span className="filter-label">外观</span>
              <div role="group" aria-label="饰品外观">
                {["all", ...exteriors].map((c) => (
                  <button
                    key={c}
                    onClick={() => setExterior(c)}
                    aria-pressed={exterior === c}
                    className={`filter-tab ${exterior === c ? "is-active" : ""}`}
                  >
                    {c === "all" ? "不限" : c}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="catalog-sort">
            <span>
              市场参考价格 <small>点击饰品查看数据与评分依据</small>
            </span>
            <div className="catalog-selects">
            <label>来源<select aria-label="报价来源" className="market-select" value={sourceFilter} onChange={e => setSourceFilter(e.target.value)}>
              <option value="all">全部来源</option><option value="observed">采集报价</option><option value="demo">演示数据</option><option value="legacy_unknown">来源未核验</option>
            </select></label>
            <label>
              排序{" "}
              <select
                aria-label="价格排序"
                className="market-select"
                value={sort}
                onChange={(e) => setSort(e.target.value)}
              >
                <option value="default">默认顺序</option>
                <option value="price-asc">价格从低到高</option>
                <option value="price-desc">价格从高到低</option>
              </select>
            </label></div>
          </div>
          <div className="market-grid" aria-busy={loading}>
            {loading
              ? Array.from({ length: 12 }, (_, i) => (
                  <div className="surface-card p-3" key={i}>
                    <Skeleton h={150} />
                    <Skeleton h={15} className="mt-4" />
                  </div>
                ))
              : visible.map((item) => (
                  <ItemCard
                    key={item.id}
                    item={item}
                    onClick={() => navigate(`/item/${item.id}`)}
                  />
                ))}
          </div>
          {!loading && items.length > 0 && !visible.length && (
            <div className="catalog-empty">
              没有符合条件的饰品。
              <button
                onClick={() => {
                  setCategory("all");
                  setExterior("all");
                  setSourceFilter("all");
                }}
              >
                清除筛选
              </button>
            </div>
          )}
        </section>
        {items.length > 0 && (
          <section className="market-opportunities">
            <div className="market-section-title">
              <h2>
                <Lightning size={19} weight="fill" />
                机会观察
              </h2>
              <span>规则信号 · 可能基于演示或未核验数据</span>
            </div>
            {opportunitiesFailed ? <ErrorState message="机会信号暂时无法载入" onRetry={() => load(false)} /> : <OpportunityPanel opportunities={opportunities} loading={loading} />}
          </section>
        )}
        {events.length > 0 && (
          <section className="market-events">
            <div className="market-section-title">
              <h2>市场事件</h2>
            </div>
            <div className="event-list">
              {events.slice(0, 6).map((e) => (
                <article key={e.id}>
                  <span>{e.timing_label}</span>
                  <strong>{e.title}</strong>
                  <small>
                    {e.impact_direction === "positive"
                      ? "正面信号"
                      : e.impact_direction === "negative"
                        ? "负面信号"
                        : "混合信号"}
                  </small>
                </article>
              ))}
            </div>
          </section>
        )}
        <div id="ask-sense-section" className="scroll-mt-24">
          <div className="surface-card p-5 flex flex-wrap items-center justify-between gap-4"><div><h2 className="font-semibold">让数据回答你的问题</h2><p className="muted-copy mt-1">带着目标进入研究工作台，核对报价、追踪证据并继续追问。</p></div><Button variant="primary" onClick={research}>打开研究工作台 <ArrowRight size={16} /></Button></div>
        </div>
        <footer className="market-footer">
          <strong>
            SenseSkin <span>AI</span>
          </strong>
          <span>CS2 饰品研究工具 · 规则评分不代表价格预测</span>
          <a
            href="https://github.com/yangkaiwen2002/sense-skin-ai"
            target="_blank"
            rel="noreferrer"
          >
            GitHub ↗
          </a>
        </footer>
      </div>
    </div>
  );
}
