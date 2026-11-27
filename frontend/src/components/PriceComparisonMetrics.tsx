import { priceComparison, type Quote } from "../utils/quantitative";
import { formatCNY } from "../utils/formatters";
import QuoteSource from "./QuoteSource";

export default function PriceComparisonMetrics({
  platforms,
  compact = false,
}: {
  platforms: Quote[];
  compact?: boolean;
}) {
  const data = priceComparison(platforms);
  const label = !data.eligible.length
    ? "暂无可比较报价"
    : data.kind === "demo"
      ? "演示报价比较"
      : "采集报价比较";
  return (
    <section
      className={`price-quant ${compact ? "is-compact" : ""}`}
      aria-label="平台价差量化"
    >
      <div className="quant-section-heading">
        <h2>{label}</h2>
        <span>
          {data.eligible.length} / {platforms.length} 个平台参与
        </span>
      </div>
      <dl className="quant-grid quant-grid-three">
        <div className="quant-tile">
          <dt>最低参考价</dt>
          <dd className="quant-money">{formatCNY(data.low)}</dd>
          <p>{data.eligible[0]?.platform || "暂无可用报价"}</p>
        </div>
        <div className="quant-tile quant-tile-accent">
          <dt>最高与最低相差</dt>
          <dd className="quant-money">{formatCNY(data.gap)}</dd>
          <p>
            {data.percent !== null
              ? `最高报价高出 ${data.percent.toFixed(1)}%`
              : "至少需要两个同类型的新鲜报价"}
          </p>
        </div>
        <div className="quant-tile">
          <dt>最高参考价</dt>
          <dd className="quant-money">{formatCNY(data.high)}</dd>
          <p>{data.eligible.at(-1)?.platform || "暂无可用报价"}</p>
        </div>
      </dl>
      {!compact && (
        <div className="quant-price-rows">
          {data.eligible.map((p) => {
            const delta = p.current_price! - data.low!;
            return (
              <div key={p.platform} className="quant-price-row">
                <div className="quant-price-row-heading">
                  <strong>{p.platform}</strong>
                  <span>{formatCNY(p.current_price)}</span>
                </div>
                <div className="quant-delta-row">
                  <div className="quant-track" aria-hidden="true">
                    <i
                      style={{
                        width: `${data.gap ? (delta / data.gap) * 100 : 0}%`,
                      }}
                    />
                  </div>
                  <span>
                    {data.eligible.length < 2
                      ? "暂无对照"
                      : delta === 0
                        ? "最低基准"
                        : `贵 ${formatCNY(delta)} · +${((delta / data.low!) * 100).toFixed(1)}%`}
                  </span>
                </div>
                <QuoteSource quote={p} compact />
              </div>
            );
          })}
        </div>
      )}
      <p className="quant-note">
        {data.kind === "demo" && data.eligible.length > 0
          ? "演示价差，不是可成交收益。"
          : "参考价差未包含费用与提现限制。"}
        {data.excluded > 0 &&
          ` ${data.excluded} 个平台因过期、缺失、未核验或数据类型不同而排除。`}
      </p>
      {!compact && (
        <details className="quant-method">
          <summary>价差怎么算</summary>
          <p>
            相差金额 = 最高价 − 最低价；百分比 = 相差金额 ÷
            最低价。条形长度显示各平台相对最低价的差额，以最大差额为满格。优先比较新鲜采集报价；没有采集报价时才比较演示价，两者不混算。
          </p>
        </details>
      )}
    </section>
  );
}
