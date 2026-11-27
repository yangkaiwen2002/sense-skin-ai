import { researchMetrics, type RunMetricsInput } from "../utils/quantitative";

export default function ResearchMetrics({ run }: { run: RunMetricsInput }) {
  const metrics = researchMetrics(run);
  return (
    <section className="research-quant" aria-label="本轮研究量化">
      <dl className="quant-grid">
        <div>
          <dt>证据来源</dt>
          <dd>
            {metrics.sources}
            <small> 条</small>
          </dd>
        </div>
        <div>
          <dt>报告引用</dt>
          <dd>
            {metrics.cited ?? "—"}
            <small> / {metrics.sources} 来源</small>
          </dd>
        </div>
        <div>
          <dt>模型选定工具</dt>
          <dd>
            {metrics.tools ?? "—"}
            <small> 次</small>
          </dd>
        </div>
        <div>
          <dt>模型调用耗时</dt>
          <dd>
            {metrics.duration !== null
              ? (metrics.duration / 1000).toFixed(1)
              : "—"}
            <small> 秒</small>
          </dd>
        </div>
      </dl>
      <p>
        引用数按不同来源计；耗时为已记录的模型调用总和。以上是执行记录，不是回答准确率。
      </p>
    </section>
  );
}
