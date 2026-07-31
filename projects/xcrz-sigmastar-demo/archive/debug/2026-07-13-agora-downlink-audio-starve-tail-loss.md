---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-agora-downlink-audio-starve-tail-loss-20260713
title: PCR02 Agora下行音频STARVE与丢尾音分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f5b80-6445-7440-90d2-5037ca2c2ff9
review_after: '2026-10-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- agora
- audio
- shm
- starve
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-13-agora-downlink-audio-starve-tail-loss.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录Agora连接正常时设备侧音频任务队列拥塞、4帧SHM ring强制回收和STREAM_END过早收尾分别造成断续与丢尾音的证据链及复测边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 Agora 下行音频 STARVE 与丢尾音分析

## 现象

2026-07-13 两组日志分别出现下行语音断续和末尾语音被截断。Agora RTC 连接统计仍持续回调，没有直接证据表明 RTC 已断线。

## 影响范围

- 路径：Agora 下行音频 → Sensor 音频任务队列 → SHM PCM downlink → 播放器。
- 症状：断续、丢帧、尾音截断。
- 本记录不包含原始语音、完整日志或用户内容。

## 证据

| 观察 | 解释 |
| --- | --- |
| 第一组日志中音频任务队列达到固定深度 128 | 单消费者吞吐低于输入，后续任务被丢弃 |
| 单连接场景队列未满，但 4 帧 SHM ring 每 10 秒持续 `STARVE` | subscriber 未及时释放，旧帧被强制回收 |
| 50 fps 输入下约有 14～16 帧/窗口被影响 | 断续与约 2.8%～3.2% 丢帧量级一致 |
| 最后一帧后约 30 ms 即触发结束 | 播放缓存尚未自然 drain，解释丢尾音 |
| Agora stats 正常 | 排除“RTC 断线是唯一根因” |

provenance：`codex-raw-sessions:019f5b80-6445-7440-90d2-5037ca2c2ff9`。

## 根因分层

1. **队列拥塞**：`PLAY_CTRL` 与 PCM 数据由单个 worker 串行消费；消费者阻塞时，128 深度队列会耗尽。
2. **SHM 容量与释放时序**：4 帧 ring 对调度抖动容忍度过低，subscriber 延迟释放会触发强制回收。
3. **结束时序**：`STREAM_END` 过早转为播放器结束，未等待 pending frame 与播放器 cache drain。

三个问题可以同时存在，不应把“断续”和“丢尾音”合并成单一 RTC 网络故障。

## 修复或规避建议

- 记录 producer/consumer sequence、queue depth、SHM acquire/release latency 和 forced reclaim。
- 将控制消息与高频 PCM 数据的处理延迟分开观测，避免慢播放器阻塞整个任务队列。
- 评估增大 SHM ring，但必须同时修复释放时序，单纯扩容只会延迟暴露。
- `STREAM_END` 应等待最后一个 PCM frame 被消费并收到 cache-drained 条件，设置有界超时。
- 引入 `stream_id/playing_id`，避免旧流尾部与新流开始交叉。

## 验证

本轮未复跑源项目或设备。后续必须在同一构建下至少覆盖单连接、双连接、CPU 高负载、连续短语音和长语音，并验证：

- queue high-watermark 不再持续达到 128；
- `STARVE` 和 forced reclaim 为 0 或满足明确预算；
- sequence 无非预期跳号；
- `STREAM_END` 后尾音完整且能收到 drain 完成事件。

```yaml
manual_validation_pending: true
manual_validation_reason: 历史日志支持根因分层，但缺少匹配构建的板级修复后对照
required_followup: 执行下行音频队列、SHM和结束时序联合压力回归
owner: leiwenjun
review_after: 2026-10-13
```

## 归档门禁

- Sanitization：通过；不保留音频、raw 日志、端点或凭证。
- Memory Candidate：no。
- Gate Result：`reviewing / device-validation-pending`。
