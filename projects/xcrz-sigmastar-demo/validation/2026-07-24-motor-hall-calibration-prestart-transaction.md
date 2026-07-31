---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-motor-hall-calibration-prestart-transaction-20260724
title: PCR02电机Hall校准前置事务验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-24-motor-hall-calibration-prestart-transaction.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f93d1-d685-78d1-b6c3-c0f9ebb24564
review_after: '2026-10-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- motor
- hall-calibration
- product-test
- transaction
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-24-motor-hall-calibration-prestart-transaction.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-24-motor-hall-calibration-prestart-transaction.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录三个HallCalibration调用点统一执行ClearFault、Estop、HallCalibration，前置失败只记录诊断且不阻断校准的代码审计和联合构建证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02电机Hall校准前置事务验证
---

# PCR02 电机 Hall 校准前置事务验证

## 验证目标

确认所有实际调用 `VSAPPUART_SendMotorHallCalibration()` 的入口统一执行：

```text
ClearFault → Estop → HallCalibration
```

本条不证明前置命令在所有真实故障态下都能达到预期机械效果。

## 调用点覆盖

| 入口 | 目标 | 历史代码审计 |
| --- | --- | --- |
| `app_product_test` 首次与 timeout 重试 | `both` | 已覆盖 |
| `app_test motor_hall_calibration` | `left/right/both` | 已覆盖 |
| `app_uart_test motor_hall_calibration` | `left/right/both` | 已覆盖 |

三条命令使用同一个目标，避免清故障、急停和实际校准对象不一致。

## 失败语义

`ClearFault`、`Estop` 返回码只记录诊断；即使失败仍继续发送 HallCalibration。这是历史实现选择，不代表前置失败没有安全风险。板级验收必须确认 MCU 对故障态、急停态和校准准入的真实处理。

## 历史命令证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
| --- | ---: | --- | --- | --- |
| 全仓 HallCalibration 调用点检索 | 0 | 共 3 处，全部覆盖前置事务。 | `codex-raw-sessions:019f93d1-d685-78d1-b6c3-c0f9ebb24564` | Project |
| `app_test` / `app_product_test` diff check | 0 | 历史 whitespace 门禁通过。 | 同一 provenance | Project |
| `rtk make app_test_app_all app_product_test_app_all` | 0 | 两个应用历史联合构建通过。 | 同一 provenance | Project |
| left/right/both 板级故障态 | not-run | 无当前设备证据。 | none | Device |

## 结果矩阵

| case | 期望 | 当前状态 |
| --- | --- | --- |
| 正常、无故障 | 前置命令后进入目标校准 | device pending |
| ClearFault 失败 | 记录错误并继续，由 MCU 最终拒绝/接受 | device pending |
| Estop 失败 | 记录错误并继续，由 MCU 最终拒绝/接受 | device pending |
| left/right/both | 三条命令目标始终一致 | code pass |
| timeout 重试 | 重试仍执行完整前置事务 | code pass |

## 结论

调用点和历史构建证据为 `partial-pass`；安全行为、目标一致性和失败态仍需板级验证。本文不授权把“忽略前置返回码”提升为团队通用规则。

```yaml
manual_validation_pending: true
manual_validation_reason: 需要板级确认left、right、both目标与故障态行为
required_followup: 对正常、ClearFault失败、Estop失败和timeout重试执行板级矩阵
owner: leiwenjun
review_after: 2026-10-24
```

## 剩余风险

- 前置命令无 ACK 或延迟生效时，固定顺序不等于物理状态已稳定。
- 后续可评估是否需要有界 ACK/settle gate；任何改变都必须重新验证产测节拍。
