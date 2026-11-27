import { useState } from "react";
import { Bell } from "@phosphor-icons/react";
import {
  readRules,
  saveRule,
  evaluateRule,
  type WatchRule,
} from "../utils/alerts";
export default function WatchRuleEditor({
  id,
  quote,
}: {
  id: number;
  quote?: { current_price?: number; price_kind?: string; is_stale?: boolean };
}) {
  const [rule, setRule] = useState<WatchRule | undefined>(
      () => readRules()[id],
    ),
    [editing, setEditing] = useState(false);
  const [target, setTarget] = useState(rule?.target.toString() || ""),
    [note, setNote] = useState(rule?.note || ""),
    [direction, setDirection] = useState<"below" | "above">(
      rule?.direction || "below",
    ),
    [error, setError] = useState(""),
    [message, setMessage] = useState("");
  const result = rule ? evaluateRule(rule, quote) : null;
  function persist(next: WatchRule | null) {
    try {
      saveRule(id, next);
      setRule(next || undefined);
      setEditing(false);
      setError("");
      setMessage(next ? "监控条件已保存。" : "监控条件已移除。");
    } catch {
      setError("保存失败，请检查价格输入或浏览器存储权限。");
    }
  }
  return (
    <section className="watch-rule">
      <div className="watch-rule-heading">
        <Bell size={16} />
        <strong>目标价监控</strong>
        <button onClick={() => setEditing(!editing)}>
          {editing ? "收起" : rule ? "编辑" : "设置"}
        </button>
      </div>
      {result && (
        <p className={`rule-${result.state}`} role="status">
          {result.label} · {rule?.direction === "below" ? "≤" : "≥"} ¥
          {rule?.target.toLocaleString()}
        </p>
      )}
      {rule?.note && !editing && <p className="rule-note">{rule.note}</p>}
      {editing && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            persist({
              target: Number(target),
              direction,
              note,
              enabled: rule?.enabled ?? true,
            });
          }}
        >
          <div>
            <label>
              触发条件
              <select
                value={direction}
                onChange={(e) =>
                  setDirection(e.target.value as "below" | "above")
                }
              >
                <option value="below">价格低于或等于</option>
                <option value="above">价格高于或等于</option>
              </select>
            </label>
            <label>
              目标价格（元）
              <input
                type="number"
                required
                min="0.01"
                max="1000000000"
                step="0.01"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              />
            </label>
          </div>
          <label>
            研究备注
            <textarea
              rows={2}
              maxLength={300}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="例如：等待更多平台报价再判断"
            />
          </label>
          <div className="rule-buttons">
            <button className="action-primary" type="submit">
              保存条件
            </button>
            {rule && (
              <button type="button" onClick={() => persist(null)}>
                移除条件
              </button>
            )}
          </div>
        </form>
      )}
      {rule && !editing && (
        <button
          className="text-action"
          onClick={() => persist({ ...rule, enabled: !rule.enabled })}
        >
          {rule.enabled ? "暂停监控" : "恢复监控"}
        </button>
      )}
      {error && (
        <p role="alert" className="text-[var(--avoid)]">
          {error}
        </p>
      )}
      {message && (
        <span className="sr-only" role="status">
          {message}
        </span>
      )}
    </section>
  );
}
