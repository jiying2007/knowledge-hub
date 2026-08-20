---
doc_type: architecture-review
review_id: pcr02-hdi-hal-cross-platform-host-development-review-20260813-v2
supersedes_candidate: pcr02-hdi-hal-cross-platform-host-development-review-20260813
reviewed_document: docs/architecture/cross-platform-hdi-hal-host-development-plan.md
related_document: docs/architecture/diag-observability-maintenance-plane.md
related_review: docs/architecture/diag-observability-maintenance-plane-review.md
reviewer: Codex
review_date: 2026-08-13
owner_approval: pending
id: pcr02-hdi-hal-cross-platform-host-development-review-20260813-v2
title: HDI/HAL 跨平台与 Host 开发测试方案审查记录 v2
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/hdi-hal-cross-platform-host-development-review-20260813-v2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: separated design review with repository static evidence
  source_sha256: d87cd631c471ec726351b343fd8b7fc07723fbdd5b256a9838d8db185890542a
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi
- hal
- architecture-review
- diag
- security-review
- cross-platform
- host-test
- rtos
validation_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-cross-platform-host-development-review-20260813-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-cross-platform-host-development-review-20260813-v2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: v2 独立审查总体跨平台方案及 Diag 专项扩展；已闭环原有三项 major、Diag 五项 major 和一项资产 minor，最终 blocker/major/minor 均为零，owner approval 仍待关闭。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL 跨平台与 Host 开发测试方案审查记录 v2
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI/HAL 跨平台与 Host 开发测试方案审查报告

## 1. 审查结论

裁决：PASS，可作为 Knowledge Hub 的 reviewing decision candidate 归档。Diag、Observability 与 Maintenance 平面已作为强制组成部分完成独立安全复审，不再作为后续可选优化。

最终分级：

- blocker：0；
- major：0；
- minor：0；
- question：平台基础输入 5 个、Diag owner approval 5 类，均已标记为实施前置条件并默认 fail closed；
- out-of-scope：代码实现、构建迁移、交叉编译、Host 测试和 HIL。

此 PASS 仅说明方案的边界、决策、迁移顺序、验证和回滚足以进入 owner review。v2 候选替代旧版作为最新审查入口，但旧候选的 lifecycle 状态仍需按 Knowledge Hub 授权与 attestation 门禁单独处理。它不代表任何平台功能已经实现、测试通过、可发布或获得 owner 批准。

## 2. 审查范围

审查对象：

- HDI、internal HAL、API、APP、OSAL 的职责与依赖方向；
- SSC305、SSU9383CM、RDK X5、Linux x86_64 Host 和 future RTOS 的覆盖；
- 当前构建冻结与未来 GROS 迁移边界；
- HDI contract、capability、board manifest、Host Fake、RTOS profile；
- Diag 公共 contract、runtime、adapter、transport/auth、维护用例与 provider 生命周期；
- permission/effect/profile/capability 策略、pre-intent audit、operation journal、资源预算和 RTOS static catalog；
- P0–P10 与 D0–D8 的迁移、验收、回滚和证据治理；
- 方案与当前仓库静态证据的一致性。

未审查：

- 未实现代码的运行行为；
- 未获得的 SDK/BSP、GROS 规格和实板能力；
- 产品性能、图像质量、RTOS 时序和量产包。

## 3. 第一轮发现与修复

### F-001：RTOS 与 GROS 被绑定在同一迁移包

- severity：major
- type：migration-risk
- evidence：初稿 P8 同时要求 RTOS backend/RPC/共享内存和 GROS 双轨迁移，两个高风险维度会使失败无法归因。
- impact：RTOS 功能问题与构建系统问题耦合，扩大回滚面，并违反单变量迁移原则。
- resolution：fixed
- fix：拆分为 P8 RTOS profile 和 P9 GROS 双轨迁移；P9 禁止同时改变 HDI contract 或目录布局，RTOS 是否同批进入由 P8 结果单独决定。
- verification：第二轮检查确认 P8/P9 各有独立前置、验收和回滚。

### F-002：板级信息移出公开头后缺少明确归属

- severity：major
- type：architecture-gap
- evidence：初稿识别了 GPIO 和板级宏泄漏，但只写“不得公开”，没有定义 GPIO、设备节点、sensor bus、IQ/校准路径和分区的承载与信任边界。
- impact：实施时可能把差异重新塞入 APP、环境变量或散落条件编译，削弱 HDI/HAL 分层并引入不可信路径风险。
- resolution：fixed
- fix：新增 Board manifest 与 capability 的边界，定义 schema/version、board identity、backend 验证、Host fixture、allowlist 和 HIL 规则。
- verification：第二轮确认 manifest 描述连接事实，capability 描述验证后的能力，职责不再混用。

### F-003：分层原则缺少持续执行门禁

- severity：major
- type：regression-risk
- evidence：初稿定义了依赖方向，但没有规定如何阻止 MI/RDK/pthread、ARM 库和直接 HDI 调用重新进入公共层。
- impact：迁移后架构可能随日常修改快速退化，Host target 也可能误收生产后端或 ARM-only 库。
- resolution：fixed
- fix：新增 public-header、dependency、source-set、symbol/dependency、contract-version 与 exception-budget 六类门禁，并采用 report-only 到 blocking 的渐进策略。
- verification：第二轮确认门禁不改变当前 P0/P1 产品构建，P2 起按迁移域启用。

## 4. 第二轮复审

### 4.1 Correctness

- 当前事实与直接仓库查询一致：ARCH=x86 只是本机编译分支，没有 i386 保证。
- POSIX 类型和厂商依赖泄漏有明确文件证据。
- ARM-only 动态库风险经 ELF 类型检查确认。
- 对 SSU9383CM、RDK X5 和 RTOS 未证事实均保持待确认，没有把历史材料升级为当前产品事实。

结果：pass。

### 4.2 Architecture

- 依赖方向单向且有例外边界。
- HDI 是稳定语义 facade，HAL backend 保持私有和可静态组合。
- OSAL core 与文件/进程/网络等平台服务分离。
- capability、board manifest、build selection 三者职责分离。
- Host Fake 与真实 backend 的证据等级区分清楚。

结果：pass。

### 4.3 Compatibility

- P0/P1 不修改根 Makefile、build/*.mk、lib.mk 或产品链接。
- x86_64 为首个 Host 目标，i386 不被误承诺。
- VS_HANDLE/VS_ID 明确禁止承载指针。
- wire/persist 结构不依赖本机 ABI。
- GROS 只冻结目标模型，不虚构 DSL。

结果：pass。

### 4.4 Testability

- Host 支持等级 L0–L4 清晰。
- Fake 有虚拟时钟、事件队列、故障脚本和资源账本。
- contract suite、sanitizer、HIL 和负面场景齐备。
- Fake 不能替代真机的限制被明确写入验收。

结果：pass。

### 4.5 Security and data governance

- board manifest 使用 schema、校验和 allowlist。
- 外部字符串不得直接进入 shell、driver 或动态加载器。
- 归档排除 raw session、日志、二进制、媒体和 credential。
- reviewing 不等同 owner approval。

结果：pass。

### 4.6 Maintainability and rollback

- P0–P10 每包有范围、验收和回滚，Diag D0–D8 已映射为强制横切工作流。
- 先建 seam 再搬实现，不同时重构目录、接口和构建。
- 单域 feature/adapter 和平台 target 提供回退边界。
- 构建回退不要求回退稳定 HDI contract。
- command/policy/limits/aliases 使用 versioned manifest 作为 SSOT，生成物携带 source hash 并禁止手改。

结果：pass。

## 5. Diag 平面范围扩展复审

专项报告对当前 include/common/diag 与 modules/app/src/app_diag 的 contract/runtime 混放、JSON/OS 绑定、直接 handler 调用、provider 生命周期和非只读命令进行了真实性核验。

第一轮共确认并修复 5 个 major：

- F-D01：将 immutable catalog snapshot 与 READY generation invocation lease 分离，cleanup 等待 snapshot epoch 和 active lease 同时清零；
- F-D02：高风险副作用前必须 durable intent audit，完成后写 completion audit；失败进入可见恢复状态，不伪造 rollback；
- F-D03：HDI adapter 只保留 typed observe，self-test 和 mutation 必须经 API/APP domain use case；
- F-D04：role 与 permission 解耦，descriptor 使用 required_permissions，不存在隐式角色等级；
- F-D05：新增 operation journal、recovery policy、MANUAL_RECOVERY、重启恢复和 bounded failure containment。

另修复 1 个长期资产 minor：command/policy/limits/aliases 的 JSON manifest 是 SSOT，C catalog、文档和 golden vectors 是带 source hash 的生成物。

复审结果：blocker=0、major=0、minor=0。详细证据见 docs/architecture/diag-observability-maintenance-plane-review.md。owner 未批准 principal trust、permission mapping、profile catalog、target limits、durable sink/journal 和兼容移除前，对应能力不得启用。

## 6. Open questions

### Q-001

- question：SSU9383CM 的正式 BSP/SDK、板型、sensor 和 Linux/RTOS 核间拓扑是什么？
- owner：SSU9383CM platform owner
- blocks：P6、P8

### Q-002

- question：RDK X5 项目最终批准的 BSP、板型、camera、DDR、eMMC 和 Wi-Fi 组合是什么？
- owner：RDK X5 platform owner
- blocks：P7

### Q-003

- question：RTOS 采用单芯、rtos_control 还是 amp_proxy？
- owner：system architect
- blocks：P8

### Q-004

- question：GROS 的正式规格、toolchain、依赖锁定和产物模型是什么？
- owner：build owner
- blocks：P9

### Q-005

- question：公共 C ABI 兼容政策和 Host 原生依赖白名单是什么？
- owner：team-core
- blocks：P2/P3 的 ABI 发布与 P1 的依赖准入

## 7. 验证证据

- build/mi_dep.mk 直接查询命中 ARCH=x86、gcc 和 g++。
- include/hdi/hdi_os.h 直接查询命中 pthread、semaphore、unistd 和 Linux system headers。
- include/api/api_video.h、api_zmq.h 直接查询命中 HDI include 和 pthread 同步类型。
- include/common/vs_type.h 直接查询确认 VS_HANDLE/VS_ID 为 VS_U32。
- modules/hdi/src/hdi_hw/hdi_sys.c 直接查询命中 mi_sys.h。
- include/common/diag/diag_types.h 直接查询命中固定 JSON reply、layer enum、字符串 handler 和指针字段；diag_provider.h/diag_contract.h 的全局 contract 由 APP runtime 实现。
- app_diag_dispatcher.c 直接查询确认 lookup 后调用 handler；已检查路径未发现 permission/effect/deadline/audit 中央门禁。此证据不等于已证明外部可利用漏洞。
- app_diag_registry.c 直接查询确认 atomic_flag busy spin 与裸 handler 生命周期风险；provider 命令直接查询命中 volume/gain、采集启停、format、SN、motor、OTA、reboot 等非只读操作。
- file -L 检查 spdlog、fmt、protobuf-lite、zmq 均为 32 位 ARM EABI5。
- 主方案和 Diag 专项规范修复后逐节复读，旧 P8 耦合标题、P0–P8 表述、required_role 和 DG-01 至 DG-16 旧范围已消除。
- 不可靠的 wrapper 管道计数曾返回与直接查询矛盾的零值，已作为负面证据排除，未进入事实结论。

## 8. 工作区与回归边界

- 本轮只新增或更新 docs/architecture 下的方案、Diag 专项规范和审查文档。
- 仓库现有 .gitignore 第 37 行忽略整个 docs 目录，因此这些文件是本地审查源，不会出现在普通 git status 中；本轮不修改 .gitignore，耐久副本以 Knowledge Hub reviewing candidate 为准。
- 未修改根 Makefile、build/*.mk、lib.mk、HDI/API/APP 源码或三方库。
- 工作区开始时已存在 pcr02/dep.mk 修改和多个未跟踪目录；这些属于既有用户状态，本轮未覆盖、清理或回退。
- 因无代码和构建变更，本轮不以产品 build/test 作为方案审查证据；AC-I1–AC-I12、AC-D1–AC-D10 与 DG-01–DG-18 才是实现级验证门禁。

## 9. 最终裁决

blocker、major 和 minor 已清零。总体方案与 Diag 专项规范可按 status=reviewing、owner_approval=pending 归档为决策候选；在 owner 关闭 Q-001 至 Q-005 及 Diag approval inputs 前，不得提升为 active，也不得据此声明对应平台或诊断能力已支持。
