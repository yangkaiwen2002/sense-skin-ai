import { StrictMode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Research from "./Research";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("restores a saved research session under StrictMode instead of staying in loading", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({
      ok: true,
      json: async () =>
        url.endsWith("/status")
          ? { model: { configured: false }, sources: [] }
          : url.endsWith("/sessions")
            ? { sessions: [] }
            : {
                id: "saved",
                title: "已保存的研究",
                item_ids: [],
                runs: [],
                active_run_id: null,
              },
    })),
  );
  render(
    <StrictMode>
      <MemoryRouter initialEntries={["/research/saved"]}>
        <Routes>
          <Route path="/research/:sessionId" element={<Research />} />
        </Routes>
      </MemoryRouter>
    </StrictMode>,
  );
  await waitFor(() =>
    expect(screen.queryByText("正在恢复研究上下文…")).toBeNull(),
  );
  expect(screen.getByText("已保存的研究")).toBeTruthy();
  expect(
    (screen.getByLabelText("研究目标或追问") as HTMLTextAreaElement).disabled,
  ).toBe(false);
});
