import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BookOpen,
  ArrowsClockwise,
  MagnifyingGlass,
  ChartLineUp,
  Lightning,
} from "@phosphor-icons/react";
import SearchBar from "../components/SearchBar";
import SkinImage from "../components/SkinImage";
import OpportunityPanel from "../components/OpportunityPanel";
import AskSense from "../components/AskSense";
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
        <h3>{item.item_name?.replace(/ \([^)]*\)$/, "") || item.skin_name}</h3>
        <p>
          {item.weapon_type} <span>·</span> {item.rarity}
        </p>
        <div className="market-item-bottom">
          <strong className="price-display">
            {item.current_price != null ? formatCNY(item.current_price) : "—"}
          </strong>
          <span>{item.platform || "参考价"}</span>
        </div>
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
  const [summary, setSummary] = useState(null),
    [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true),
    [loadError, setLoadError] = useState(false);
  const [busy, setBusy] = useState(false),
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
        (exterior === "all" || i.exterior === exterior),
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
  }, [items, category, exterior, sort]);
  useEffect(() => {
    load();
  }, []);
  async function load() {
    setLoading(true);
    const [data, opp, sum, evt] = await Promise.all([
      getItems(50),
      getOpportunities(8),
      getMarketSummary(),
      getMarketEvents(),
    ]);
    setLoadError(data === null);
    setItems(data || []);
    setOpp(opp?.opportunities || []);
    setSummary(sum);
    setEvents(evt?.events || []);
    setLoading(false);
  }
  async function act(fn) {
    setBusy(true);
    setActionError("");
    const result = await fn();
    if (!result) setActionError("操作失败，请检查后端连接后重试。");
    await load();
    setBusy(false);
  }
  const research = () =>
    document
      .getElementById("ask-sense-section")
      ?.scrollIntoView({ behavior: "smooth" });
  return (
    <div className="market-page">
      <div className="market-container">
        <div className="market-page-heading">
          <div>
            <span className="game-label">CS2</span>
            <h1>饰品市场</h1>
            <span className="heading-caption">行情 · 发现 · 研究</span>
          </div>
          <div className="market-search">
            <SearchBar />
          </div>
        </div>
        <div className="market-banner-grid">
          <div className="market-banner">
            <div className="banner-copy">
              <span className="banner-eyebrow">SENSESKIN MARKET</span>
              <h2>好饰品，也要看懂行情。</h2>
              <p>价格趋势、平台比较、市场信号，一站查看。</p>
              <button
                onClick={() =>
                  document
                    .getElementById("market-catalog")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
              >
                探索饰品 <ArrowRight size={16} />
              </button>
            </div>
            <div className="banner-art" aria-hidden="true">
              {items[0] && (
                <SkinImage
                  iconUrl={items[0].icon_url}
                  name={items[0].item_name}
                />
              )}
              <span>COUNTER-STRIKE 2</span>
            </div>
          </div>
          <button
            className="research-promo"
            onClick={research}
            aria-label="打开研究助手"
          >
            <span className="research-promo-icon">
              <BookOpen size={26} />
            </span>
            <span className="promo-kicker">ASK SENSE</span>
            <strong>选饰品前，先问一问。</strong>
            <span>租还是买？如何判断流动性？</span>
            <b>
              打开研究助手 <ArrowRight size={14} />
            </b>
          </button>
        </div>
        <div className="market-pulse">
          <span className="pulse-heading">
            <ChartLineUp size={17} />
            市场概览
          </span>
          <span>
            收录饰品 <b>{loading ? "—" : items.length}</b>
          </span>
          <span>
            市场情绪 <b>{summary?.market_mood || "—"}</b>
          </span>
          <span>
            平均评分 <b>{summary?.avg_score ?? "—"}</b>
          </span>
          <span>
            活跃事件 <b>{events.length}</b>
          </span>
          <small>研究原型 · 含示例与估算数据</small>
        </div>
        {loadError && (
          <ErrorState
            message="暂时无法连接市场数据，请确认后端已启动后重试。"
            onRetry={load}
          />
        )}
        {actionError && (
          <p role="alert" className="text-[var(--avoid)] my-4">
            {actionError}
          </p>
        )}
        {!loading && !loadError && !items.length && (
          <EmptyState
            icon={MagnifyingGlass}
            title="还没有饰品数据"
            sub="载入示例数据，体验行情与研究功能。"
            action={
              <Button
                variant="primary"
                loading={busy}
                onClick={() => act(seedDatabase)}
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
              loading={busy}
              onClick={() => act(refreshPrices)}
            >
              <ArrowsClockwise size={14} />
              刷新价格
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
            </label>
          </div>
          <div className="market-grid">
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
              <span>规则信号 · 查看支持与反对依据</span>
            </div>
            <OpportunityPanel opportunities={opportunities} loading={loading} />
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
          <AskSense />
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
