import { beforeEach, expect, it } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import WatchRuleEditor from "./WatchRuleEditor";
beforeEach(() => {
  cleanup();
  localStorage.clear();
});
it("saves a target, shows the mock result and pauses without losing the note", async () => {
  const user = userEvent.setup();
  render(
    <WatchRuleEditor
      id={1}
      quote={{ current_price: 90, price_kind: "demo" }}
    />,
  );
  await user.click(screen.getByRole("button", { name: "设置" }));
  await user.type(screen.getByLabelText("目标价格（元）"), "100");
  await user.type(screen.getByLabelText("研究备注"), "需要真实报价");
  await user.click(screen.getByRole("button", { name: "保存条件" }));
  expect(screen.getByText(/演示检查 · 已达到目标/)).toBeTruthy();
  expect(screen.getByText("需要真实报价")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "暂停监控" }));
  expect(screen.getByText(/已暂停/)).toBeTruthy();
});
