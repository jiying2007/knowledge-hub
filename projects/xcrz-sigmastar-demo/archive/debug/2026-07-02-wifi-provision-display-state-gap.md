---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-wifi-provision-display-state-gap-20260702
title: PCR02扫码配网显示状态机缺口分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-wifi-provision-display-state-gap.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f2106-845d-72a2-94f9-3de0e6fbcd7a
review_after: '2026-10-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- wifi
- qr-code
- display
- state-machine
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-wifi-provision-display-state-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-wifi-provision-display-state-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录扫码成功且WiFi已进入连接流程时界面仍停留扫码页的跨模块状态机缺口，以及sensor只做有限NETWORK_CONNECTING兜底、task或IOT负责业务编排的边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 扫码配网显示状态机缺口分析

## 现象

二维码已识别，WiFi service 已收到凭据并进入连接流程，设备随后也能达到联网状态，但 UI 仍停留在扫码页面，没有稳定显示“联网中”。

## 影响范围

- `QrScene`、Sensor WiFi service、display control、task/IOT 业务编排。
- 影响配网体验和状态可解释性，不等同于网络连接失败。
- task 源码在分析时不可见，因此最终业务 owner 仍待确认。

## 证据与时间线

| 阶段 | 观察 | 判断 |
| --- | --- | --- |
| 扫码 | 凭据发布到 `sensor/wifi/provision/info` | 二维码链路成功 |
| WiFi | service 接收凭据并发起连接 | 网络动作已开始 |
| Display | 未观察到确定的 `CMD_SET_NETWORK_STATE` 或关闭 QR scene | 显示状态未闭环 |
| 后续 | 网络状态可达到 connected | “一直扫码”不是网络未连接 |

`DisplayManager::switchToQrScene(false)` 能进入联网场景，问题在于缺少可靠的业务状态触发。provenance：`codex-raw-sessions:019f2106-845d-72a2-94f9-3de0e6fbcd7a`。

## 根因

扫码、WiFi 连接和显示是三条异步链路，缺少一个拥有明确 owner、幂等条件和终态收敛规则的配网显示状态机。task/IOT 事件偶发晚到、丢失或条件不满足时，二维码 scene 会继续刷新，因此表现为“概率性不切换”。

## 边界与规避

- task/IOT 应负责 `SCANNING → CONNECTING → SUCCESS/FAILURE` 业务编排。
- Sensor 不应接管成功/失败终态，否则会与 task/IOT 竞争。
- Sensor 可做有限兜底：仅在收到有效凭据、尚未 linked 且本轮尚未提示时发布一次 `NETWORK_CONNECTING`。
- 重复扫码、已联网、失败重试和 scene 重建必须有幂等/去抖规则。

历史会话记录 Sensor 模块和最终应用构建通过，但本轮没有复跑源项目；该证据只说明当时有限兜底能够编译，不代表 task 端状态机已经闭环。

## 验证矩阵

后续板测至少覆盖首次配网、重复扫码、连接中再次扫码、已联网扫码、错误密码、超时、重启恢复和 task 事件延迟，并记录显示状态与真实 WiFi 状态的对应关系。

```yaml
manual_validation_pending: true
manual_validation_reason: task源码不可见，最终状态编排owner和概率性场景尚未完成板级验证
required_followup: 对配网状态机执行故障注入和重复事件幂等测试
owner: leiwenjun
review_after: 2026-10-02
```

## 归档门禁

- Sanitization：未保留二维码内容、WiFi 凭据、端点或 raw 日志。
- Memory Candidate：no。
- Gate Result：`reviewing / owner-boundary-pending`。
