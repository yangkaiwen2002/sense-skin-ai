/**
 * DecisionPanel — Evidence-based trading recommendation UI.
 *
 * Displays the full output of the decision engine:
 *   BUY / WATCH / HOLD / AVOID badge
 *   Confidence bar
 *   Rationale sentence
 *   Upside factors & risk factors
 *   Supporting signals (evidence log)
 *   Event context
 *   Evidence sources
 *   7-dimension subscore bar chart
 */

import { useState } from "react";

const REC_STYLES = {
  BUY:   { bg: "bg-green-500/15",  border: "border-green-500/40",  text: "text-green-400",  badge: "bg-green-500" },
  WATCH: { bg: "bg-blue-500/15",   border: "border-blue-500/40",   text: "text-blue-400",   badge: "bg-blue-500" },
  HOLD:  { bg: "bg-amber-500/15",  border: "border-amber-500/40",  text: "text-amber-400",  badge: "bg-amber-500" },
  AVOID: { bg: "bg-red-500/15",    border: "border-red-500/40",    text: "text-red-400",    badge: "bg-red-500" },
};

const SIGNAL_ICONS = { "+": "▲", "-": "▼", "=": "◆" };
const SIGNAL_COLORS = {
  "+": "text-green-400",
  "-": "text-red-400",
  "=": "text-zinc-400",
};

const SUBSCORE_LABELS = {
  rarity:    "稀有度",
  exterior:  "外观品相",
  liquidity: "流动性",
  trend:     "7日趋势",
  valuation: "估值空间",
  demand:    "市场需求",
  event:     "事件信号",
};

function ScoreBar({ label, value }) {
  const color =
    value >= 70 ? "bg-green-500" :
    value >= 50 ? "bg-blue-500"  :
    value >= 35 ? "bg-amber-500" :
    "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-zinc-400 w-16 shrink-0 text-right">{label}</span>
      <div className="flex-1 bg-zinc-800 rounded-full h-1.5">
        <div
          className={`${color} h-1.5 rounded-full transition-all duration-500`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="text-xs text-zinc-300 w-7 text-right">{value}</span>
    </div>
  );
}

export default function DecisionPanel({ decision, loading }) {
  const [showSignals, setShowSignals] = useState(false);
  const [showEvents, setShowEvents]   = useState(false);

  if (loading) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 space-y-3 animate-pulse">
        <div className="h-5 bg-zinc-800 rounded w-1/3" />
        <div className="h-10 bg-zinc-800 rounded" />
        <div className="h-4 bg-zinc-800 rounded w-2/3" />
        <div className="h-4 bg-zinc-800 rounded w-1/2" />
      </div>
    );
  }

  if (!decision) return null;

  const style = REC_STYLES[decision.recommendation] || REC_STYLES.HOLD;
  const conf  = Math.round(decision.confidence * 100);
  const ss    = decision.score_summary || {};

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-5 space-y-4`}>

      {/* Header — badge + total score */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`${style.badge} text-white text-sm font-bold px-3 py-1 rounded-full`}>
            {decision.recommendation_cn}
          </span>
          <span className={`text-xs font-medium ${style.text}`}>
            {decision.recommendation}
          </span>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-white">{ss.total ?? "—"}</div>
          <div className="text-xs text-zinc-500">综合评分</div>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-zinc-400">
          <span>决策置信度</span>
          <span className={style.text}>{conf}%</span>
        </div>
        <div className="bg-zinc-800 rounded-full h-2">
          <div
            className={`${style.badge} h-2 rounded-full transition-all duration-700`}
            style={{ width: `${conf}%` }}
          />
        </div>
      </div>

      {/* Rationale */}
      <p className="text-sm text-zinc-200 leading-relaxed border-l-2 border-zinc-600 pl-3">
        {decision.rationale}
      </p>

      {/* Valuation label + net signal */}
      <div className="flex gap-4 text-xs">
        <span className="text-zinc-500">估值：
          <span className={
            ss.valuation_label === "低估" ? "text-green-400" :
            ss.valuation_label === "高估" ? "text-red-400" :
            "text-zinc-300"
          }> {ss.valuation_label}</span>
        </span>
        <span className="text-zinc-500">信号净值：
          <span className={ss.net_signal >= 0 ? "text-green-400" : "text-red-400"}>
            {ss.net_signal >= 0 ? "+" : ""}{ss.net_signal}
          </span>
        </span>
      </div>

      {/* Upside / Risk columns */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs font-semibold text-green-400 mb-1.5">做多因素</div>
          {decision.upside_factors?.length ? (
            decision.upside_factors.slice(0, 3).map((u, i) => (
              <div key={i} className="flex items-start gap-1.5 mb-1">
                <span className="text-green-500 text-xs mt-0.5 shrink-0">✓</span>
                <span className="text-xs text-zinc-300 leading-snug">{u}</span>
              </div>
            ))
          ) : (
            <span className="text-xs text-zinc-500">暂无</span>
          )}
        </div>
        <div>
          <div className="text-xs font-semibold text-red-400 mb-1.5">风险因素</div>
          {decision.risk_factors?.length ? (
            decision.risk_factors.slice(0, 3).map((r, i) => (
              <div key={i} className="flex items-start gap-1.5 mb-1">
                <span className="text-red-500 text-xs mt-0.5 shrink-0">✗</span>
                <span className="text-xs text-zinc-300 leading-snug">{r}</span>
              </div>
            ))
          ) : (
            <span className="text-xs text-zinc-500">暂无</span>
          )}
        </div>
      </div>

      {/* 7-dimension subscores */}
      {ss.total && (
        <div className="space-y-1.5 pt-1 border-t border-zinc-800">
          <div className="text-xs font-semibold text-zinc-400 mb-2">7维度评分</div>
          {Object.entries(SUBSCORE_LABELS).map(([key, label]) =>
            ss[key] !== undefined ? (
              <ScoreBar key={key} label={label} value={ss[key]} />
            ) : null
          )}
        </div>
      )}

      {/* Evidence log (collapsible) */}
      {decision.supporting_signals?.length > 0 && (
        <div className="border-t border-zinc-800 pt-3">
          <button
            onClick={() => setShowSignals(v => !v)}
            className="flex items-center justify-between w-full text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <span>决策证据链 ({decision.supporting_signals.length} 条信号)</span>
            <span>{showSignals ? "▲" : "▼"}</span>
          </button>
          {showSignals && (
            <div className="mt-2 space-y-1.5">
              {decision.supporting_signals.map((sig, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span className={`text-xs font-bold shrink-0 ${SIGNAL_COLORS[sig.direction]}`}>
                    {SIGNAL_ICONS[sig.direction]}
                  </span>
                  <div>
                    <span className="text-xs font-medium text-zinc-300">{sig.label}</span>
                    {sig.points > 0 && (
                      <span className={`ml-1.5 text-xs ${SIGNAL_COLORS[sig.direction]}`}>
                        {sig.direction === "+" ? "+" : "-"}{sig.points}pt
                      </span>
                    )}
                    <p className="text-xs text-zinc-500 leading-snug mt-0.5">{sig.note}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Event context (collapsible) */}
      {decision.event_context?.length > 0 && (
        <div className="border-t border-zinc-800 pt-3">
          <button
            onClick={() => setShowEvents(v => !v)}
            className="flex items-center justify-between w-full text-xs font-semibold text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            <span>市场事件 ({decision.event_context.length} 个)</span>
            <span>{showEvents ? "▲" : "▼"}</span>
          </button>
          {showEvents && (
            <div className="mt-2 space-y-2">
              {decision.event_context.map((e, i) => (
                <div key={i} className="bg-zinc-800/50 rounded-lg p-2.5 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-zinc-200">{e.title}</span>
                    <span className={`text-xs font-bold ${
                      e.impact === "positive" ? "text-green-400" :
                      e.impact === "negative" ? "text-red-400" :
                      "text-zinc-400"
                    }`}>
                      {e.impact === "positive" ? "▲" : e.impact === "negative" ? "▼" : "◆"}
                      {" "}{Math.round(e.strength * 100)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <span>{e.window_label}</span>
                    <span>·</span>
                    <span>{e.event_type}</span>
                    <span>·</span>
                    <span>相关性 {Math.round(e.relevance * 100)}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Evidence sources */}
      {decision.evidence_sources?.length > 0 && (
        <div className="border-t border-zinc-800 pt-2">
          <div className="text-xs text-zinc-600">
            数据来源：{decision.evidence_sources.join(" · ")}
          </div>
        </div>
      )}
    </div>
  );
}
