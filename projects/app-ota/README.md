# PCR02 OTA App

- 项目 ID：`app-ota`
- 所属组：`pcr02`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=app-ota` 的 Git remote key 为准。
- 当前知识：`projects/app-ota/current/`
- 决策：`projects/app-ota/decisions/`
- 验证：`projects/app-ota/validation/`
- 归档：`projects/app-ota/archive/`

OTA app 的发布、协议、升级验证和失败分析优先沉淀到本入口；跨 SDK 发布链结论再同步到 `projects/pcr02-ssc305/`。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是 `reviewing` 控制资产，用于补齐项目画像、维护、决策和验证结构；不代表 owner 签收或发布就绪。

- [项目画像候选](current/project-profile.md)
- [维护 runbook](current/runbooks/maintenance-entry.md)
- [权威边界决策候选](decisions/project-boundary-decision-candidate.md)
- [readiness validation](validation/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
