# Knowledge Hub Schemas

本目录提供核心结构化契约的机器可读 JSON Schema。运行时仍以 `registry/schema.md` 和 Python 内核的显式校验为准；schema 文件用于编辑器提示、离线审查和后续 CI，不会自动修改 registry。

`catalog.json` 是入口目录，并明确 registry/Markdown 双权威边界：身份与生命周期以 registry 为准；标题、摘要、标签、关系和正文以 Markdown 为内容权威；frontmatter 只是受 drift gate 约束的镜像。

- `item.schema.json`：`registry/items.jsonl` 单行条目。
- `authorization.schema.json`：`registry/authorizations.jsonl` 单行授权。
- `review-attestation.schema.json`：绑定正文 hash、原状态和目标状态的本地内容复核确认表；该表不包含执行授权。
- `lifecycle-event.schema.json`：`registry/lifecycle-events.jsonl` 单行生命周期事件。
- `frontmatter-mirror.schema.json`：managed Markdown Properties 镜像。
- `retrieval-result.schema.json`：检索 JSON v3 契约；v3 将有界 `search_trace` 与阶段化 `timing` 固化为必需字段，修正了 v2 在不升版本时增加必需字段的版本语义缺口。
- `agent-contract.schema.json`：registry item 可选的显式 Agent 运行时角色、scope、capability、guard 与关系契约。
- `knowledge-map.schema.json`：有界、可分页、仅用于导航的 registry map 契约。
- `evidence-pack.schema.json`：MUST / SHOULD / CONTEXT / PROVISIONAL / CONFLICT / MISSING 分层契约。
- `action-check.schema.json`：`ALLOW / BLOCK / NEEDS_REVIEW` 确定性动作预检契约。
- `agent-review-policy.schema.json`：默认禁用的 report-only shadow proposal policy。
- `proposal-route.schema.json`：不写 registry 的候选路由评估契约。
- `proposal-shadow-stats.schema.json`：不回显 proposal/client 内容的本地 shadow 哈希链与路由安全汇总契约。
- `raw-evidence-inspection.schema.json`：rawmem-compatible ledger 的 metadata-only、fail-closed 检查契约。
- `artifact-restore-drill.schema.json`：checksum-bound release source 的隔离复制、负例检测、恢复与 source 不变契约。
- `compliance-eval.schema.json`：批量动作合规用例 v2 的脱敏结果契约，包含最小样本门槛与 high-risk false-allow 汇总。
- `project-readiness.schema.json`：项目能力矩阵契约。
- `local-workspaces.schema.json`：未跟踪的本机 Git workspace 发现结果契约。
- `final-gate-product.schema.json`：唯一 product 终态门禁契约。
- `obsidian-view-build.schema.json`：managed Properties、MOC 和 Base 构建契约。
- `team-export.schema.json`：本地团队导出计划/结果契约。
- `restore-drill.schema.json`：无 cache、无 local mapping 的恢复演练契约。
- `local-metrics.schema.json`：只保存 query hash 的本地运营指标 v3 契约；usage/feedback 与 performance 分别绑定 interaction/performance contract，旧实现性能样本只保留为 provenance。
- `pcr02-evidence-readiness.schema.json`：PCR02 三条 reviewing candidate 证据路径契约。

JSONL 文件应逐行应用对应 schema。授权状态、日期窗口、scope 与动作匹配仍属于跨行/运行时约束，不能只靠 JSON Schema 证明。
