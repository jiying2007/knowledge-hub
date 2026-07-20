# XCRZ SigmaStar Demo

- 项目 ID：`xcrz-sigmastar-demo`
- 所属组：`pcr02`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=xcrz-sigmastar-demo` 的 Git remote key 为准。
- 当前知识：`projects/xcrz-sigmastar-demo/current/`
- 决策：`projects/xcrz-sigmastar-demo/decisions/`
- 验证：`projects/xcrz-sigmastar-demo/validation/`
- 归档：`projects/xcrz-sigmastar-demo/archive/`

本入口统一承载 `robot/xcrz_sigmastar_demo` 的设备应用、诊断、媒体、显示应用层、模块集成和会话证据。SDK、kernel、boot、镜像、OTA、存储和板级平台事实统一进入 `projects/pcr02-ssc305/`；跨仓记录按结论主责只保留一份正文，再用 `related`、registry 和索引关联。

`pcr02` 仅是 `registry/project-groups.json` 中的产品组 ID，不是独立项目、正文 domain 或兼容路由。源码仓本地 `AGENTS.md` 和运行规则继续由源码仓管理。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](validation/project-readiness.md)
- [统一 readiness dashboard](../../indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
