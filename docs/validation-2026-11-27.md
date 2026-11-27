# 本地产品验收 · 2026-11-27

范围：Mock 业务 API + 真实本地 Ollama 0.40.18 / Qwen3 4B，macOS Apple Silicon，React 开发预览与独立生产构建。行情、租赁和事件数据均为演示数据；模型生成和工具执行实际发生。

## 自动检查

| 检查 | 结果 |
| --- | --- |
| Python / FastAPI / Agent / 数据边界 | 102 passed，1 skipped |
| TypeScript | `tsc --noEmit` 通过；覆盖新增 TypeScript 页面与客户端契约 |
| 前端数据与 SSE 单测 | 9 passed |
| Vitest 页面与交互 | 8 passed |
| 生产构建 | Vite 8 构建成功 |
| 前端依赖审计 | `npm audit`：0 vulnerabilities（本次审计时） |
| 24 题检索回归 | 基线门禁通过 |
| `git diff --check` | 通过 |

跳过项是需显式开启的真实 embedding 模型烟测。FAISS 固定向量逻辑测试已经运行；默认本地检索未启用语义模型。Python 仍有依赖和 `datetime.utcnow()` 等弃用警告，不代表测试失败。

当前默认 TF-IDF + BM25 RRF 的 Recall@3 为 **0.7917**，MRR@3 为 **0.8125**，nDCG@3 为 **0.7468**。这是固定 24 题检索集的结果，不是生成质量、收益率或长期 Agent 成功率。

## 免费模型真实链路

执行 `make smoke`（含 `--require-generated`），三条请求都完成，报告通过结构、来源引文与数字校验，无修复、无降级。

| 场景 | 模型选定工具次数 | 本地会话 |
| --- | --- | --- |
| 红线各平台报价与数据边界 | 1 | `ddbaabc5-b6f7-4c7b-b8fe-0c0758f8f914` |
| 流动性知识与需核对的数据 | 1 | `4c4ea877-df5a-4701-a9c4-e45059cd1141` |
| 红线使用 7 天、预算 1000 元的租买分析 | 4 | `177e38e7-a6f7-4249-9216-778aada65737` |

租买结果引用本次工具输出中的演示租金 9.28 元、购买本金 251.68 元、情景转卖损耗 10.07 元，并保留“押金金额未知，无法确认全部资金需求”。这些数值仅用于复核演示数据流。

验收过程中发现并修复了研究页在 StrictMode 下重新打开会话一直加载、目录名称中的 AK-47 被误当作不支持数字、长租买说明截断押金缺口等问题，均加入回归测试。早期小模型输出失败记录保留在本地运行统计中，未伪装成成功记录；重复试验可归档恢复。

## 浏览器检查与截图

实际在 Chrome 检查：市场搜索与 URL 筛选、详情来源、收藏目标价及备注、租买计算、平台比较、研究流式过程及重新打开、研究库重命名/归档/恢复、知识检索、现场运行评估。390 px 移动端检查了市场、比较、租买与研究，未发现页面整体横向溢出。最后检查未出现浏览器 console error/warn。

- [市场桌面](screenshots/product-market-desktop.jpg)
- [Agent 工具轨迹](screenshots/product-agent-trace-desktop.jpg)
- [模型连接与运行状态](screenshots/product-system-desktop.jpg)
- [检索评估](screenshots/product-evaluation-desktop.jpg)
- [市场移动端](screenshots/product-market-mobile.jpg)
- [研究移动端](screenshots/product-research-mobile.jpg)

## 未覆盖与限制

这些检查证明本地主要流程可运行，不构成生产就绪证明。没有 Docker 环境，Compose 未启动实测；没有真实平台授权接入、账户隔离、跨设备同步、后台通知、生产压测和长期生成评估。小模型仍可能被校验拒绝；降级会清楚标识。静态知识库尚未逐条独立核验。

代码与简历能力的对应关系，以及不能声称已完成的部分，见 [工程能力与边界](engineering-evidence.md)。
