import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowsClockwise,
  Database,
  Cpu,
  CheckCircle,
  Flask,
  BookOpen,
} from "@phosphor-icons/react";
import {
  workspaceRequest,
  type RuntimeStatus,
  type Evaluation,
} from "../services/workspace";

export default function System() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null),
    [evaluating, setEvaluating] = useState(false);
  const [query, setQuery] = useState("如何判断饰品流动性？"),
    [searching, setSearching] = useState(false);
  const [search, setSearch] = useState<{
    results: { id: number; title: string; content: string; category: string }[];
    meta: { active_retrievers: string[] };
  } | null>(null);
  async function load() {
    setLoading(true);
    setError("");
    try {
      setStatus(await workspaceRequest<RuntimeStatus>("/workspace/status"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
  }, []);
  async function evaluate() {
    setEvaluating(true);
    setError("");
    try {
      setEvaluation(
        await workspaceRequest<Evaluation>("/workspace/evaluation", {
          method: "POST",
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEvaluating(false);
    }
  }
  async function retrieve(e: React.FormEvent) {
    e.preventDefault();
    setSearching(true);
    setError("");
    try {
      setSearch(
        await workspaceRequest("/rag/search", {
          method: "POST",
          body: JSON.stringify({ question: query, top_k: 3 }),
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSearching(false);
    }
  }
  return (
    <div className="page-shell system-page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">SYSTEM & EVIDENCE</span>
          <h1>每一条结论，都有来处。</h1>
          <p>检查模型连接、理解数据边界，验证研究过程是否可信。</p>
        </div>
        <button className="action-secondary" disabled={loading} onClick={load}>
          <ArrowsClockwise size={18} />
          {loading ? "检查中…" : "重新检查"}
        </button>
      </div>
      {error && (
        <p role="alert" className="notice notice-error">
          {error}
        </p>
      )}
      {!status && loading && <p role="status">正在检查工作区…</p>}
      {status && (
        <>
          <div className="system-grid">
            <section className="surface-card system-card">
              <div className="card-title">
                <Cpu size={22} />
                <h2>模型运行时</h2>
                <span
                  className={`source-badge ${status.model.health === "ready" ? "source-observed" : "source-demo"}`}
                >
                  {status.model.health === "ready" ? "服务在线" : "待连接"}
                </span>
              </div>
              <strong className="runtime-model">
                {status.model.model || "未配置模型"}
              </strong>
              <p>{status.model.detail}</p>
              <dl>
                <div>
                  <dt>提供方</dt>
                  <dd>{status.model.provider}</dd>
                </div>
                <div>
                  <dt>运行方式</dt>
                  <dd>
                    {status.model.provider === "ollama"
                      ? "本地推理 · 无按量费用"
                      : "服务器配置"}
                  </dd>
                </div>
              </dl>
              {status.model.health !== "ready" && (
                <details>
                  <summary>如何启动免费模型</summary>
                  <pre>ollama serve{"\n"}ollama pull qwen3:4b</pre>
                  <p>
                    后端设置
                    AI_PROVIDER=ollama。端口与模型名称须与后端配置一致。
                  </p>
                </details>
              )}
            </section>
            <section className="surface-card system-card">
              <div className="card-title">
                <Database size={22} />
                <h2>数据环境</h2>
                <span className="source-badge source-demo">
                  {status.data_mode === "mock" ? "MOCK" : "LIVE ADAPTERS"}
                </span>
              </div>
              <strong className="runtime-model">
                {status.catalog_count} 件饰品{" "}
                <small>
                  {" "}
                  / {status.snapshot_count.toLocaleString()} 条快照
                </small>
              </strong>
              <p>
                {status.data_mode === "mock"
                  ? "业务接口使用可重复的演示数据；Agent 调用真实本地模型。"
                  : "真实采集适配器已启用，每条快照仍需检查来源与时间。"}
              </p>
              <dl>
                <div>
                  <dt>行情 / 租赁</dt>
                  <dd>
                    {status.data_mode === "mock"
                      ? "演示 / 演示"
                      : "按快照标注 / 演示"}
                  </dd>
                </div>
                <div>
                  <dt>使用范围</dt>
                  <dd>单用户本地工作区</dd>
                </div>
              </dl>
              <p className="workspace-footnote">
                暂无账户隔离、交易执行或后台通知服务。
              </p>
            </section>
          </div>
          <section className="surface-card system-card">
            <div className="card-title">
              <CheckCircle size={22} />
              <h2>研究运行记录</h2>
              <span className="muted-copy">
                最近 {status.runs.sample_size} 次
              </span>
            </div>
            <div className="metric-strip">
              <div>
                <strong>{status.runs.completed}</strong>
                <span>完成</span>
              </div>
              <div>
                <strong>{status.runs.failed}</strong>
                <span>失败</span>
              </div>
              <div>
                <strong>{status.runs.validated_reports}</strong>
                <span>通过结构与引文校验</span>
              </div>
            </div>
            {status.recent_runs.length ? (
              <div className="run-table">
                {status.recent_runs.map((r) => (
                  <Link key={r.id} to={`/research/${r.session_id}`}>
                    <span>{r.question}</span>
                    <small>
                      {r.steps} 步 · {r.sources} 个来源
                    </small>
                    <b className={`run-status status-${r.status}`}>
                      {{
                        completed: "完成",
                        failed: "失败",
                        running: "运行中",
                        cancelled: "已停止",
                        interrupted: "已中断",
                      }[r.status] || r.status}
                    </b>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="muted-copy">
                还没有运行记录。完成一次研究后，这里会显示实际执行结果。
              </p>
            )}
          </section>
        </>
      )}
      <div className="system-grid">
        <section className="surface-card system-card">
          <div className="card-title">
            <BookOpen size={22} />
            <h2>知识检索检查</h2>
          </div>
          <p>查看实际检索原文。静态知识中的历史数字不代表当前行情。</p>
          <form className="knowledge-form" onSubmit={retrieve}>
            <label htmlFor="knowledge-query">研究问题</label>
            <input
              id="knowledge-query"
              required
              maxLength={2000}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              className="action-primary"
              disabled={searching || !query.trim()}
            >
              {searching ? "检索中…" : "检索证据"}
            </button>
          </form>
          {search && (
            <div aria-live="polite">
              <p className="workspace-footnote">
                实际检索通道：{search.meta.active_retrievers.join(" + ")}
              </p>
              {search.results.length ? (
                search.results.map((r) => (
                  <details className="knowledge-result" key={r.id}>
                    <summary>{r.title}</summary>
                    <p>{r.content}</p>
                  </details>
                ))
              ) : (
                <p>知识库没有覆盖这个问题。</p>
              )}
            </div>
          )}
        </section>
        <section className="surface-card system-card">
          <div className="card-title">
            <Flask size={22} />
            <h2>检索质量评估</h2>
          </div>
          <p>运行仓库中的 24 条中英文标注问题，检查当前检索器的 Top 3 结果。</p>
          <button
            className="action-secondary"
            disabled={evaluating}
            onClick={evaluate}
          >
            {evaluating ? "正在运行评估…" : "运行评估"}
          </button>
          {evaluation && (
            <div aria-live="polite">
              <div className="metric-strip">
                {(["recall", "mrr", "ndcg"] as const).map((key) => (
                  <div key={key}>
                    <strong>
                      {(evaluation.summary[key] * 100).toFixed(1)}%
                    </strong>
                    <span>{key.toUpperCase()}@3</span>
                  </div>
                ))}
              </div>
              <p className="workspace-footnote">
                {evaluation.summary.count} 条问题 · P95{" "}
                {evaluation.latency_ms.p95} ms ·{" "}
                {new Date(evaluation.executed_at).toLocaleTimeString("zh-CN")}
              </p>
              <p>{evaluation.note}</p>
              <details className="evaluation-cases">
                <summary>检查逐条结果</summary>
                {evaluation.cases.map((c) => (
                  <p key={c.id}>
                    {c.query}
                    <br />
                    <small>
                      召回率 {(c.metrics.recall * 100).toFixed(0)}% · 文档{" "}
                      {c.retrieved_ids.join(", ")}
                    </small>
                  </p>
                ))}
              </details>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
