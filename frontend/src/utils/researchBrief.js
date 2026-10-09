const labels = { BUY: "偏多", WATCH: "关注", HOLD: "中性", AVOID: "偏谨慎" };
const finite = (x) => typeof x === "number" && Number.isFinite(x);
const money = (x) => `¥${x.toFixed(2)}`;

// Deterministic synthesis of the loaded context. No model calls or invented facts.
export function buildResearchBrief(overview, decision) {
  const prices = (overview?.platforms || [])
    .filter((p) => finite(p.current_price) && p.current_price > 0)
    .sort((a, b) => a.current_price - b.current_price);
  const low = prices[0],
    high = prices.at(-1);
  const facts = [];
  if (low)
    facts.push(
      `已载入平台中，${low.platform} 参考价最低：${money(low.current_price)}。`,
    );
  if (prices.length > 1)
    facts.push(
      `最高与最低参考价相差 ${money(high.current_price - low.current_price)}（${((high.current_price / low.current_price - 1) * 100).toFixed(1)}%）；未计手续费与提现限制。`,
    );
  if (finite(low?.return_7d))
    facts.push(
      `${low.platform} 的 7 日变动为 ${(low.return_7d * 100).toFixed(1)}%。`,
    );
  const total = decision?.score_summary?.total;
  if (finite(total))
    facts.push(
      `规则综合评分 ${total}/100，信号方向${labels[decision.recommendation] || "待确认"}。`,
    );
  const signals = (decision?.supporting_signals || []).map((s) => ({
    direction: s.direction,
    label: s.label,
    note: s.note,
  }));
  const next = ["核实当前挂单、成交深度和平台费用，再判断参考价差是否可交易。"];
  if (
    finite(decision?.score_summary?.liquidity) &&
    decision.score_summary.liquidity < 40
  )
    next.push("流动性评分偏低，优先核对成交量与退出成本。");
  if (signals.some((s) => s.direction === "-"))
    next.push("复核下方负向信号，观察价格与事件变化是否改变原有依据。");
  if (!decision) next.push("决策数据尚未载入，本简报仅汇总已取得的价格信息。");
  if (!prices.length)
    next.push("当前缺少有效报价，先补充数据，不能据此比较价格。");
  return {
    title: overview?.item_name || "饰品研究",
    facts,
    signals,
    next,
    caveat:
      "根据当前已载入的数据按规则汇总，包含示例与估算价格；不是实时验证报价或收益预测。",
  };
}
export function briefText(brief) {
  return [
    brief.title,
    "研究简报 · 本地规则汇总",
    "",
    "当前观察",
    ...brief.facts.map((x) => `• ${x}`),
    "",
    "信号依据",
    ...brief.signals.map(
      (s) => `• [${s.direction}] ${s.label}：${s.note || ""}`,
    ),
    "",
    "后续关注",
    ...brief.next.map((x) => `• ${x}`),
    "",
    brief.caveat,
  ].join("\n");
}
