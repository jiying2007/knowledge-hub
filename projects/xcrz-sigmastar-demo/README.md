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

## 版本化架构候选入口（仅作历史导航）

以下链接是已明确登记 `supersedes_candidate` 的候选链末端，不代表真实
Owner 签收、源仓硬切换或生产验收。历史原文继续保留唯一正文与证据追溯，
但不应将旧版方案当作新的实施指令。

- [HDI/HAL/Diag v4：当前版本化候选末端](decisions/hdi-hal-cross-platform-host-development-architecture-20260813-v4.md)：早期初版 → v2 → v3 → v4
- [Diag/Observability/Maintenance v3：当前版本化候选末端](decisions/diag-observability-maintenance-cross-platform-plane-20260813-v3.md)：初版 → v2 → v3

上述文档在 Registry 中仍为 `reviewing`；只有源项目真实验收、独立
owner decision 和明确的受治理生命周期操作才能改变知识权威状态。
自动全库审计仅把旧版标记为“已声明被后续候选覆盖，建议比对清理”，
不执行物理删除、变更 `review_after` 或自动提升 `active`。


## 低帧媒体切换的历史纠偏导航（不提供产品默认值授权）

同一功能存在不同时间和作用域的观察，禁止按文件名中的“最终”、最近日期或一次
HIL 的 PASS 自动提升为当前生产事实。四份入口在 Registry 中仍为
`reviewing`，源仓和实机证据需重新按具体 commit/firmware 身份核验。

- [ProfileSwitchMode 受审候选](current/decisions/active-low-1-profile-switch-mode.md)：记录 COLD 为安全默认、WARM 为预生产验证候选、HOT 仅用于受控实验；不能视为已获产品 Owner 发布批准
- [7 月 31 日推送及短周期板测](validation/2026-07-31-vi-fps-publish-validation.md)：证明当时的远端分支身份及 5 轮双向切换测试，不证明长期稳定性、功耗、温循或当前版本已部署
- [8 月 15 日 WARM + 当前业务负载故障复核 V2](archive/debug/2026-08-15-warm-current-workload-cmdq-regression-v2.md)：明确纠正对 VIF sleep/re-arm 的单因归因，保留 AE warmup、DS2_RAW/SCL 负载及 WARM Channel rebuild 的交互假设；需要同构建单变量 A/B
- [8 月 14 日原始 WARM 故障观察](archive/debug/2026-08-14-warm-vif-sleep-cmdq-regression.md)：仅作最初日志和推断的历史出处，**不得单独据此宣称** VIF sleep 是已确认根因，或推导 HOT 必然失败

上述是**导航与适用性提醒**，不是覆盖原始证据的整篇
`supersedes_candidate`、历史删除指令或自动更新 Registry 的决策。
只有当前源码/固件、相同业务负载的失败/通过 A/B、COLD/WARM/HOT 回归、长稳、温循、
日夜/IR、功耗及独立 Owner 资格验证闭环后，才能改变生产配置建议。
