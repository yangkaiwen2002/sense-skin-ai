import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import MarketMetrics from "./MarketMetrics";
import PriceComparisonMetrics from "./PriceComparisonMetrics";
import RentalMetrics from "./RentalMetrics";
afterEach(cleanup);
const items = [
  {
    current_price: 100,
    price_kind: "demo",
    snapshot_time: new Date().toISOString(),
  },
  {
    current_price: 300,
    price_kind: "demo",
    snapshot_time: new Date().toISOString(),
  },
];
it("updates market statistics with the filtered items and does not show false zeroes on failure", () => {
  const { rerender } = render(
    <MarketMetrics items={items} total={2} loading={false} failed={false} />,
  );
  expect(screen.getByText("¥200.00")).toBeTruthy();
  rerender(
    <MarketMetrics
      items={items.slice(0, 1)}
      total={2}
      loading={false}
      failed={false}
    />,
  );
  expect(screen.getByText("¥100.00")).toBeTruthy();
  rerender(
    <MarketMetrics items={[]} total={2} loading={false} failed={true} />,
  );
  expect(screen.queryByText("¥100.00")).toBeNull();
  expect(screen.getByText("数据未完整载入，暂不计算市场指标。")).toBeTruthy();
});
it("explicitly labels demo comparison and missing deposit alongside an apparent cost advantage", () => {
  render(
    <>
      <PriceComparisonMetrics
        platforms={items.map((p, i) => ({ ...p, platform: `平台${i}` }))}
      />
      <RentalMetrics
        rent_cost={9.28}
        rent_available
        buy_resale_loss={10.07}
        buy_price={251.68}
        budget={1000}
        days={7}
        deposit_required
      />
    </>,
  );
  expect(screen.getByText("演示报价比较")).toBeTruthy();
  expect(screen.getByText("¥0.79")).toBeTruthy();
  expect(
    screen.getByText("租赁押金金额未知 · 无法计算租赁总资金占用"),
  ).toBeTruthy();
});
