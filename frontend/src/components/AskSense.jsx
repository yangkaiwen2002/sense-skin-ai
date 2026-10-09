import { useEffect, useState, useRef } from "react";
import {
  BookOpen,
  PaperPlaneRight,
  ArrowUpRight,
  MagnifyingGlass,
  X,
  CaretDown,
} from "@phosphor-icons/react";
import { BASE_URL } from "../services/api";
import { consumeSSE } from "../utils/sse";
import Button from "./ui/Button";
import Skeleton from "./ui/Skeleton";

const SUGGESTED = [
  "刀应该租还是买？",
  "如何评估皮肤的流动性？",
  "StatTrak 为什么有溢价？",
];
const CATEGORY_LABEL = {
  rent_vs_buy: "租买决策",
  tournament_effects: "赛事影响",
  price_factors: "价格因素",
  rarity_guide: "品相与稀有度",
  specific_skins: "饰品研究",
  skin_investment: "风险与策略",
  market_mechanics: "市场机制",
  platform_comparison: "交易平台",
};

function SourceCard({ source, index }) {
  return (
    <details className="evidence-source group">
      <summary className="flex items-center gap-3 cursor-pointer list-none p-4">
        <span className="source-number">
          {String(index + 1).padStart(2, "0")}
        </span>
        <span className="flex-1 min-w-0">
          <span className="block text-[10px] text-[var(--text-secondary)] mb-1">
            {CATEGORY_LABEL[source.category] || source.category}
          </span>
          <span className="text-[13px] font-semibold">{source.title}</span>
        </span>
        <CaretDown
          size={16}
          className="shrink-0 transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="px-4 pb-4 text-[13px] leading-7 text-[var(--text-secondary)] border-t border-[var(--border-subtle)] pt-3">
        {source.content || "此来源暂无可显示的原文。"}
      </div>
    </details>
  );
}

export default function AskSense() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [searched, setSearched] = useState(false);
  const abortRef = useRef(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  async function submit(q, searchOnly = false) {
    const text = (q ?? question).trim();
    if (!text) return;
    if (q) setQuestion(q);
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setAnswer("");
    setSources([]);
    setError("");
    setNotice("");
    setSearched(false);
    setLoading(true);
    try {
      const res = await fetch(
        `${BASE_URL}/rag/${searchOnly ? "search" : "query"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: text, top_k: 3 }),
          signal: ctrl.signal,
        },
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : `请求失败 (${res.status})`,
        );
      }
      if (searchOnly) {
        const data = await res.json();
        if (ctrl.signal.aborted) return;
        setSources(data.results);
        setSearched(true);
        setNotice(
          "已找到相关知识片段。展开来源可阅读原文，也可以选择「综合回答」。",
        );
      } else {
        await consumeSSE(res.body, (evt) => {
          if (ctrl.signal.aborted) return;
          if (evt.type === "sources") {
            setSources(evt.sources);
            setSearched(true);
          } else if (evt.type === "text") setAnswer((a) => a + evt.text);
          else if (evt.type === "notice") setNotice(evt.text);
          else if (evt.type === "error") setError(evt.error);
        });
      }
    } catch (e) {
      if (!ctrl.signal.aborted) setError(e.message || "连接失败，请稍后重试");
    } finally {
      if (abortRef.current === ctrl) setLoading(false);
    }
  }

  function clear() {
    abortRef.current?.abort();
    setLoading(false);
    setAnswer("");
    setSources([]);
    setQuestion("");
    setError("");
    setNotice("");
    setSearched(false);
  }

  return (
    <section className="research-workspace" aria-labelledby="ask-sense-title">
      <div className="research-intro">
        <BookOpen
          size={25}
          weight="duotone"
          className="text-[var(--accent-strong)] mb-5"
        />
        <p className="text-xs tracking-[0.16em] text-[var(--text-secondary)] mb-3">
          ASK SENSE
        </p>
        <h2
          id="ask-sense-title"
          className="text-2xl font-semibold tracking-tight leading-snug"
        >
          每一个判断，
          <br />
          都应该有依据。
        </h2>
        <p className="text-[13px] leading-7 text-[var(--text-secondary)] mt-4">
          从知识库寻找线索，展开原文核对，再用 AI 整理思路。
        </p>
        <div className="mt-7 space-y-2">
          {SUGGESTED.map((s) => (
            <button
              key={s}
              onClick={() => submit(s, true)}
              className="research-suggestion"
            >
              <span>{s}</span>
              <ArrowUpRight size={14} />
            </button>
          ))}
        </div>
        <p className="mt-6 text-[11px] leading-5 text-[var(--text-secondary)]">
          知识库是静态参考资料，其中的价格和费率不代表当前行情。
        </p>
      </div>
      <div className="research-main" aria-busy={loading}>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <label
            htmlFor="research-question"
            className="block text-sm font-semibold mb-3"
          >
            你想了解什么？
          </label>
          <textarea
            id="research-question"
            value={question}
            maxLength={2000}
            rows={3}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="例如：长期用一把刀，租赁和购买的成本怎么比较？"
            className="research-input"
          />
          <div className="flex flex-wrap justify-between gap-3 items-center mt-3">
            <span className="text-[11px] text-[var(--text-secondary)]">
              {question.length} / 2000
            </span>
            <div className="flex gap-2">
              {loading ? (
                <Button
                  type="button"
                  onClick={() => {
                    abortRef.current?.abort();
                    setLoading(false);
                  }}
                >
                  <X size={14} />
                  停止
                </Button>
              ) : (
                <>
                  <Button
                    type="button"
                    onClick={() => submit(undefined, true)}
                    disabled={!question.trim()}
                  >
                    <MagnifyingGlass size={14} />
                    查找来源
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={!question.trim()}
                  >
                    <PaperPlaneRight size={14} />
                    综合回答
                  </Button>
                </>
              )}
            </div>
          </div>
        </form>
        {error && (
          <p role="alert" className="mt-5 text-sm text-[var(--avoid)]">
            {error}
          </p>
        )}
        {notice && (
          <p
            role="status"
            className="mt-5 text-xs leading-6 text-[var(--text-secondary)]"
          >
            {notice}
          </p>
        )}
        {searched && sources.length === 0 && (
          <p className="py-6 text-sm text-[var(--text-secondary)]">
            未找到相关来源。试试具体的饰品名称，或更换关键词。
          </p>
        )}
        {sources.length > 0 && (
          <div className="mt-6">
            <div className="flex justify-between text-xs text-[var(--text-secondary)] mb-3">
              <span>参考来源 · {sources.length}</span>
              <span>点击展开原文</span>
            </div>
            <div className="space-y-2">
              {sources.map((s, i) => (
                <SourceCard key={s.id} source={s} index={i} />
              ))}
            </div>
          </div>
        )}
        {answer && (
          <div className="mt-6 pt-5 border-t border-[var(--border-default)]">
            <p className="text-xs font-semibold text-[var(--accent-strong)] mb-3">
              综合回答
            </p>
            <p className="text-sm leading-8 whitespace-pre-wrap">{answer}</p>
          </div>
        )}
        {loading && !answer && (
          <div className="mt-6 space-y-3" role="status" aria-label="正在查询">
            <Skeleton h={12} />
            <Skeleton w="78%" h={12} />
          </div>
        )}
        {(searched || answer || error) && !loading && (
          <button
            onClick={clear}
            className="text-xs text-[var(--text-secondary)] mt-5 hover:text-[var(--accent)]"
          >
            清空本次研究
          </button>
        )}
        {!searched && !loading && !error && (
          <div className="research-empty">
            <BookOpen size={28} weight="light" />
            <p>先找到来源，再形成判断。</p>
            <span>无需配置 AI 密钥，也可以使用知识检索。</span>
          </div>
        )}
      </div>
    </section>
  );
}
