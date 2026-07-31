---
id: pcr02-app-sensor-test-v3-hard-cut-20260731
title: PCR02 Sensor 测试框架 v3 硬切换验证记录
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-v3-hard-cut.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz_sigmastar_demo
  source_sha256: 404acd60d643a90d8d1765f3d439602ab8a85d132efc7082edeadb8ab4a4b699
review_after: '2026-08-14'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- sensor
- validation
- stress
- hard-cut
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-v3-hard-cut.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-v3-hard-cut.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: app_sensor_test 已完成 v3 单轨硬切换、分层去耦、22 个板端 case、durable JSONL、逐操作 deadline、独立 cleanup budget、host/sanitizer/coverage
  与 ARM 构建；TSan 环境和板端 HIL 仍待闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Sensor 测试框架 v3 硬切换验证记录
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# app_sensor_test v3 独立审查报告

审查日期：2026-07-31。

## 1. 审查结论

代码级审查结论为：

- blocker：0
- major：0
- minor：0 个未处置代码缺陷
- 外部验证缺口：2 个，分别是 TSan 运行环境和板端/HIL evidence

该结论只覆盖 app_sensor_test v3 框架、host 可执行逻辑、交叉构建和静态架构门禁，
不等价于 Sensor 全硬件能力通过。

## 2. 审查范围

- `application/`：CLI 到单次 plan、fixture、runner、evidence、exit code 的编排。
- `framework/`：显式 metadata、selection、参数、risk、deadline、JSONL、durability。
- `cases/`：22 个 executor、协议负向、stream/media、stress/soak、terminal cleanup。
- `runtime/`：中立 ports、SigmaStar adapter、资源探针、Deep Sleep callback 状态机。
- `tests/`：contract、white-box、unit、fake board、architecture、sanitizer、coverage。
- 文档：目标边界、测试矩阵、恢复点、设备/HIL 放大门禁。

## 3. 审查发现与闭环

| ID | 原级别 | 发现 | 处置与证据 |
| --- | --- | --- | --- |
| R1 | major | case deadline 未传入 req/rep 与 feature operation，单次 transport 可越过总预算 | port 显式接收 timeout；每次 operation 传 remaining budget；Deep Sleep 多阶段共享 `OperationBudget` |
| R2 | major | 执行 deadline 耗尽后 cleanup 获得 0ms，恢复调用实际会被 adapter 拒绝 | `CaseSpec::cleanup_timeout_ms` 成为 catalog/evidence 字段；恢复使用独立 5s `CleanupBudget`，多步骤共享预算 |
| R3 | major | Deep Sleep callbacks 捕获栈对象且未清理，失败返回后存在悬空回调风险 | callback 捕获 `shared_ptr<DeepSleepCoordinator>`；RAII session 在所有返回路径清空模块 callbacks |
| R4 | major | 未授权 case 携带自身参数时被误判为未知参数，无法形成预期 skip | 已提供参数按完整 selection 校验；required 参数只按已授权 case 校验；增加回归测试 |
| R5 | major | stress 部分完成未区分 run-duration deadline 与 case timeout，可能把 case timeout 当正常完成 | invocation 记录 deadline 来源；只有 duration limit 可接受部分 operation，case timeout 强制 fail |
| R6 | major | exception、evidence callback、cleanup 失败的退出语义可能丢失 | executor exception 转 evidence error result；write/finalize 错误返回 70；cleanup failure 降级为 fail |
| R7 | minor | `/proc/self/status` 只检查 thread，RSS/HWM 缺失时仍可能生成零值指标 | RSS、peak RSS、thread 三项都必须成功解析 |
| R8 | maintainability | SigmaStar adapter 接近 500 行上限且混有 callback/ACK 职责 | 拆出 `DeepSleepCoordinator` 和 `device_control_ack`，最大 production cpp 降至 469 行 |

## 4. 验证证据

| Gate | 结果 |
| --- | --- |
| clean host check（9 binaries） | PASS |
| ASan + UBSan（9 binaries） | PASS |
| production line coverage | PASS，80.54%（1391/1727），门槛75% |
| architecture hard-cut/dependency/size | PASS |
| ARM `app_sensor_test_app_all` | PASS |
| ThreadSanitizer | 环境缺口：GNU linker 缺少 `libtsan_preinit.o`，未运行到测试 |

最终 ARM 编译产物：

- path：`out/arm/app/prog_sensor_test`
- type：ARM EABI5、动态链接、含 debug_info、not stripped
- size：85555708 bytes
- BuildID：`2105de1e3c2d7543cf3e6f5f293ffa730cc143d2`
- SHA-256：`dccb1f34465ce2fbe433151b728379d142232f5bd525aedbfa4a48ee5c77198b`
- MD5：`78f1fc9ed742ca26d76ae49c9a484cbb`

## 5. 外部验证与治理边界

1. 当前没有指定板卡、installed artifact、ADB/串口或仪器上下文，因此没有执行 board
   smoke、5～10 次短循环、1000 次长循环、soak 或 destructive/HIL；不得据此宣称
   Sensor 硬件全面通过。
2. 外层仓库当前把整个 `app_sensor_test/` 显示为 untracked。代码和门禁已形成长期资产，
   但仍需 owner review 后显式纳入版本控制；本次未自动 stage/commit。
3. capability matrix 中 IR、Laser、Display、Audio-out、QR、DVR、OTA、motor motion、
   reboot/shutdown/wake 与 concurrency HIL 仍是后续板端能力扩展，不伪装成已验证能力。
