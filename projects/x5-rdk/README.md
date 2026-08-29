# RDK X5 SDK

`x5-rdk` 是 RDK X5 SDK 的多仓聚合知识入口，覆盖 `integration`、`manifest` 和 `vendor-docs` 三个主治理仓。

## 边界

- `integration`：同步、构建、验证、收据和交接流程的工程 SSOT。
- `manifest`：Android repo 项目集合与固定提交点的版本 SSOT。
- `vendor-docs`：供应商资料索引、来源身份与不可变清单的归档 SSOT。
- SDK 源码项目由固定 manifest 约束，不在 Knowledge Hub 中逐仓复制。
- 既有 `projects/firmware-toolchains/validation/` 下的 X5 条目保留原始归属，作为历史来源，不迁移、不重复登记。

## 知识分区

- `current/`：当前有效状态、短期操作入口和待人工评审候选。
- `decisions/`：经评审的架构和治理决策。
- `validation/`：可复核的验证结论与证据摘要。
- `archive/`：经授权生命周期迁移后的历史归档；不得直接写入 `reviewing` 候选。

Knowledge Hub 候选不替代仓库内的版本化文档、CI 结果、构建日志或发布收据，也不代表人工验收已经完成。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](validation/project-readiness.md)
- [统一 readiness dashboard](../../indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
