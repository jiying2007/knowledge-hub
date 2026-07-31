---
id: pcr02-player-monotonic-sync-validation-20260729
title: PCR02 player 单调时钟与请求确认优化验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/reports/2026-07-29-player-monotonic-sync-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: engineering-session
  from: current Codex engineering session, user-provided boot log, and local repository diff
  source_sha256: 1279d1ddb463df2cccd13b44d3b6ba5c83c0fcb1b5856c99979e1a451bffc5aa
  temporary_source_retained: false
review_after: '2026-10-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- player
- semaphore
- monotonic-clock
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/reports/2026-07-29-player-monotonic-sync-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/reports/2026-07-29-player-monotonic-sync-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录 PCR02 启动校时导致 player semaphore 误超时的修复候选：单调时钟、请求 ID 完成确认、超时故障态与上层 fail-closed；当前只有构建和 host smoke 证据，设备 HIL 待补。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 player 单调时钟与请求确认优化验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 player 单调时钟与请求确认优化验证

## 问题与根因

- 设备启动早期系统墙上时间从 1970 跳到 2026，基于 `CLOCK_REALTIME` 的 semaphore/condition 有限等待可能立即超时。
- player 原实现用共享 semaphore 表示多类状态确认，迟到信号可能被后续命令消费，无法确认信号属于哪次 START/STOP。
- Wi-Fi `os_net_sem_wait` 同样使用 `CLOCK_REALTIME + sem_timedwait`，并把毫秒余数乘以 `1000` 而不是 `1000000`，会把亚秒超时缩短约 1000 倍。

## 实现候选

- HDI semaphore/condition 的有限等待改用 `CLOCK_MONOTONIC`；condition 创建时绑定单调时钟。
- player 用串行 command mutex、递增 request ID 和 completion condition variable 配对请求与真实完成事件。
- START 只在 open 完成后确认，STOP 只在 close 完成后确认；同步失败后 player 进入 faulted 状态并执行受控停止。
- 已超时请求被标记为放弃，迟到消息不再改变状态；sensor 在旧播放停止失败时拒绝启动新文件。
- Wi-Fi semaphore 改用 `sem_clockwait(CLOCK_MONOTONIC)`，补齐纳秒换算、进位和 `EINTR` 重试。

## 验证证据

- `modules/hdi_obj_all`、`modules/api_obj_all`、`modules/sensor_obj_all`、`modules/wifi_obj_all` 构建通过。
- 对应四个静态库重建后，`pcr02_app_all` 链接通过。
- ARM ELF 包含 `_PLAYER_WaitRequest`、`VSHDIOS_SemLockTimeout`、`os_net_sem_wait`，并引用 `sem_clockwait@GLIBC_2.30` 和 `pthread_condattr_setclock@GLIBC_2.4`。
- Host smoke 中 120 ms Wi-Fi semaphore 无信号等待实测为 120 ms。

## 未闭环

- 尚未部署设备执行启动校时并发场景、快速连续语音替换循环和长时间 HIL；候选只可作为待板级复核的 validation 记录。
