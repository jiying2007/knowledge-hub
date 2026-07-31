---
id: pcr02-prog-pcr02-memory-growth-monitoring-20260731
title: PCR02 prog_pcr02 匿名堆持续增长监控记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-prog-pcr02-memory-growth-monitoring.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session-and-runtime-evidence
  from: 2026-07-31 PCR02 prog_pcr02 只读 ADB 内存监控、源码检查与证据哈希
  source_sha256: 8a03da64bb2fdf647fd14456d9e8081bc45db44270568a8839e9e2e621a07fec
review_after: '2026-10-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- prog-pcr02
- memory-leak
- runtime-monitoring
- adb
- needs-root-cause
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-prog-pcr02-memory-growth-monitoring.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-31-prog-pcr02-memory-growth-monitoring.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 2026-07-31 对 PCR02 prog_pcr02 进行只读内存监控，确认匿名堆与 Private Dirty 以约 4.5～4.9 MB/min 增长；线程、FD、映射数稳定，根因尚待分配器与队列计数定位。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 prog_pcr02 匿名堆持续增长监控记录

## 归档目的与结论边界

本文归档 2026-07-31 对 PCR02/SigmaStar SSC305 设备上 `prog_pcr02` 的只读内存监控结论、证据索引和后续定位方案。

当前可确认：

- 监控窗口内 PID、进程启动时间和 `boot_id` 均保持不变。
- `VmRSS`、`RssAnon`、PSS、`Private_Dirty`、`VmData` 持续增长，系统 `MemAvailable` 同步下降。
- 线程数、FD 数和 `/proc/<pid>/maps` 行数保持稳定。
- 运行态证据高度符合既有匿名堆中的存活对象、业务队列或缓存持续积压。
- 最新 dmesg 未见 OOM、`Killed process`、segfault、panic 或 core。

当前不能确认：

- 尚未取得分配调用栈、对象类型或模块级队列增长证据，不能把问题归因到具体函数或模块。
- 尚未通过 `mallinfo2()` 区分真实存活分配与 glibc arena/碎片化。
- 尚未完成修复前后对比和长时间 soak，不能声明问题已修复。

本文不保存设备端点、真实 SN、raw log、二进制、本机绝对路径、凭证或完整会话内容。

## 环境与方法

- 平台：PCR02 / SigmaStar SSC305 ARM Linux。
- 目标进程：`/customer/bin/prog_pcr02`。
- 设备运行二进制 MD5：`8f5b188c5e04c9e48e2697932e347e2`。
- 采集方式：通过 ADB 只读采样 `/proc/<pid>/status`、`smaps_rollup`、FD、maps 和 `/proc/meminfo`。
- 采样窗口：2026-07-31 16:06:49 至 16:10:23，Asia/Hong_Kong。
- 有效样本：8 个；间隔约 30 秒；首末跨度 214 秒。
- 终止条件：系统可用内存快速下降；为避免坐等 OOM，在证据足够后主动停止长窗口。
- 设备变更：未执行 kill、restart、部署、覆盖、remount 或其他设备写操作。

## 运行态证据

| 指标 | 首样本 | 末样本 | 变化 | 线性斜率 |
| --- | ---: | ---: | ---: | ---: |
| `VmRSS` | 84,200 kB | 102,684 kB | +18,484 kB | +4,899 kB/min |
| `RssAnon` | 68,348 kB | 86,368 kB | +18,020 kB | +4,745 kB/min |
| PSS | 85,766 kB | 103,053 kB | +17,287 kB | +4,554 kB/min |
| `Private_Dirty` | 70,916 kB | 88,192 kB | +17,276 kB | +4,551 kB/min |
| `VmData` | 1,064,680 kB | 1,081,976 kB | +17,296 kB | +4,539 kB/min |
| `MemAvailable` | 38,468 kB | 21,148 kB | -17,320 kB | -4,591 kB/min |

稳定项：

- 线程数：`113 -> 113`。
- FD 数：首末均为 `169`，窗口内范围 `168-169`。
- maps 行数：`836 -> 836`。
- `RssFile` 仅增加 464 kB，主要增量来自匿名和 private dirty 内存。
- `CmaFree=0` 全程存在，但当前证据直接指向进程匿名内存；不能据此认定 CMA 泄漏。

停止长窗口约两分钟后复核：

- PID、启动时间和 `boot_id` 仍未变化。
- `RssAnon=92,592 kB`。
- `Private_Dirty=94,180 kB`。
- `MemAvailable=15,048 kB`。

该复核说明增长不是采样过程造成的一次性瞬时抖动。由于系统已进入低内存压力区，没有继续等待 OOM 或崩溃。

## 假设矩阵

| 假设 | 当前依据 | 下一验证动作 | 状态 |
| --- | --- | --- | --- |
| 线程池任务积压 | 公共 ThreadPool 使用无容量上限的 FIFO；已有 queued/submitted/completed 统计但未周期输出 | 每 30 秒输出 `ThreadPool::stats()`，比较 queue depth 与内存斜率 | 高优先级，未确认 |
| 存活堆对象持续增加 | `RssAnon`、PSS、`Private_Dirty`、`VmData` 同步增长 | 周期输出 `mallinfo2()` 的 `uordblks/fordblks/arena/hblkhd` | 高优先级，未确认 |
| glibc arena 或碎片化 | maps 不增长，现有匿名堆区扩张也可能包含 allocator retained free pages | 测试构建中比较 `uordblks` 与 RSS；受控执行一次 `malloc_trim(0)` | 中优先级，未确认 |
| Display flush 队列积压 | 非 shadow 路径使用无容量上限的 `flushQueue_` | 增加 depth/high-water/submitted/completed/flush latency | 中优先级，未确认 |
| ZMQ 或业务 handler 积压 | 历史日志存在 req/rep handler 长耗时；当前窗口未建立直接相关性 | 按 channel 统计 published/received/dropped/inflight bytes | 中优先级，未确认 |
| FD 或线程泄漏 | FD 和线程数稳定 | 无需优先扩大此方向 | 已基本排除 |
| 不断新增 mmap | maps 行数稳定 | 用 `mallinfo2().hblkhd` 和映射分类继续核对 | 当前证据不支持 |
| CMA/驱动专属泄漏 | `CmaFree=0`，但进程 private anonymous 增长明确 | 只有进程指标解释不足时再补 vendor counter | 低优先级 |

## 推荐定位顺序

1. 在 `prog_pcr02` 主循环中每 30 秒聚合输出 `mallinfo2()` 和现有 `ThreadPool::stats()`；禁止逐次 malloc 日志。
2. 若 `uordblks` 与 `RssAnon` 同步增长，继续追存活对象或业务积压；若 `arena/fordblks` 增长而 `uordblks` 稳定，转向碎片化和 allocator retained pages。
3. 若 `queued_tasks` 或 `submitted-completed` 差值增长，按任务名追加 queued count、queued bytes、执行耗时和等待时长。
4. 给 Display flush、视频帧、音频帧、protobuf Arena 和 ZMQ channel 增加 created/destroyed/live/live_bytes 或 produced/consumed/dropped/inflight 聚合计数。
5. 固定相同制品与场景，按 AI Vision、Bridge video、Sensor Display、AI Voice/Agora、Navigation、IoT、Task 的顺序做单变量功能二分。
6. 只有缩小到具体模块后，才对大于阈值的分配做低比例调用栈采样，并用匹配 debug ELF 解析地址。

## 修复验证门禁

修复完成至少需要：

- 相同固定场景下完成修复前后对比。
- 预热后连续 30 分钟 RSS/PSS 进入平台期，波动有界且不再呈稳定正斜率。
- 相关队列深度、live object 和 live bytes 不持续扩大，并能在业务结束后回落。
- 完成 5-10 次相关功能启停循环，内存恢复到稳定区间。
- 长时间 soak 无 OOM、core、fatal dmesg、PID 漂移或 ADB/shell 健康异常。
- 测试结束恢复产品健康状态和最终 installed 制品身份。

## 证据索引

- 运行态监控 raw artifact SHA256：`e6218072bd68b23b124d68b3be95251c11a951b41af07d658d31ec7b98e74f20`；raw log 不进入 Knowledge Hub 正文。
- 稳定 preflight evidence-index SHA256：`77010395b5717f1b8550f6fe764c49e795e3a90880edf47962f1ffe25641f0e8`。
- 停止监控后 post-capture evidence-index SHA256：`5f1e194ec4c7c94306540a57b2fa4889957a96f4be2e1104d7eff408f7e16780`。
- `git diff --check`：退出码 0。
- `final-ready.sh`：退出码 0；不替代根因和修复验证。

## 临时脚本与资产边界

- 本次使用的 `memory_monitor.sh`、`analyze_memory_monitor.py` 和 `tmp/pcr02-adb-runtime-debug/` 中其他文件属于临时运行态证据与分析辅助物，不自动同步到 Knowledge Hub，也不复制到归档正文。
- 归档只保留脚本所实现的指标定义、分析口径、结果摘要和 raw artifact SHA256。
- 若后续确认脚本具备长期复用价值，应单独审查并提升到项目 `codex_assets/skills/pcr02-adb-runtime-debug/scripts/`，补齐参数校验、端点脱敏、熔断、evidence index、help/dry-run 和验证；不能把临时脚本直接视为正式工具。
- 脚本提升属于源码/工具资产变更，需要单独 diff、测试和提交决策，不由知识归档自动完成。

## Provenance 与治理

- `captured_at`：2026-07-31。
- `last_verified`：2026-07-31。
- 来源：当前 Codex 会话、PCR02 只读 ADB 运行态监控、项目源码只读检查和证据 SHA256。
- 脱敏：设备端点、真实 SN、raw log、二进制、凭证和本机绝对路径未保存。
- 根因状态：`needs-fix`；未确认具体分配函数或模块。
- memory candidate：否。
- AGENTS candidate：否。
- promotion：无；本条目仅作为 `reviewing` debug record，不自动成为 current fact、owner decision、memory 或团队通用规范。
