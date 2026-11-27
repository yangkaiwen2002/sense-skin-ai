import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Library from "./Library";
const row = {
  id: "test",
  title: "原研究标题",
  archived: false,
  item_ids: [1],
  active_run_id: null,
  updated_at: "2026-11-27T00:00:00Z",
};
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("renames a persisted session and reports success", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ sessions: [row] }),
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ...row, title: "新的研究标题" }),
    });
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <Library />
    </MemoryRouter>,
  );
  await user.click(
    await screen.findByRole("button", { name: "重命名：原研究标题" }),
  );
  const input = screen.getByLabelText("研究标题");
  await user.clear(input);
  await user.type(input, "新的研究标题");
  await user.click(screen.getByRole("button", { name: "保存" }));
  expect(
    await screen.findByRole("link", { name: "新的研究标题" }),
  ).toBeTruthy();
  expect(fetchMock.mock.calls[1][1].method).toBe("PATCH");
});
it("shows a failed request and allows retry without inventing records", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockRejectedValueOnce(new Error("连接失败"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ sessions: [] }),
      }),
  );
  const user = userEvent.setup();
  render(
    <MemoryRouter>
      <Library />
    </MemoryRouter>,
  );
  expect(await screen.findByRole("alert")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: "重新加载" }));
  await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  expect(await screen.findByText("从一个具体问题开始")).toBeTruthy();
});
