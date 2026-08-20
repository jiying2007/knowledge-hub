---
doc_type: architecture-decision
decision_id: pcr02-osal-platform-hdi-boundary-20260817-v1
supersedes_sections:
- pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4/3.2
- pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4/4
- pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4/4.2
updated: 2026-08-17
build_policy: current Make remains the sole build authority
id: xcrz-osal-platform-hdi-final-boundary-20260817
title: OSAL Platform HDI 终版边界与硬切验证
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/osal-platform-hdi-final-boundary-20260817.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: repository-document
  from: xcrz-sigmastar-demo/docs/architecture/osal-platform-hdi-final-architecture.md
  source_sha256: d3494e9cc52d9522d7e668dde597e6a045ff16828018db77ef89f376af339df2
review_after: '2026-09-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- osal
- platform
- hdi
- cross-platform
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/osal-platform-hdi-final-boundary-20260817.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/osal-platform-hdi-final-boundary-20260817.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-17'
updated_at: '2026-08-17'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-17'
manual_validation_pending: true
summary_zh: OSAL、Platform、HDI 三域终版边界，包含无兼容硬切、Host/ARM 验证与产品认证 fail-closed 边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- OSAL Platform HDI 终版边界与硬切验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# OSAL / Platform / HDI 终版边界

## 1. 定案

OSAL、Platform、HDI 是三个同级职责域，不把 OSAL 或 Platform 放进 HDI，也不把 Platform 放进 OSAL。唯一允许的依赖方向是：

```text
APP composition ────────┬──> API ──> HDI facade ──> private HAL backend ──> SDK/driver
                        ├──> Platform services ──> OSAL core ──> OS/RTOS primitives
                        └──> OSAL lifecycle

HDI implementation ─────────> Platform services / OSAL primitives（按需）
HDI implementation -X-------> OSAL lifecycle ownership
OSAL -X----------------------> Platform / HDI / API / APP
Platform -X------------------> HDI / API / APP
```

HDI 可以使用线程、同步、时间或平台进程/环境服务来实现硬件语义，但不能初始化或反初始化 OSAL，不能通过 HDI capability 决定内存池策略。OSAL 生命周期和 HDI 生命周期由 composition root 按 `OSAL → HDI` 初始化、`HDI → OSAL` 反初始化，并负责失败回滚。

## 2. 稳定接口

### 2.1 OSAL

- `include/osal/osal_core.h` 仅聚合强制可移植原语：lifecycle、memory、sync、thread、time、atomic、log。
- 对应窄头为 `osal_lifecycle.h`、`osal_memory.h`、`osal_sync.h`、`osal_thread.h`、`osal_time.h`、`osal_atomic.h`、`osal_log.h` 和 `osal_types.h`。
- calendar、observe、task、thread pool 位于 `include/osal/ext/`；target 不需要时可不编译、不暴露。
- 已删除 `include/osal/osal.h` 和旧 `include/osal/osal_task.h`，不提供转发头或 alias。
- POSIX 实现在 `modules/osal/posix`；RTOS 必须实现同一核心契约，可按 profile 选择扩展。

### 2.2 Platform

- 公共能力位于 `include/platform`，实现和独立制品位于 `modules/platform` / `libplatform`。
- filesystem、dynamic library、environment、power 是独立 typed contract。
- shell/process 执行只对仓内受控 adapter 开放，接口位于 `modules/platform/include/private`，不成为通用公共 API。
- 已删除混合职责的 `platform_system.h`；power、environment、process 分开，不留兼容包装。

### 2.3 HDI / private HAL

- HDI 只表达硬件领域语义、资源所有权、能力和后端状态。
- `VSHDI_Init(void)` 只启动编译期选定 backend；重复调用幂等，失败进入 idle 或 cleanup-required。
- `VSHDI_RuntimeInfo_t` 只暴露 backend identity、硬件 capabilities 和 `bInitialized`；runtime ABI major 为 2。
- OS core、memory pool 和 POSIX device I/O 不再是 HDI capability；相关 init flag、mask 和 active flags 全部删除。
- HAL backend 保持 HDI 私有；SSC305、SSU9383CM、RDK X5、host_fake、RTOS/AMP 各自独立，单 target 只链接一个 backend。

## 3. 平台组合与 Host

- `VSAPPCOMPOSITION_PlatformConfig_t` ABI major 为 2，只保留 OSAL 内存池策略；SoC system 不再是可关闭的组合选项。
- ARM 默认启用现有内存池，Host manifest/测试显式关闭；这是 target 配置，不是 HDI capability 猜测。
- Host source set 将 `host_posix_osal`、`host_posix_platform`、`host_hdi_facade` 分开；HDI source set 不依赖 OSAL。
- PC 覆盖 OSAL、Platform、HDI fake、composition、API/APP 逻辑、并发、回滚和 sanitizer；不替代芯片 SDK、驱动时序、媒体质量和 HIL。
- 当前 Make 继续是唯一构建 SSOT；未来 GROS 直接映射这些 source set 和依赖，不保留 Make/GROS 双产品轨。

## 4. 硬切与长期门禁

以下旧资产是阻断项：`osal.h`、旧 `osal_task.h`、`platform_system.h`、`modules/osal/posix/services`、`VSHDI_INIT_FLAG_OS_CORE`、`VSHDI_INIT_FLAG_MEMORY_POOL`、`VSPLATSYS_ExecuteCommand*`。

长期自动化要求：

- OSAL 禁止依赖 Platform/HDI/API/APP；Platform 禁止依赖 HDI/API/APP。
- HDI 禁止调用 `VSOSAL_CoreInit/DeInit`。
- HDI/API/APP/Platform 公共头禁止泄漏 OSAL 类型和头。
- 所有 public header 独立通过 C11/C++17 编译，不暴露 POSIX/Linux/vendor SDK 类型。
- manifest/generated fragment 无漂移；Host 普通、ASan/UBSan、TSan、fuzz 合同通过。
- SSC305 ARM 库和所有已授权 consumer 必须编译链接通过；产品发布仍需独立 target identity、HIL 和 release receipt。

## 5. 非目标与无残留声明

- 不提供旧 API 兼容层、deprecated 宏、双签名 `VSHDI_Init`、路径转发头或 runtime fallback。
- 不把 Host fake 结果冒充 SSC305、SSU9383CM、RDK X5 或 RTOS 认证。
- 不在本次变更中引入 GROS 语法或第二套构建规则。
- SSU9383CM、RDK X5 和 RTOS 的 backend 实现仍由各 target 项目在本边界内落地；这不是本架构的过渡设计。

## 6. 可恢复执行契约

- goal_statement：完成 OSAL/Platform/HDI 终版硬切、consumer 迁移、自动化门禁和长期资产沉淀。
- completion_claim：仓内实现、Host/ARM 编译、架构门禁和文档闭环；不包含未提供的目标板 HIL/发布认证。
- claimant：Codex。
- verifier：自动化门禁与最终代码复审；产品认证由 platform/release owner 完成。
- retry_budget：同一失败路径最多 2 次。
- evidence_stale_after：源码、manifest、toolchain 或 binary identity 变化立即失效；其余 24 小时。
- stop_conditions：旧标识残留、门禁失败、consumer 链接失败或未授权范围发生重叠时不得声明完成。
