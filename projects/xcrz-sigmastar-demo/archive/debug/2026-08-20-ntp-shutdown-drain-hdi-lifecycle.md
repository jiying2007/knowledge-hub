---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-ntp-shutdown-drain-hdi-lifecycle-20260820
title: PCR02 NTP shutdown drain 与 HDI 生命周期修复
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-ntp-shutdown-drain-hdi-lifecycle.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-09-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug-record
- knowledge-new
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-ntp-shutdown-drain-hdi-lifecycle.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-20-ntp-shutdown-drain-hdi-lifecycle.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-20'
updated_at: '2026-08-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-20'
manual_validation_pending: true
summary_zh: detached NTP worker 超时返回后仍可能使用 HDI；采用原子 shutdown+引用计数 drain，并在未排空时保留 HDI 至进程退出。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 NTP shutdown drain 与 HDI 生命周期修复

## 现象

恢复出厂或 SOC 重启期间，WiFi Tick 正在进行并行 NTP 校时时，旧实现需要等待网络 worker，曾出现 Sensor 反初始化耗时约 18 秒。将 worker 改为 detached 并设置总超时后，调用方可以快速返回，但后台 worker 仍可能继续执行 DNS 或 socket 操作。

## 影响范围

适用于 `xcrz-sigmastar-demo` 的 API WiFi/NTP、Tick 与 Sensor shutdown 链路。风险集中在进程完整反初始化后触发 SOC 重启的路径。

## 环境

SigmaStar SSC305 ARM Linux；API 与 Sensor 为独立仓库。API C 层并发原语必须使用 `VSHDIOS_Atomic*`、mutex 和 condvar 接口。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-08-20 | 日志定位 `VSAPITICK_Set Invalid tick ID` 与 NTP worker 慢 | Tick 回调和反初始化存在竞态 |
| 2026-08-20 | detached worker 方案代码审查 | 发现 worker 可能跨越 `VSHDI_DeInit()` 生命周期 |
| 2026-08-20 | 引入 shutdown admission、引用计数 drain 与 Sensor preservation | 本地三层构建通过，待实机循环 |

## 证据

- `rtk make modules/api_obj_all -j20`：通过。
- `rtk make modules/api_lib_all -j20`：通过。
- `rtk make modules/sensor_obj_all -j20`：通过。
- `rtk make modules/sensor_lib_all -j20`：通过。
- `rtk make pcr02_app_all -j20`：通过。
- `rtk bash build/check_public_headers.sh --root "$PWD" api`：通过。
- 原始现场日志未归档，仅保留问题摘要。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| Tick ID 已销毁后回调再次 Set | 增加 shutdown fence，并让 Destroy 等待活动回调 | 本地构建和静态链路通过 | 已处理 |
| detached NTP worker 跨越 HDI deinit | 检查 `VSHDI_DeInit()` 会反初始化 atomic/memory pool | 风险成立 | 已处理 |
| bounded drain 足以保证所有 DNS worker 退出 | DNS 可能超过 drain grace | 假设不成立 | 已否定 |

## 根因

NTP Tick 回调与 shutdown 缺少统一生命周期栅栏。detached worker 超时返回只限制调用方耗时，不能证明 worker 已退出；若随后反初始化 HDI atomic/memory pool，后台 worker 可能访问已销毁依赖。

## 修复或规避

- NTP 使用单个 HDI 原子状态字，高位表示 shutdown，低位表示活动调用引用；CAS 线性化新请求准入。
- 直接 NTP、并行调度主调用和 worker 都纳入 drain 引用计数。
- WiFi shutdown 设置栅栏并最多等待 200 ms；仍有阻塞 worker 时返回 busy。
- Sensor 在最终 drain 仍 busy 时跳过 API/HDI teardown，保留依赖到进程退出，由 SOC reboot/OS 回收。
- Tick callback 记录执行线程 PID；回调内 Destroy 改为 deferred self-destroy，回调返回后清理，避免自等待死锁。

## 验证

本地公共头同步、API/Sensor/App 构建、SOC reboot 静态检查和 API 分层检查均通过。最终制品包含 WiFi PrepareShutdown、NTP drain、Tick Destroy 与 Sensor preservation 符号。当前无 ADB endpoint，恢复出厂 5～10 次短循环和 1000 次长循环尚未执行，因此条目保持 `reviewing`。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason: 当前会话没有 PCR02 ADB endpoint，且恢复出厂属于显式授权设备写操作
required_followup: 在隔离 standby/watchdog/FPS 修改者后执行恢复出厂短循环与长循环，并核对 shutdown elapsed、core、dmesg 和最终制品身份
owner: leiwenjun
review_after: 2026-09-20
```

## 后续动作

实机验证通过后补充耗时分布和设备证据；出现 worker preservation 时确认 SOC reboot 可正常完成且无 core。未经 owner 复核不提升为 active，也不写入团队通用规范。
