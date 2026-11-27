import { ArrowSquareOut, Quotes } from "@phosphor-icons/react";
interface Finding {
  source_id: string;
  quote: string;
  observation: string;
}
interface Report {
  conclusion: string;
  findings: Finding[];
  next_action: string;
}
export default function StructuredReport({
  report,
  runId,
  sources,
}: {
  report: Report;
  runId: string;
  sources: { id: string; kind: string }[];
}) {
  function openSource(id: string) {
    const el = document.getElementById(`source-${runId}-${id}`);
    if (el instanceof HTMLDetailsElement) el.open = true;
  }
  const groups: (Omit<Finding, "quote"> & { quotes: string[] })[] = [];
  for (const finding of report.findings) {
    const group = groups.find(
      (g) =>
        g.source_id === finding.source_id &&
        g.observation === finding.observation,
    );
    if (group) {
      if (!group.quotes.includes(finding.quote))
        group.quotes.push(finding.quote);
    } else groups.push({ ...finding, quotes: [finding.quote] });
  }
  return (
    <section className="structured-report">
      <header>
        <span className="eyebrow">RESEARCH CONCLUSION</span>
        <h3>{report.conclusion}</h3>
        <p>根据本轮证据形成的研究结论</p>
      </header>
      <div className="report-findings">
        {groups.map((finding, i) => (
          <article key={i}>
            <div>
              <span className="finding-number">
                {String(i + 1).padStart(2, "0")}
              </span>
              <p>{finding.observation}</p>
              <a
                href={`#source-${runId}-${finding.source_id}`}
                onClick={() => openSource(finding.source_id)}
                aria-label={`查看来源 ${finding.source_id}`}
              >
                {finding.source_id}
                <ArrowSquareOut size={13} />
              </a>
            </div>
            <small className="finding-source-kind">
              {sources.find((s) => s.id === finding.source_id)?.kind ===
              "knowledge"
                ? "静态知识资料 · 未独立核验"
                : sources.find((s) => s.id === finding.source_id)?.kind ===
                    "rental"
                  ? "租买计算 · 演示租金"
                  : "本轮来源 · 请核对数据类型"}
            </small>
            {finding.quotes.map((quote, q) =>
              quote.length <= 180 ? (
                <blockquote className="inline-evidence" key={q}>
                  {quote}
                </blockquote>
              ) : (
                <details key={q}>
                  <summary>
                    <Quotes size={14} />
                    核对原文摘录
                  </summary>
                  <blockquote>{quote}</blockquote>
                </details>
              ),
            )}
          </article>
        ))}
      </div>
      <footer>
        <strong>下一步</strong>
        <p>{report.next_action}</p>
      </footer>
      <p className="report-limit">
        引文和数字通过来源校验，不代表语义正确性已验证。演示数据不能用于交易，静态资料不代表当前行情。
      </p>
    </section>
  );
}
