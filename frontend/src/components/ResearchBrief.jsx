import { useMemo } from "react";
import { DownloadSimple, ListChecks } from "@phosphor-icons/react";
import { buildResearchBrief, briefText } from "../utils/researchBrief";
import Button from "./ui/Button";
export default function ResearchBrief({ overview, decision, loading }) {
  const brief = useMemo(
    () => buildResearchBrief(overview, decision),
    [overview, decision],
  );
  function download() {
    const url = URL.createObjectURL(
      new Blob([briefText(brief)], { type: "text/plain;charset=utf-8" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `SenseSkin-research-${overview.item_id}.txt`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return (
    <section className="surface-card p-5" aria-label="本地研究简报">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div>
          <h2 className="text-base font-semibold flex items-center gap-2">
            <ListChecks size={19} className="text-[var(--accent)]" />
            研究简报
          </h2>
          <p className="text-[11px] text-[var(--text-secondary)] mt-1">
            行情汇总 → 信号依据 → 后续关注 · 无需 AI 密钥
          </p>
        </div>
        <Button size="sm" onClick={download} disabled={loading}>
          <DownloadSimple size={14} />
          导出简报
        </Button>
      </div>
      {loading && (
        <p role="status" className="text-xs text-[var(--text-dim)] mb-3">
          正在汇总信号…
        </p>
      )}
      <ul className="space-y-2 text-[13px] leading-6">
        {brief.facts.map((x) => (
          <li key={x}>{x}</li>
        ))}
      </ul>
      <details className="mt-4 border-t border-[var(--border-default)] pt-3">
        <summary className="cursor-pointer text-xs text-[var(--accent)]">
          核对信号依据（{brief.signals.length}）
        </summary>
        <ul className="mt-3 space-y-2">
          {brief.signals.map((s, i) => (
            <li className="text-xs leading-6" key={i}>
              <strong
                className={
                  s.direction === "-"
                    ? "text-[var(--avoid)]"
                    : "text-[var(--text-primary)]"
                }
              >
                {s.label}
              </strong>{" "}
              · {s.note}
            </li>
          ))}
        </ul>
      </details>
      <div className="mt-4 p-3 bg-[var(--bg-surface-raised)] rounded">
        <h3 className="font-semibold text-xs mb-2">后续关注</h3>
        <ul className="text-xs text-[var(--text-secondary)] leading-6 space-y-1">
          {brief.next.map((x) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </div>
      <p className="text-[10px] text-[var(--text-dim)] mt-3 leading-5">
        {brief.caveat}
      </p>
    </section>
  );
}
