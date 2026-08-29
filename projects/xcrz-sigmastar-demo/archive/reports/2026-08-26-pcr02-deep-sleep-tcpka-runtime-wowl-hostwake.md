---
id: pcr02-deep-sleep-tcpka-runtime-wowl-hostwake-20260826
title: PCR02 DEEP_SLEEP TCPKA runtime WoWL host-wake 验证归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-08-26-pcr02-deep-sleep-tcpka-runtime-wowl-hostwake.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: code-and-hil-validation
  from: PCR02 source review, local build and board validation; raw logs, endpoints and device identifiers excluded
  source_sha256: ac66d17fa198c837a83165c9c2aafa43c59a3a6b2bc8a1625ecb38cc3c0a7a67
  temporary_source_retained: false
review_after: '2026-11-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- deep-sleep
- tcpka
- wowl
- bcmdhd
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-26-pcr02-deep-sleep-tcpka-runtime-wowl-hostwake.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-26-pcr02-deep-sleep-tcpka-runtime-wowl-hostwake.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-26'
updated_at: '2026-08-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-26'
manual_validation_pending: true
summary_zh: DEEP_SLEEP 保持 SoC 不进入 Linux system suspend，通过 TCPKA runtime offload 配置 Wi-Fi WoWL；补齐 host-sleep/bus 阶段后，板端验证 pin37
  与 MCU 唤醒链路恢复正常。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 DEEP_SLEEP TCPKA runtime WoWL host-wake 验证归档

## 结论

DEEP_SLEEP 不进入 Linux system suspend，而是由 MCU 在 TCPKA 交接后完成 SoC 物理掉电。要使 Wi-Fi 在该模式下仍能通过 host-wake GPIO 唤醒 MCU，runtime offload 必须完成两类配置：

1. STA WoWL 配置：TCPKA、pattern、`wowl`、`wowl_wakeind` 与省电参数；
2. WoWL host-sleep/bus 配置：`wowl_activate`、`hostsleep` 和 SDIO bus sleep。

仅执行第一类配置时，驱动会记录 WoWL 配置成功，但 pin37 不会表现出与 SLEEP 模式一致的 WoWL host-wake 行为。补齐第二类配置后，板端功能验证正常。

## 实现边界

- 保持 SoC 不进入 Linux system suspend，避免 PA8/RTC_IO1 与系统 wake 的竞争。
- 不调用完整 PM notifier 或完整系统 suspend 事务。
- runtime enable 顺序为：firmware suspend 设置、STA WoWL 设置、WoWL host-sleep/bus 设置。
- runtime disable 与失败回滚按反向顺序恢复。
- bus sleep 的返回值必须上传，禁止把 host-sleep 失败误报为 offload 成功。

## 验证结论

- DEEP_SLEEP 中 TCPKA runtime offload 成功；
- MCU 收到可靠 ARMED ACK 后执行 PA8 掉电时序；
- SoC 应用以正常退出语义结束，daemon 不重拉；
- 已确认板端 pin37、MCU Wi-Fi 唤醒路径和 SoC 唤醒功能正常。

## 风险与复核

- runtime bus sleep 必须在后续不再需要 Wi-Fi 控制命令的低功耗阶段使用；若低功耗 gate 需要继续发驱动命令，应拆为 offload 与 host-sleep 两阶段接口。
- 后续内核升级时需复核 `dhd_conf_suspend_resume_bus()` 内部 WoWL 语义与错误返回。
- 本归档不保留原始日志、网络端点、设备标识、二进制或现场数据。

## 证据来源

- PCR02 SoC、MCU 与 bcmdhd 源码审查；
- 本地构建与静态检查；
- 已确认的板端功能验证。
