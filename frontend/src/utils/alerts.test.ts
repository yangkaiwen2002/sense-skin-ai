import { describe, it, expect } from "vitest";
import { evaluateRule, readRules, saveRule, type WatchRule } from "./alerts";
const rule: WatchRule = {
  target: 100,
  direction: "below",
  note: "等待数据",
  enabled: true,
};
describe("watchlist target checks", () => {
  it("does not trigger on stale or unverified quotes", () => {
    expect(
      evaluateRule(rule, {
        current_price: 90,
        price_kind: "observed",
        is_stale: true,
      }).state,
    ).toBe("unknown");
    expect(
      evaluateRule(rule, { current_price: 90, price_kind: "legacy_unknown" })
        .state,
    ).toBe("unknown");
  });
  it("clearly labels a mock threshold match", () => {
    expect(
      evaluateRule(rule, { current_price: 100, price_kind: "demo" }),
    ).toEqual({ state: "matched", label: "演示检查 · 已达到目标" });
  });
  it("honors pause and direction", () => {
    expect(
      evaluateRule(
        { ...rule, enabled: false },
        { current_price: 90, price_kind: "observed" },
      ).state,
    ).toBe("paused");
    expect(
      evaluateRule(
        { ...rule, direction: "above" },
        { current_price: 99, price_kind: "observed" },
      ).state,
    ).toBe("waiting");
  });
  it("handles corrupt storage and preserves other rules", () => {
    localStorage.clear();
    localStorage.setItem("senseskin.watch-rules.v1", '{"1":null}');
    expect(readRules()).toEqual({});
    saveRule(1, rule);
    saveRule(2, { ...rule, target: 200 });
    saveRule(1, null);
    expect(readRules()).toEqual({ "2": { ...rule, target: 200 } });
  });
});
