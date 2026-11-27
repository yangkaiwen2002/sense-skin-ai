import { rentalMetrics, type RentalInput } from "../utils/quantitative";
import { formatCNY } from "../utils/formatters";

export default function RentalMetrics(props: RentalInput) {
  const data = rentalMetrics(props);
  return (
    <section className="rental-quant" aria-label="租买成本量化">
      <div className="quant-section-heading">
        <h3>同一使用期，成本差多少？</h3>
        <span>{props.days} 天 · 租金为演示数据</span>
      </div>
      <div className="rental-quant-hero">
        <div>
          <span>
            {!data.cheaper
              ? "使用成本差额 · 数据不足"
              : data.cheaper === "equal"
                ? "使用成本差额 · 两种情景相同"
                : `使用成本差额 · ${data.cheaper === "rent" ? "租赁" : "购买后转卖"}较低`}
          </span>
          <strong>{formatCNY(data.difference)}</strong>
        </div>
        <p>
          {data.cheaper === "equal"
            ? "两种使用成本一致"
            : data.percent !== null
              ? `比另一方案低 ${data.percent.toFixed(1)}%`
              : "需同时取得租金和转卖损耗"}
          <small>只比较使用成本，另需核对本金与押金</small>
        </p>
      </div>
      <div className="rental-cost-bars">
        {[
          { title: "租赁总费用", value: data.rent, daily: data.rentPerDay },
          { title: "转卖损耗情景", value: data.loss, daily: data.buyPerDay },
        ].map((row, i) => (
          <div key={row.title}>
            <div>
              <span>{row.title}</span>
              <strong>
                {formatCNY(row.value)}
                <small>
                  {row.daily !== null
                    ? `${formatCNY(row.daily)} / 天`
                    : "日均不可用"}
                </small>
              </strong>
            </div>
            <div className={`quant-track cost-bar-${i}`} aria-hidden="true">
              <i
                style={{
                  width: `${row.value !== null && data.maximum > 0 ? (row.value / data.maximum) * 100 : 0}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
      <div className="rental-capital">
        <div>
          <span>购买本金占预算</span>
          <strong>
            {data.budgetRatio !== null
              ? `${data.budgetRatio.toFixed(1)}%`
              : "—"}
          </strong>
        </div>
        <div className="quant-track" aria-hidden="true">
          <i
            className={
              data.budgetLeft !== null && data.budgetLeft < 0
                ? "is-over-budget"
                : ""
            }
            style={{ width: `${Math.min(data.budgetRatio ?? 0, 100)}%` }}
          />
        </div>
        <p>
          {data.budgetLeft !== null
            ? `${data.budgetLeft < 0 ? "本金缺口" : "支付本金后剩余"} ${formatCNY(Math.abs(data.budgetLeft))} · 不含手续费`
            : "本金或预算缺失，无法计算"}
        </p>
        {props.deposit_required && (
          <p className="quant-deposit">
            租赁押金金额未知 · 无法计算租赁总资金占用
          </p>
        )}
      </div>
      <details className="quant-method">
        <summary>成本口径</summary>
        <p>
          成本差额 =
          两种使用成本的绝对差；差额百分比以较高方案的成本为分母。购买一栏比较本次持有期的转卖损耗情景，并非全部购买本金。未包含未来价格涨跌、手续费及未知押金；成本较低不代表预算一定可负担。
        </p>
      </details>
    </section>
  );
}
