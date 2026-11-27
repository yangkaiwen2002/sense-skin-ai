import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Archive,
  ArrowCounterClockwise,
  MagnifyingGlass,
  Plus,
  PencilSimple,
  Books,
} from "@phosphor-icons/react";
import { workspaceRequest, type Session } from "../services/workspace";

export default function Library() {
  const [rows, setRows] = useState<Session[]>([]),
    [query, setQuery] = useState(""),
    [archived, setArchived] = useState(false);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(""),
    [notice, setNotice] = useState("");
  const [editing, setEditing] = useState(""),
    [title, setTitle] = useState(""),
    [reload, setReload] = useState(0);
  useEffect(() => {
    const ctrl = new AbortController();
    setLoading(true);
    setError("");
    workspaceRequest<{ sessions: Session[] }>(
      `/research/sessions?archived=${archived}`,
      { signal: ctrl.signal },
    )
      .then((data) => setRows(data.sessions))
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [archived, reload]);
  async function update(row: Session, patch: Partial<Session>) {
    setBusy(row.id);
    setError("");
    setNotice("");
    try {
      const updated = await workspaceRequest<Session>(
        `/research/sessions/${row.id}`,
        { method: "PATCH", body: JSON.stringify(patch) },
      );
      setRows((old) =>
        old
          .map((r) => (r.id === updated.id ? updated : r))
          .filter((r) => r.archived === archived),
      );
      setEditing("");
      setNotice(
        patch.title
          ? "研究标题已保存。"
          : patch.archived
            ? "已归档，可在归档记录中恢复。"
            : "已恢复到研究库。",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  const visible = rows.filter((r) =>
    r.title.toLocaleLowerCase().includes(query.toLocaleLowerCase()),
  );
  return (
    <div className="page-shell library-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">RESEARCH LIBRARY</span>
          <h1>把每一次判断，留下依据。</h1>
          <p>恢复上下文、继续研究，随时回看当时的数据与结论。</p>
        </div>
        <Link className="action-primary" to="/research">
          <Plus size={18} />
          新建研究
        </Link>
      </div>
      <div className="workspace-toolbar">
        <div className="segmented">
          <button
            aria-pressed={!archived}
            onClick={() => {
              setArchived(false);
              setEditing("");
            }}
          >
            研究记录
          </button>
          <button
            aria-pressed={archived}
            onClick={() => {
              setArchived(true);
              setEditing("");
            }}
          >
            已归档
          </button>
        </div>
        <label className="search-field">
          <MagnifyingGlass size={18} />
          <span className="sr-only">搜索研究标题</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索研究标题…"
          />
        </label>
      </div>
      {error && (
        <p role="alert" className="notice notice-error">
          {error}
          <button onClick={() => setReload((n) => n + 1)}>重新加载</button>
        </p>
      )}
      {notice && (
        <p role="status" className="notice">
          {notice}
        </p>
      )}
      {loading ? (
        <div role="status" className="surface-card state-panel">
          正在读取研究记录…
        </div>
      ) : visible.length ? (
        <div className="library-list">
          {visible.map((row) => (
            <article className="library-row" key={row.id}>
              <span className="library-icon">
                <Books size={23} />
              </span>
              <div className="library-content">
                {editing === row.id ? (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      update(row, { title: title.trim() });
                    }}
                  >
                    <label className="sr-only" htmlFor="session-title">
                      研究标题
                    </label>
                    <input
                      id="session-title"
                      value={title}
                      maxLength={160}
                      required
                      onChange={(e) => setTitle(e.target.value)}
                    />
                    <button
                      disabled={!!busy || !title.trim()}
                      className="action-secondary"
                    >
                      保存
                    </button>
                    <button type="button" onClick={() => setEditing("")}>
                      取消
                    </button>
                  </form>
                ) : (
                  <>
                    <Link to={`/research/${row.id}`}>
                      <h2>{row.title}</h2>
                    </Link>
                    <p>
                      {new Date(row.updated_at).toLocaleString("zh-CN", {
                        hour12: false,
                      })}{" "}
                      ·{" "}
                      {row.item_ids.length
                        ? `${row.item_ids.length} 件饰品`
                        : "知识研究"}{" "}
                      · {row.active_run_id ? "运行中" : "已保存"}
                    </p>
                  </>
                )}
              </div>
              <div className="library-actions">
                <button
                  aria-label={`重命名：${row.title}`}
                  disabled={!!busy || !!row.active_run_id}
                  onClick={() => {
                    setEditing(row.id);
                    setTitle(row.title);
                  }}
                >
                  <PencilSimple size={18} />
                </button>
                <button
                  disabled={!!busy || !!row.active_run_id}
                  aria-label={`${archived ? "恢复" : "归档"}：${row.title}`}
                  onClick={() => update(row, { archived: !archived })}
                >
                  {archived ? (
                    <ArrowCounterClockwise size={18} />
                  ) : (
                    <Archive size={18} />
                  )}
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="surface-card state-panel">
          <Books size={32} />
          <h2>
            {query
              ? "没有匹配的研究"
              : archived
                ? "暂无归档记录"
                : "从一个具体问题开始"}
          </h2>
          <p>
            {query
              ? "试试其他关键词。"
              : "在 AI 研究中完成的每一轮，都会保留证据、执行过程与报告。"}
          </p>
          <Link to="/research" className="action-secondary">
            开始研究
          </Link>
        </div>
      )}
      <p className="workspace-footnote">
        单用户本地工作区 · 最近 50 条记录 ·
        报告可在研究详情内导出。归档不会删除研究内容。
      </p>
    </div>
  );
}
