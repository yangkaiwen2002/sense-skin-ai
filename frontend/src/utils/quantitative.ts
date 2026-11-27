import { quoteMetadata } from "./quotes";

export interface Quote {
  current_price?: number | null;
  price_kind?: string | null;
  snapshot_time?: string | null;
  is_stale?: boolean;
  platform?: string;
  weapon_type?: string | null;
}
export const isAmount = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value) && value >= 0;

export function quoteState(quote: Quote, now = Date.now()) {
  if (!isAmount(quote.current_price) || quote.current_price === 0)
    return "missing";
  const meta = quoteMetadata(quote, now);
  if (meta.stale) return "stale";
  if (
    !meta.date ||
    meta.date.getTime() > now ||
    !["observed", "demo"].includes(quote.price_kind || "")
  )
    return "unknown";
  return quote.price_kind === "observed" ? "observed" : "demo";
}

export function catalogMetrics(items: Quote[], now = Date.now()) {
  const counts = { observed: 0, demo: 0, stale: 0, unknown: 0, missing: 0 };
  for (const item of items) counts[quoteState(item, now)]++;
  const prices = items
    .filter((q) => ["observed", "demo"].includes(quoteState(q, now)))
    .map((q) => q.current_price as number)
    .sort((a, b) => a - b);
  const middle = Math.floor(prices.length / 2);
  const median = prices.length
    ? prices.length % 2
      ? prices[middle]
      : (prices[middle - 1] + prices[middle]) / 2
    : null;
  return {
    counts,
    sample: prices.length,
    median,
    min: prices[0] ?? null,
    max: prices.at(-1) ?? null,
    buckets: [
      { label: "< ¥100", count: prices.filter((p) => p < 100).length },
      {
        label: "¥100–1千",
        count: prices.filter((p) => p >= 100 && p < 1000).length,
      },
      {
        label: "¥1千–1万",
        count: prices.filter((p) => p >= 1000 && p < 10000).length,
      },
      { label: "≥ ¥1万", count: prices.filter((p) => p >= 10000).length },
    ],
  };
}

export function priceComparison(platforms: Quote[], now = Date.now()) {
  const fresh = platforms.filter((p) =>
    ["observed", "demo"].includes(quoteState(p, now)),
  );
  const kind = fresh.some((p) => p.price_kind === "observed")
    ? "observed"
    : "demo";
  const eligible = fresh
    .filter((p) => p.price_kind === kind)
    .sort((a, b) => a.current_price! - b.current_price!);
  const low = eligible[0]?.current_price ?? null,
    high = eligible.at(-1)?.current_price ?? null;
  const gap =
    eligible.length >= 2 && low !== null && high !== null ? high - low : null;
  return {
    kind,
    eligible,
    excluded: platforms.length - eligible.length,
    low,
    high,
    gap,
    percent: gap !== null && low ? (gap / low) * 100 : null,
  };
}

export interface RentalInput {
  rent_cost?: number | null;
  buy_resale_loss?: number | null;
  buy_price?: number | null;
  days?: number;
  budget?: number;
  deposit_required?: boolean;
  rent_available?: boolean;
}
export function rentalMetrics(data: RentalInput) {
  const rent =
    data.rent_available && isAmount(data.rent_cost) ? data.rent_cost : null;
  const loss = isAmount(data.buy_resale_loss) ? data.buy_resale_loss : null;
  const comparable = rent !== null && loss !== null;
  const difference = comparable ? Math.abs(rent - loss) : null;
  const maximum = Math.max(rent ?? 0, loss ?? 0);
  const cheaper = !comparable
    ? null
    : rent === loss
      ? "equal"
      : rent < loss
        ? "rent"
        : "buy";
  const budgetRatio =
    isAmount(data.buy_price) && isAmount(data.budget) && data.budget > 0
      ? (data.buy_price / data.budget) * 100
      : null;
  const budgetLeft =
    isAmount(data.buy_price) && isAmount(data.budget)
      ? data.budget - data.buy_price
      : null;
  return {
    rent,
    loss,
    difference,
    maximum,
    cheaper,
    budgetRatio,
    budgetLeft,
    percent:
      difference !== null && maximum > 0 ? (difference / maximum) * 100 : null,
    rentPerDay:
      rent !== null && data.days && data.days > 0 ? rent / data.days : null,
    buyPerDay:
      loss !== null && data.days && data.days > 0 ? loss / data.days : null,
  };
}

export interface RunMetricsInput {
  sources?: { id: string; kind: string }[];
  artifact?: {
    report?: { findings: { source_id: string }[] };
    validation?: {
      tool_calls?: number;
      model_calls?: { duration_ms?: number }[];
    };
  } | null;
}
export function researchMetrics(run: RunMetricsInput) {
  const sourceIds = new Set((run.sources || []).map((s) => s.id));
  const cited = run.artifact?.report
    ? new Set(
        run.artifact.report.findings
          .map((f) => f.source_id)
          .filter((id) => sourceIds.has(id)),
      ).size
    : null;
  const calls = run.artifact?.validation?.model_calls;
  const duration =
    calls?.length && calls.every((c) => isAmount(c.duration_ms))
      ? calls.reduce((n, c) => n + c.duration_ms!, 0)
      : null;
  return {
    sources: sourceIds.size,
    cited,
    duration,
    tools: run.artifact?.validation?.tool_calls ?? null,
  };
}
