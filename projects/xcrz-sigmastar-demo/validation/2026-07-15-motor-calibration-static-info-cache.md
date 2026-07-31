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
id: pcr02-motor-calibration-static-info-cache-20260715
title: PCR02电机标定静态信息缓存语义验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-15-motor-calibration-static-info-cache.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f64ba-488c-7000-816b-c9daf687344d
review_after: '2026-10-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- motor
- calibration
- static-info
- cache
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-15-motor-calibration-static-info-cache.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-15-motor-calibration-static-info-cache.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录read_ok与status_value分离、成功读取未标定结果也应缓存、只重试失败侧以及主动重标定时定向清除ready位的代码和构建验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02电机标定静态信息缓存语义验证
---

# PCR02 电机标定静态信息缓存语义验证

## 验证目标

确认静态信息服务能区分“读取成功但未标定”和“读取失败”，并避免已经得到权威结果的一侧电机被周期重复查询。

## 核心语义

- 左、右电机分别维护 ready 状态。
- `read_ok=true` 表示本次读取成功，与 `status_value` 是否为 0 无关。
- `status_value=0` 是权威的“未标定”，应缓存且停止重复查询。
- 某侧读取失败时只重试失败侧。
- 主动重新发起单侧标定时，仅清除目标侧 ready 位。
- 目标侧获得权威结果后立即结束 tracking。

## 历史证据

| Command | Exit Code | Result Summary | Evidence Path | Layer |
| --- | ---: | --- | --- | --- |
| 四组 pending mask 编译期断言 | 0 | 覆盖两侧未读、仅左已读、仅右已读、两侧已读。 | `codex-raw-sessions:019f64ba-488c-7000-816b-c9daf687344d` | Project |
| `rtk make modules/sensor_lib_all -j8 NC=1` | 0 | Sensor 模块历史构建通过。 | 同一 provenance | Project |
| `rtk make pcr02_app_all -j8 NC=1` | 0 | 最终应用历史链接通过。 | 同一 provenance | Project |
| `rtk git -C modules/sensor diff --check` | 0 | 历史 whitespace 门禁通过。 | 同一 provenance | Project |
| 设备启动/重标定复测 | not-run | 没有板级序列证据。 | none | Device |

## 结果矩阵

| case | 期望 | 代码证据 | 状态 |
| --- | --- | --- | --- |
| 两侧均未读取 | 查询 left + right | 编译期断言覆盖 | code pass |
| 左侧已成功读取 | 只查询 right | 编译期断言覆盖 | code pass |
| 右侧已成功读取 | 只查询 left | 编译期断言覆盖 | code pass |
| 两侧已成功读取 | 不再查询 | 编译期断言覆盖 | code pass |
| `read_ok=true,status=0` | 缓存未标定，不重试 | 源码语义覆盖 | device pending |
| 单侧主动重标定 | 只清除并查询目标侧 | 源码语义覆盖 | device pending |

## 结论

代码与历史构建证据为 `partial-pass`；设备启动、失败恢复和主动重标定仍待验证。该模式可复用于“读取质量”和“业务值”必须分离的其他静态数据。

```yaml
manual_validation_pending: true
manual_validation_reason: 需要设备启动和主动重标定复测
required_followup: 采集左右电机read_ok/status/query计数并验证单侧失败恢复
owner: leiwenjun
review_after: 2026-10-15
```

## 剩余风险

- MCU 重启或持久化状态外部变化时，缓存失效策略需明确。
- tracking timeout 与静态周期查询不得形成双重重试。
- 本文不保存设备标识、raw UART 日志或本机路径。
