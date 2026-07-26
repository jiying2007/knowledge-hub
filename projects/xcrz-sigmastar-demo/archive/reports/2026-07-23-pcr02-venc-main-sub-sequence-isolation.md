---
id: pcr02-venc-main-sub-sequence-isolation-20260723
title: PCR02 VENC main/sub 发布序号独立化记录
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-23-pcr02-venc-main-sub-sequence-isolation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-implementation-summary
  from: 当前会话需求、Sensor源码、定向构建与负向扫描证据
  source_sha256: dc045ffd9a2e671bff3fbb678c76a092982802f3ccda9aac8188b42beb98f786
  temporary_source_retained: false
review_after: '2026-10-23'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- sensor
- venc
- shm
- main-stream
- sub-stream
- sequence
- agora-diagnostics
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-23-pcr02-venc-main-sub-sequence-isolation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-23-pcr02-venc-main-sub-sequence-isolation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-23'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-23'
manual_validation_pending: true
summary_zh: 固化编码视频 main/sub SHM 元数据序号由跨流共享改为每路独立递增的原因、兼容边界和验证证据；源码定向编译通过，板端与 IoT 消费兼容性仍待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 VENC main/sub 发布序号独立化记录

## 结论与边界

PCR02 Sensor 的编码视频 SHM 元数据原先由 main/sub 共用一个原子序号。两路同时发布时，同一路消费者会观察到序号跳跃；这不是实际丢帧，但容易被 IoT、诊断日志或后续连续性检查误判。

当前实现已改为：

- main 使用 `main_sequence_`。
- sub/low 使用 `low_sequence_`。
- 两路均从 0 开始独立递增。
- release/reacquire 不重置序号，保持原有对象生命周期语义。
- 原子递增使用 `std::memory_order_relaxed`，仅保证每个原子对象自身的唯一递增，不建立无必要的跨流、跨核顺序。

本条目只归档 sequence 语义调整。它不声明解决 Agora `ERR_VIDEO_SEND_OVER_BANDWIDTH_LIMIT` 或 `pacer-timeout`；这类异常仍需独立核对实际码率、目标带宽、关键帧突发、CPU 调度和网络状态。

## 背景

运行日志中 main/sub 关键帧的 `last_key_seq` 接近交错：

```text
main: 5556
sub:  5557
```

后续单路序号会包含另一条流消耗的编号。源码核对确认 `VideoEncodedFrameHub` 原先只有一个 `sequence_`，而 main/sub 已经具备独立 SHM channel、profile、publisher 和发布锁，因此序号也应按通道独立。

## 实现

影响文件：

- `modules/sensor/video/video_encoded_frame_hub.h`
- `modules/sensor/video/video_encoded_frame_hub.cpp`

字段由一个全局计数器拆分为：

```cpp
std::atomic<uint64_t> main_sequence_{0};
std::atomic<uint64_t> low_sequence_{0};
```

发布时按 source 选择：

```cpp
if (source == VIDEO_FRAME_SOURCE_VENC_MAIN) {
    meta.set_seq(main_sequence_.fetch_add(1, std::memory_order_relaxed));
}
else {
    meta.set_seq(low_sequence_.fetch_add(1, std::memory_order_relaxed));
}
```

`commitFrameLocked()` 只会在 main/sub source 已完成校验后进入上述分支，因此 `else` 对应 sub/low。

## 行为契约

修改后：

```text
main: 0, 1, 2, 3, ...
low:  0, 1, 2, 3, ...
```

兼容性边界：

- `VideoFrameMeta.seq` 字段类型、序列化格式和 SHM 协议不变。
- 单个 SHM channel 内继续保持唯一、单调递增。
- 不再保证 main 与 low 两个 channel 之间的全局唯一性；跨通道比较 seq 没有业务语义。
- 消费者应以 channel/profile 作为流身份，不能只凭 seq 关联两条不同视频流。

## 验证

2026-07-23 在源码工作区执行：

| Command | Exit Code | Result Summary | Evidence |
| --- | ---: | --- | --- |
| `rtk make modules/sensor_obj_all -j2` | 0 | `video_encoded_frame_hub.cpp` 定向重新编译通过。 | 当前工作区构建输出 |
| `rtk git -C modules/sensor diff --check` | 0 | 修改无空白错误。 | Sensor 子仓 |
| `rtk rg -n 'meta\.set_seq\(sequence_' modules/sensor/video/video_encoded_frame_hub.cpp` | 1（预期） | 旧的共享 sequence 写法已不存在。 | 负向源码扫描 |
| main/low 字段与写入点定向扫描 | 0 | 两个字段和两个 source 写入分支均存在。 | `video_encoded_frame_hub.*` |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | 完成交付门禁。 | 当前会话门禁输出 |

归档时源码状态：

- Sensor 子仓分支：`master`。
- 包含本实现的源码快照：`21aa1bb057df98d84e26e0d8084351f863ea9c2d`。
- 该 revision 是包含多项低功耗/媒体改动的 merge commit，不能把整提交归因于本次 sequence 调整。
- Sensor 子仓工作区在归档检查时为 clean。

## 未完成验证

- 尚未以设备侧相同 BuildID 验证 main/low 长时间序号连续性。
- 尚未验证 IoT 是否存在把不同 channel 的 seq 当成全局唯一值的隐藏依赖。
- 尚未执行弱网、双路 Agora 推流和消费者重连场景回归。

建议板端验证至少记录：

1. main/low 各自连续 2 分钟的 `profile + seq + timestamp_ms`。
2. 单路启停和双路反复订阅后的序号行为。
3. SHM reclaim/acquire failure 存在时，区分“生产序号连续”和“消费者实际跳帧”。
4. IoT 日志按 local stream 打印 seq，确认不再因另一条流发布而产生固定间隔跳号。

## 风险与回退

- 如果历史消费者错误依赖跨通道全局唯一 seq，需要先修正消费者，以 `(channel/profile, seq)` 作为身份；不建议恢复错误的跨流连续性语义。
- 如必须临时回退，只需恢复单个 `sequence_` 并在两路发布时共用，但会重新引入单路观察到的伪跳号。
- 本改动不改变编码码率、GOP、关键帧大小、SHM payload 上限或 Agora pacer 行为。

## Provenance 与脱敏

- captured_at：2026-07-23。
- last_verified：2026-07-23。
- source：当前会话需求、Sensor 源码、定向构建与负向扫描证据。
- sanitization：未保存设备地址、完整运行日志、客户信息、凭证、二进制或本机绝对源码路径。
- memory candidate：否。
- active promotion：否；仅作为 `reviewing` 项目归档候选。

## 归档门禁摘要

- Source：当前会话与 `modules/sensor/video/video_encoded_frame_hub.*`。
- Topic：`venc-main-sub-sequence-isolation`。
- Sanitization：通过。
- Verification：源码定向编译与静态检查通过，板端验证待完成。
- Memory Candidate：no。
- Gate Result：archive candidate 可落盘；运行态结论为 `manual-validation-pending`。
