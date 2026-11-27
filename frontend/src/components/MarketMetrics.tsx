import { catalogMetrics, type Quote } from "../utils/quantitative";
import { formatCNY } from "../utils/formatters";

const labels = {
  observed: "采集",
  demo: "演示",
  stale: "过期",
  unknown: "未核验",
  missing: "无报价",
};
export default function MarketMetrics({
  items,
  total,
  loading,
  failed,
}: {
  items: Quote[];
  total: number;
  loading: boolean;
  failed: boolean;
}) {
  const data = catalogMetrics(items);
  if (loading)
    return (
      <div className="quant-loading" role="status">
        正在统计当前筛选的数据…
      </div>
    );
  if (failed)
    return (
      <p className="quant-unavailable">数据未完整载入，暂不计算市场指标。</p>
    );
  return (
    <section className="market-metrics" aria-label="当前筛选量化概览">
      <div className="quant-section-heading">
        <h2>当前筛选，一眼看清</h2>
        <span>仅统计已载入的 {total} 件饰品</span>
      </div>
      <dl className="quant-grid market-quant-grid">
        <div className="quant-tile">
          <dt>匹配饰品</dt>
          <dd>
            {items.length}
            <small> / {total} 件</small>
          </dd>
          <div className="quant-track" aria-hidden="true">
            <i
              style={{ width: `${total ? (items.length / total) * 100 : 0}%` }}
            />
          </div>
          <p>筛选改变时，以下指标同步更新</p>
        </div>
        <div className="quant-tile">
          <dt>参考价中位数</dt>
          <dd className="quant-money">{formatCNY(data.median)}</dd>
          <p>
            {data.sample
              ? `区间 ${formatCNY(data.min)} – ${formatCNY(data.max)}`
              : "暂无可统计的参考价"}
          </p>
          <p>
            {data.sample} 个价格样本 ·{" "}
            {!data.sample
              ? "等待有效数据"
              : data.counts.demo > 0
                ? "包含演示数据"
                : "采集报价"}
          </p>
        </div>
        <div className="quant-tile">
          <dt>24 小时内采集报价</dt>
          <dd>
            {data.counts.observed}
            <small> / {items.length} 件</small>
          </dd>
          <div className="quant-source-stack" aria-hidden="true">
            {Object.entries(data.counts).map(([key, count]) => (
              <i
                key={key}
                className={`quant-source-${key}`}
                style={{
                  width: `${items.length ? (count / items.length) * 100 : 0}%`,
                }}
              />
            ))}
          </div>
          <p className="quant-legend">
            {Object.entries(data.counts)
              .filter(([, n]) => n > 0)
              .map(([key, count]) => (
                <span key={key}>
                  <i className={`quant-source-${key}`} />
                  {labels[key as keyof typeof labels]} {count}
                </span>
              ))}
            {!items.length && "当前筛选无数据"}
          </p>
        </div>
        <div className="quant-tile quant-distribution">
          <dt>
            价格分布 <span>{data.sample} 件</span>
          </dt>
          <div
            className="quant-histogram"
            role="img"
            aria-label={data.buckets
              .map((b) => `${b.label}：${b.count} 件`)
              .join("；")}
          >
            {data.buckets.map((b) => (
              <div key={b.label}>
                <strong>{b.count}</strong>
                <div>
                  <i
                    style={{
                      height: `${(b.count / Math.max(...data.buckets.map((x) => x.count), 1)) * 100}%`,
                    }}
                  />
                </div>
                <small>{b.label}</small>
              </div>
            ))}
          </div>
        </div>
      </dl>
      <details className="quant-method">
        <summary>统计口径</summary>
        <p>
          中位数和价格分布只采用有明确数据类型、采集时间在最近 24
          小时内的正数参考价，包含已标记的演示价。过期、无报价、时间异常和来源未核验的数据不参与价格统计。不同饰品的价格分布不是市场涨跌指数。
        </p>
      </details>
    </section>
  );
}
