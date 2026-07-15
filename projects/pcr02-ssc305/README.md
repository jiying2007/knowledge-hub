# PCR02 SSC305 SDK

- 项目 ID：`pcr02-ssc305`
- 所属组：`pcr02`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=pcr02-ssc305` 的 Git remote key 为准。
- 当前知识：`projects/pcr02-ssc305/current/`
- 决策：`projects/pcr02-ssc305/decisions/`
- 验证：`projects/pcr02-ssc305/validation/`
- 归档：`projects/pcr02-ssc305/archive/`

本入口只承载 `robot/pcr02_ssc305` 的 SDK、kernel、boot、镜像、OTA、存储、板级硬件和平台集成事实。`robot/xcrz_sigmastar_demo` 的应用、诊断、媒体、显示应用层和模块联调事实统一进入 `projects/xcrz-sigmastar-demo/`；跨仓记录按结论主责只保留一份正文，再用 `related`、registry 和索引关联。

`pcr02` 仅是 `registry/project-groups.json` 中的产品组 ID，不是独立项目、正文 domain 或兼容路由。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是 `reviewing` 控制资产，用于补齐项目画像、维护、决策和验证结构；不代表 owner 签收或发布就绪。

- [项目画像候选](current/project-profile.md)
- [维护 runbook](current/runbooks/maintenance-entry.md)
- [权威边界决策候选](decisions/project-boundary-decision-candidate.md)
- [readiness validation](validation/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
