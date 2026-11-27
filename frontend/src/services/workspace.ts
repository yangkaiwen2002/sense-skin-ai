import { BASE_URL } from "./api";
export interface Session {
  id: string;
  title: string;
  archived: boolean;
  item_ids: number[];
  active_run_id: string | null;
  updated_at: string;
}
export interface RuntimeStatus {
  data_mode: "mock" | "live";
  single_user: boolean;
  checked_at: string;
  catalog_count: number;
  snapshot_count: number;
  model: {
    configured: boolean;
    provider: string;
    model: string | null;
    health: string;
    detail: string;
  };
  runs: {
    sample_size: number;
    completed: number;
    failed: number;
    validated_reports: number;
  };
  recent_runs: {
    id: string;
    session_id: string;
    question: string;
    status: string;
    mode: string;
    created_at: string;
    steps: number;
    sources: number;
  }[];
}
export interface Evaluation {
  summary: { count: number; recall: number; mrr: number; ndcg: number };
  latency_ms: { p50: number; p95: number };
  executed_at: string;
  note: string;
  cases: {
    id: string;
    query: string;
    retrieved_ids: number[];
    metrics: { recall: number };
  }[];
}
export async function workspaceRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "服务暂时不可用，请稍后重试。",
    );
  return data as T;
}
