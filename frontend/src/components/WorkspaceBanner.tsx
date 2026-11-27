import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { workspaceRequest, type RuntimeStatus } from "../services/workspace";
export default function WorkspaceBanner() {
  const [status, setStatus] = useState<RuntimeStatus | null>(null),
    [failed, setFailed] = useState(false);
  useEffect(() => {
    const ctrl = new AbortController();
    workspaceRequest<RuntimeStatus>("/workspace/status", {
      signal: ctrl.signal,
    })
      .then(setStatus)
      .catch((e) => {
        if (e.name !== "AbortError") setFailed(true);
      });
    return () => ctrl.abort();
  }, []);
  return (
    <div className="workspace-banner">
      <div>
        <span
          className={`connection-dot ${status?.model.health === "ready" ? "is-ready" : ""}`}
        />
        <span>
          {failed
            ? "后端连接失败"
            : status
              ? status.data_mode === "mock"
                ? "演示工作区 · 行情与事件为 Mock 数据"
                : "行情工作区 · 请核对每条数据来源"
              : "正在检查工作区…"}
        </span>
      </div>
      <Link to="/system">
        {status?.model.health === "ready"
          ? "本地 Agent 在线"
          : "连接与数据说明"}
      </Link>
    </div>
  );
}
