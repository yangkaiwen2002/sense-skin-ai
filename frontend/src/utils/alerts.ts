export interface WatchRule {
  target: number;
  direction: "below" | "above";
  note: string;
  enabled: boolean;
}
export type RuleMap = Record<string, WatchRule>;
const KEY = "senseskin.watch-rules.v1";
export function readRules(
  storage: Pick<Storage, "getItem"> = localStorage,
): RuleMap {
  try {
    const raw = JSON.parse(storage.getItem(KEY) || "{}");
    if (!raw || Array.isArray(raw) || typeof raw !== "object") return {};
    return Object.fromEntries(
      Object.entries(raw).filter(([, v]) => {
        const r = v as WatchRule;
        return (
          r &&
          Number.isFinite(r.target) &&
          r.target > 0 &&
          ["below", "above"].includes(r.direction) &&
          typeof r.enabled === "boolean" &&
          typeof r.note === "string" &&
          r.note.length <= 300
        );
      }),
    ) as RuleMap;
  } catch {
    return {};
  }
}
export function saveRule(
  id: number,
  rule: WatchRule | null,
  storage: Pick<Storage, "getItem" | "setItem"> = localStorage,
) {
  const rules = readRules(storage);
  if (rule) {
    if (
      !Number.isFinite(rule.target) ||
      rule.target <= 0 ||
      rule.target > 1e9 ||
      rule.note.length > 300
    )
      throw new Error("请输入有效目标价格，备注不超过 300 字。");
    rules[id] = rule;
  } else delete rules[id];
  storage.setItem(KEY, JSON.stringify(rules));
  return rules;
}
export function evaluateRule(
  rule: WatchRule,
  quote?: { current_price?: number; price_kind?: string; is_stale?: boolean },
) {
  if (!rule.enabled) return { state: "paused", label: "已暂停" };
  if (
    !quote ||
    !Number.isFinite(quote.current_price) ||
    !quote.current_price ||
    quote.is_stale
  )
    return { state: "unknown", label: "缺少有效报价，暂不判断" };
  if (quote.price_kind !== "observed" && quote.price_kind !== "demo")
    return { state: "unknown", label: "来源未核验，暂不判断" };
  const match =
    rule.direction === "below"
      ? quote.current_price <= rule.target
      : quote.current_price >= rule.target;
  return {
    state: match ? "matched" : "waiting",
    label: `${quote.price_kind === "demo" ? "演示检查 · " : ""}${match ? "已达到目标" : "尚未达到目标"}`,
  };
}
