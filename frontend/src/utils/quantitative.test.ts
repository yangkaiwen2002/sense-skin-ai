import { describe, expect, it } from "vitest";
import {
  catalogMetrics,
  priceComparison,
  rentalMetrics,
  researchMetrics,
  type Quote,
} from "./quantitative";
const now = Date.parse("2026-11-27T04:00:00Z");
const quote = (current_price: number, extra: Partial<Quote> = {}): Quote => ({
  current_price,
  price_kind: "demo",
  snapshot_time: "2026-11-27T03:00:00",
  ...extra,
});

describe("quantified market data", () => {
  it("keeps provenance counts and excludes stale/unknown/invalid prices from distribution", () => {
    const data = catalogMetrics(
      [
        quote(50),
        quote(150),
        quote(1000),
        quote(10000),
        quote(1, { price_kind: "observed" }),
        quote(900, { snapshot_time: "2026-11-20T00:00:00Z" }),
        quote(10, { snapshot_time: null }),
        quote(Infinity),
        quote(0),
      ],
      now,
    );
    expect(data.counts).toEqual({
      observed: 1,
      demo: 4,
      stale: 1,
      unknown: 1,
      missing: 2,
    });
    expect(data.median).toBe(150);
    expect(data.buckets.map((b) => b.count)).toEqual([2, 1, 1, 1]);
    expect(catalogMetrics([], now).median).toBeNull();
  });
  it("computes the even median and rejects future timestamps", () => {
    expect(catalogMetrics([quote(100), quote(300)], now).median).toBe(200);
    expect(
      catalogMetrics(
        [quote(100, { snapshot_time: "2027-01-01T00:00:00Z" })],
        now,
      ).sample,
    ).toBe(0);
  });
  it("does not mix a cheaper demo quote into an observed comparison", () => {
    const data = priceComparison(
      [
        quote(20),
        quote(100, { price_kind: "observed" }),
        quote(120, { price_kind: "observed" }),
        quote(1000, { is_stale: true }),
      ],
      now,
    );
    expect(data.low).toBe(100);
    expect(data.gap).toBe(20);
    expect(data.percent).toBe(20);
    expect(data.excluded).toBe(2);
  });
  it("requires two comparable platforms, including when only one is observed", () => {
    expect(
      priceComparison([quote(20), quote(100, { price_kind: "observed" })], now)
        .gap,
    ).toBeNull();
    expect(priceComparison([quote(100), quote(100)], now).percent).toBe(0);
    expect(
      priceComparison([quote(100, { is_stale: true })], now).low,
    ).toBeNull();
  });
});
describe("cost and evidence metrics", () => {
  it("compares usage costs separately from purchase capital and unknown deposit", () => {
    const data = rentalMetrics({
      rent_cost: 9.28,
      buy_resale_loss: 10.07,
      buy_price: 251.68,
      budget: 1000,
      days: 7,
      rent_available: true,
      deposit_required: true,
    });
    expect(data.difference).toBeCloseTo(0.79);
    expect(data.cheaper).toBe("rent");
    expect(data.budgetLeft).toBeCloseTo(748.32);
    expect(data.budgetRatio).toBeCloseTo(25.168);
    expect(data.rentPerDay).toBeCloseTo(9.28 / 7);
  });
  it("handles free rental, absent quotes, zero budget and a capital shortfall", () => {
    expect(
      rentalMetrics({ rent_available: true, rent_cost: 0, buy_resale_loss: 0 })
        .cheaper,
    ).toBe("equal");
    expect(
      rentalMetrics({ rent_available: true, rent_cost: 0, buy_resale_loss: 10 })
        .percent,
    ).toBe(100);
    expect(
      rentalMetrics({ rent_cost: 0, buy_resale_loss: 10 }).difference,
    ).toBeNull();
    expect(rentalMetrics({ buy_price: 100, budget: 0 }).budgetRatio).toBeNull();
    expect(rentalMetrics({ buy_price: 100, budget: 20 }).budgetLeft).toBe(-80);
  });
  it("counts distinct actual citations and reports only complete duration telemetry", () => {
    const run = {
      sources: [
        { id: "S1", kind: "market" },
        { id: "S2", kind: "knowledge" },
      ],
      artifact: {
        report: {
          findings: [
            { source_id: "S1" },
            { source_id: "S1" },
            { source_id: "S99" },
          ],
        },
        validation: {
          tool_calls: 1,
          model_calls: [{ duration_ms: 300 }, { duration_ms: 500 }],
        },
      },
    };
    expect(researchMetrics(run)).toEqual({
      sources: 2,
      cited: 1,
      tools: 1,
      duration: 800,
    });
    expect(researchMetrics({ sources: run.sources }).cited).toBeNull();
    expect(
      researchMetrics({ artifact: { validation: { model_calls: [{}] } } })
        .duration,
    ).toBeNull();
  });
});
