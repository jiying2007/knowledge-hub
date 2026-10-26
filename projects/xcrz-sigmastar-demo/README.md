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

## 电机、构建与音频历史记录的复用边界（2026-10-20）

本节落实 Issue #176 的正文审读发现，只补充当前导航，不改写历史正文、
Registry、Owner、`review_after` 或生命周期，也不授予源项目写入、设备操作或发布权限。

### 电机保护：历史测试方案不是现行安全策略

[2026-05-29 电机 MCU 调试记录](archive/reports/2026-05-29-motor-mcu-debug-record.md)
描述的是 `0.2.0-20260527.hex` 阶段性测试，原文同时保留“1.3A 持续 3s”与
“持续偏大 10s”两种未固化口径，并明确 SoC 异常综合决策尚未实现。
**不得据此取消 MCU 本地保护，也不得把“上报 SoC”当作已经存在的安全兜底。**
复用前须由真实责任人核对当前 MCU/SoC 源码与固件、保护责任、通信失效处理及
温度、堵转、缺相的受控验证；本入口不选定电流或时间阈值，不提供运动测试命令。

### 构建权威：按范围和日期读取后续纠偏

[GROS 单轨候选及后续纠偏](decisions/gros-single-track-cross-platform-build-hard-cut-20260830-v1.md)
仅替代 HDI/HAL v4 的 `build-policy` 与 `gros-future-boundary` 范围，不废弃其分层、
profile 隔离和 HIL 要求。该文 2026-09-05 文首已废止历史 Python resolver / JSON
source-set 构建权威，改为原生 CMake；后面的 8 月实施记录仍保留旧图与阶段性失败。
当前命令必须从源项目的 `GROS.md` 与对应原生 CMake 说明重新取得，不能从旧段落
恢复 Make/Python 产品构建图。Host 测试或交叉链接不代表缺失 IoT、HIL、许可和签名已补齐。

### 音频链路：不得混用分支接口和实验条件

[AISpeech 源码分析与日期增补](archive/reports/2026-08-23-pcr02-aispeech-algorithm-source-analysis.md)
依次记录预编译静态审计、`dev/vad` 候选、后续 `master` 公共 AEC/BF/AES 与
NR 或 NN+AGC 尾链，以及最终公共头修订；它们不是同一时刻的运行事实。
不得恢复已弃用的 `AISP_AFE_*` 分支接口或私有 include，不得把历史 gain=1.6 录音
当作 gain=1.25 与当前 BuildID 的验证。文中资源数值的时间单位、NR-VAD 能力、
RTC 业务接入和已安装版本须回读当前源码及独立运行证据，不由本导航推定通过。

### IR 与 Diag：历史示例不得直接作为当前实现

[IR 优化计划](archive/plans/2026-05-08-irlight-optimization-plan.md) 的示例存在手动请求
未消费、ADC 中间区间未保持原状态以及通知不绕过计时间隔的问题；
[AOV 分析](validation/reports/2026-05-08-sigmastar-aov-lightsensor-analysis-report.md) 的
对比表与后文需求又把充电时的软／硬光敏选择写反。这些是历史文本与示例发现，
不是当前固件已复现的缺陷。本入口不选择光敏策略或阈值；实际改动须核对当前源码、
状态机、AE 统计量纲和硬件测量，不能直接复制旧代码。

[Diag 使用指南](current/runbooks/diag-usage-guide.md) 的下载循环只匹配 `state`，
没有完整核对进程退出码、`code/ret`、预期 size/hash，也没有总截止时间；信号处理
只请求取消并不保证循环退出。不能把该历史示例作为可直接运行的压测脚本。
复用前应验证有界等待、失败传播、取消完成、资源释放与实际制品身份。

[prog_tool 旧指南](current/runbooks/prog-tool-usage-guide.md) 的 `env expect=any`
只表示调用链有回复，不是业务成功；示例中的失败计数与成功字段存在不一致。
套件失败、零命令发现、跳过和功能通过必须分别报告。`local` 独立运行时不是
运行中业务进程；不得把远端 `unauthorized` 理解为已获切换本地执行的授权。

[V1 迁移报告](validation/reports/2026-05-07-v1-migration-final-report.md) 仍保留真实构建
失败，却把禁用格式检查计作已解决，并提出空头文件桩。不得用关闭门禁或伪造依赖
替代成功构建；“计划完成”“文件已复制”“终版发布”标题均不是运行或发布回执。
这些提示不改写历史正文，也不授权源项目写入、设备测试、保护阈值修改或发布。
