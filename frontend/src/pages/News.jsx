import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Newspaper,
  ArrowsClockwise,
  ArrowUpRight,
} from "@phosphor-icons/react";
import { workspaceRequest } from "../services/workspace";
export default function News() {
  const [data, setData] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [query, setQuery] = useState(""),
    [note, setNote] = useState("");
  async function load(sync = false) {
    setBusy(true);
    setError("");
    try {
      if (sync) {
        const r = await workspaceRequest("/refresh-events", { method: "POST" });
        if (r.status === "error") throw new Error(r.message);
        setNote(r.message || `已同步 ${r.fetched} 条公告`);
      }
      setData(await workspaceRequest("/market/news"));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  const rows =
    data?.events?.filter((e) =>
      (e.title + e.summary).toLowerCase().includes(query.toLowerCase()),
    ) || [];
  return (
    <div className="page-shell">
      <div className="page-heading">
        <div>
          <span className="eyebrow">NEWS & CONTEXT</span>
          <h1>事件提供背景，证据支持判断。</h1>
          <p>保留来源和时间，区分已发生的事实与尚未验证的影响。</p>
        </div>
        <button
          className="action-secondary"
          disabled={busy}
          onClick={() => load(true)}
        >
          <ArrowsClockwise size={18} />
          {busy ? "更新中…" : "同步事件"}
        </button>
      </div>
      <div className="news-page-layout">
        <section>
          <label className="search-field">
            <span className="sr-only">搜索事件</span>
            <input
              placeholder="搜索标题或摘要…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          {error && (
            <p role="alert" className="notice notice-error">
              {error}
              <button onClick={() => load()}>重试</button>
            </p>
          )}
          {note && (
            <p role="status" className="notice">
              {note}
            </p>
          )}
          {!data && busy && (
            <p role="status" className="state-panel">
              正在载入事件…
            </p>
          )}
          {rows.map((event) => (
            <article className="surface-card event-article" key={event.id}>
              <div className="event-meta">
                <span
                  className={`source-badge ${event.data_kind === "demo" ? "source-demo" : "source-observed"}`}
                >
                  {event.data_kind === "demo" ? "演示事件" : "官方公告"}
                </span>
                <time>
                  {new Date(event.event_date).toLocaleDateString("zh-CN")}
                </time>
              </div>
              <h2>{event.title}</h2>
              <p>{event.summary}</p>
              <footer>
                <span>{event.source} · 影响待评估</span>
                {/^https:\/\//.test(event.source_url || "") && (
                  <a href={event.source_url} target="_blank" rel="noreferrer">
                    原文 <ArrowUpRight size={14} />
                  </a>
                )}
              </footer>
            </article>
          ))}
          {data && !rows.length && (
            <div className="surface-card state-panel">
              <Newspaper size={32} />
              <h2>暂无匹配事件</h2>
              <p>更换关键词，或同步来源后再试。</p>
            </div>
          )}
        </section>
        <aside className="surface-card news-guide">
          <span className="eyebrow">RESEARCH NOTE</span>
          <h2>看新闻之后，先问三个问题。</h2>
          <ol>
            <li>消息来自哪里，能否找到原文？</li>
            <li>是否直接涉及所研究的饰品？</li>
            <li>有没有真实成交与历史数据支持影响判断？</li>
          </ol>
          <Link className="action-primary" to="/research">
            带着问题开始研究
          </Link>
          <p>
            Mock 模式中的事件为明确标注的虚构场景，不会提供伪造的官方原文链接。
          </p>
        </aside>
      </div>
    </div>
  );
}
