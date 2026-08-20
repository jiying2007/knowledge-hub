---
id: xcrz-hdi-hal-diag-ai-mp4-hard-cut-final-review-20260814
title: HDI HAL Diag AI MP4 跨平台硬切最终复审
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-08-14-hdi-hal-diag-ai-mp4-hard-cut-final-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-final-review
  from: xcrz-sigmastar-demo repository final review 2026-08-14
  source_sha256: 4541742a2051d29fd094711db5584560970d3c0ff9164e12a99130f1b1cf364f
review_after: '2026-11-12'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- hdi
- hal
- diag
- ai
- mp4
- cross-platform
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-14-hdi-hal-diag-ai-mp4-hard-cut-final-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-14-hdi-hal-diag-ai-mp4-hard-cut-final-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-14'
updated_at: '2026-08-14'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-14'
manual_validation_pending: true
summary_zh: 跨平台 HDI/HAL/Diag 与 AI/MP4 源码硬切的最终决策、边界、验证证据和未认证 target fail-closed 状态。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 最终实现复审（2026-08-14）

## 结论

仓内实现复审 PASS，不留待办式优化项。AI、MP4 已由历史预编译/ABI 改写过渡链硬切为可审查源码模块；旧目录、样例、manifest、tool、test 均已删除并受 retired gate 防止复活。现有 Make 产品编译规则未改。

本结论不等于产品可发布：SSC305 的 signing/lifecycle/boot/update/anti-rollback/HIL，以及 SSU9383CM、RDK X5、RTOS 的 target identity/BSP 仍需对应 owner 提供真实输入。缺失时 product/RTOS gate 按设计 fail closed。

## 本轮关闭发现

| ID | Severity | Finding | Final resolution | Evidence |
|---|---|---|---|---|
| FR-08R | P1 | 无源码 AI/MP4 archive 需 objcopy 改写 OS 符号，属过渡设计 | 删除 ABI import manifest/tool/test；AI/MP4 源码直接调用 OSAL | architecture PASS; retired scan PASS |
| FR-10 | P1 | MP4 传入/传出时间单位分散换算 | 公共 packet/seek 合同统一为 us，file duration 为 ms，只在 MP4 内部转换 | Host record/read/seek contract + sanitizer |
| FR-11 | P1 | MP4 32-bit handle 暴露指针，x86_64 截断且 stale handle 不安全 | generation-tagged 32-bit opaque handle table，关闭后拒绝 stale handle | x86_64 normal + ASan/UBSan |
| FR-12 | P1 | AI 核心唤醒实现越层依赖 `hdi_os` | 迁移到 `voice/wakeup/wakeup_module`，直接依赖 OSAL，API 统一 `wakeup_module_*` | ARM full Werror build |
| FR-13 | P1 | AI Werror 被关闭，Eigen 上游警告与项目警告混合 | 启用项目 Werror；Eigen 作为 system include；所有项目警告清零 | `modules/ai_lib_all -B` PASS |
| FR-14 | P1 | WebSocket timer 对非 standard-layout class 做 `container_of` | 标准布局 timer wrapper + owner 指针 + static assertion | ARM Werror build |
| FR-15 | P1 | PIDNet 边界点循环最后一次访问 `i+1` 越界 | 循环条件改为 `i + 1 < size` | ARM Werror build |
| FR-16 | P2 | AI 只有 ARM/vendor 整体测试，PC 无法快速回归纯算法 | 增加 `host_ai_core` source set，partial-sort normal + ASan/UBSan | Host full gate PASS |
| FR-17 | P2 | `wakeup_test/qs` 样例、旧 MP4 头/静态/动态库可被误复用 | 删除整个旧路径，retired path gate 阻止重建 | architecture PASS |
| FR-18 | P2 | `pcr02` 仍打包旧 `libmp4.so` 并保留 `prog_tool` 残留 | `dep.mk` 改为 `modules/mp4`，删除旧动态库和已退役 bin | `pcr02_app_all -B` PASS |
| FR-19 | P1 | MP4 fast-realloc 新区间清零越界，失败时 allocation/pointer 可能失配 | 以旧 allocation 为清零起点，溢出前置拒绝，所有调用点以临时指针提交 | Host normal + ASan/UBSan |
| FR-20 | P1 | AI BEV 同时维护 `count_points` 与 vector size，可能越界序列化 | 删除冗余 count，唯一使用 vector size，并对 protobuf `int` 上限 fail closed | AI ARM full Werror |
| FR-21 | P1 | DVR consumer 仍保留 `/90`、`/16`、`/10` 与 HDI FPS 倍速换算 | 删除全部隐式单位换算；API 只传语义倍率，MP4 从 track 索引推导时间步长；进度计算防溢出 | API ARM full Werror + MP4 Host contract |
| FR-22 | P1 | MP4 C++ 链接、64 位字节序、CTTS v1、极值参数仍有未定义/截断风险 | public header 加 C linkage；统一安全时间缩放；64 位 BE 读取、CTTS v0/v1 和尺寸/FPS/时长边界 fail closed | header C11/C++17 + Host sanitizer + ARM Werror |
| FR-23 | P2 | AI 保留未使用兼容形参/旧线程名，`pcr02/dep.mk` 留待办和注释式候选项 | 删除兼容形参与旧命名；依赖清单只保留实际项，`addr2line` 明确绑定 backtrace owner | residue scan + AI/API/pcr02 rebuild |

## 最终边界

- APP → API → HDI → private backend → OSAL/SDK/driver；Diag 保持正交维护平面。
- AI 和 MP4 是源码模块，不是 `libs/3rdparty` ABI 修补物；产品 target 通过 `dep.mk` 显式选择。
- AI 的 MI/IPU/OpenCV/摄像头集成仍由 ARM/target 测试证明；Host 只运行已声明的平台中立源码集，不用 stub 伪装整个 AI 可运行。
- MP4 整个核心在 Host 直接编译，与 ARM 使用同一份代码。
- x86_64 Host 是永久开发 target，不引入 i386/`ARCH=x86` 别名。
- 未来 GROS 必须独立完成 target 等价验证后一次硬切；本次不保留 Make/GROS 双轨实现。

## 新鲜验证

- `architecture-check`：PASS，无 retired/runtime 残留。
- `generated-check`：PASS，Host AI source set 与派生 fragment 一致。
- architecture unit：17/17 PASS。
- `host_linux_x86_64-check`：PASS，包含 normal、ASan/UBSan、TSan、fuzz、Diag integration、HDI Fake、APP composition、MP4 source、AI core。
- AI ARM 全量 Werror：PASS；静态归档无旧 `wakeup_test` member，唤醒实现仅为 `wakeup_module.user.arm.o`。
- MP4 ARM 全量 Werror：PASS；Host normal + ASan/UBSan：PASS。
- API ARM 全量 Werror：PASS；DVR consumer 直接消费 MP4 us/ms/倍率合同。
- `pcr02_app_all -B`：PASS，旧 `libs/3rdparty/mp4` 删除后仍完成最终链接。
- `prog_pcr02` 产物审计：ARM32 ELF；内部 MP4 静态链接，无 `libmp4.so` NEEDED；AI archive 无旧 wakeup member。
- SSC305、SSU9383CM、RDK X5 product contract 与 RTOS contract：均以 `target-not-certified` 拒绝，精确绑定缺失的 `config/targets/<target>.json`，fail closed 符合设计。

## 未关闭的外部认证输入

| ID | Class | Exact blocker | Required authority/evidence |
|---|---|---|---|
| FB-03 | product certification | 缺 SSC305 certified target/signing/release/anti-rollback identity | platform/security/release owner |
| FB-04 | HIL | 缺 SSC305 boot/update/refusal/peripheral/HIL receipt | 实板环境与 owner 签核 |
| FB-05 | future targets | SSU9383CM、RDK X5、RTOS identity/BSP/product shape 未冻结 | 对应 target owner |

因此最终判定为：repository implementation PASS；product certification BLOCKED。两者不能混为“Host 通过即产品可发布”。

## 完成门禁核对

- Scope：Common/OSAL/HDI/API/APP/Diag、AI、MP4、7 个授权 consumer、`pcr02/dep.mk`、架构资产、测试与本文档；`app_sensor_test` 未修改。
- Claimant：Codex 声明 repository hard-cut 完成，不声明任何 product/RTOS 已认证。
- Verifier：完成验证门禁逐项核对构建、测试、产物、残留和 fail-closed 证据。
- Review status：未关闭 blocker/major/minor = 0/0/0；FR-08R、FR-10–FR-23 均已修复并复验。
- Breaking change：是。旧 HDI OS/Diag/MP4/wakeup 路径、符号及历史 MP4 时间单位被一次删除；所有仓内授权 consumer 同批迁移，不提供 shim、alias 或双轨。
- Rollback：仅通过 Git 恢复整批变更；禁止只恢复旧头、旧库或 ABI import 形成混合态。未执行 commit/push/merge/rebase。
- Retry audit：CTTS v0/v1 首次补丁因声明落入相邻函数被 Host/ARM 编译立即拒绝；定位精确行后修复，同一 Host/ARM 门禁复跑通过，未消耗完单路径 2 次 retry budget。
- Final gate：repository PASS；product/RTOS certification 保持 fail closed，责任人为对应 platform/security/release/HIL owner。

## Evidence Index

| Command | Exit | Result summary | Evidence path | Layer | Related artifact |
|---|---:|---|---|---|---|
| `make architecture-check generated-check header-compile-check host_linux_x86_64-check` | 0 | 架构、生成、头文件、17 tests、Host normal/sanitizer/TSan/fuzz/integration 全通过 | `out/host_linux_x86_64/bootstrap/` | Workflow | Host contract matrix |
| `make modules/ai_lib_all -B` | 0 | AI 双产物 ARM 全源码 Werror 通过 | `libs/arm/libs/glibc/11.1.0/static/libai.a` | Workflow | AI source module |
| `make modules/mp4_lib_all -B` | 0 | MP4 双产物 ARM 全源码 Werror 通过 | `libs/arm/libs/glibc/11.1.0/static/libmp4.a` | Workflow | MP4 source module |
| `make modules/api_lib_all -B` | 0 | API ARM 全源码 Werror 通过 | `libs/arm/libs/glibc/11.1.0/static/libapi.a` | Workflow | DVR consumer |
| `make pcr02_app_all -B` | 0 | SSC305 应用强制重编与最终链接通过 | `out/arm/app/prog_pcr02` | Workflow | product ELF |
| `file` / `readelf -d` / `ar t` 产物审计 | 0 | ARM32 ELF；无 `libmp4.so` NEEDED；无旧 wakeup member | `out/arm/app/prog_pcr02` | Agent | ELF/archive audit |
| root、AI、MP4 `git diff --check` | 0 | 无 whitespace/error marker | root、`modules/ai`、`modules/mp4` worktree | Agent | patch set |
| retired path `stat` 审计 | 1（预期） | 旧 MP4、wakeup_test、ABI import manifest/tool/test 均不存在 | `config/architecture/retired_identifiers.json` | Agent | hard-cut absence |
| 三个 `product-contract-check` | 2（预期） | 分别以缺失 certified target manifest 拒绝 | `config/targets/` | Workflow | product fail-closed gate |
| `rtos-contract-check TARGET=rtos_control` | 2（预期） | 以缺失 certified RTOS manifest 拒绝 | `config/targets/` | Workflow | RTOS fail-closed gate |
