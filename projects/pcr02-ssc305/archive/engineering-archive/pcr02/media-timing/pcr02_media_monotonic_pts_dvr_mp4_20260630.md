# PCR02 media monotonic PTS 对 DVR/MP4 的影响归档

Date: 2026-06-30
Captured: 2026-07-11
Status: archive-only migrated coverage

## 边界

本文从旧 Codex archive `research-notes/20260630-103933-media-monotonic-pts-mp4-impact.md` 抽取。它只保留 PCR02 媒体时间基准的源码级分析和日志迹象，不复制 raw session、完整设备日志或构建产物，不声明已经完成长时间录像/回放压测。

## 结论

- `VSHDIOS_SysInit()` 用 `CLOCK_MONOTONIC` 初始化 `MI_SYS_SyncPts()` 更符合媒体 pipeline 对帧 PTS、latency、gap 和 duration 的要求。
- DVR 录像路径用 frame PTS 做切片、duration 和 MP4 audio/video packet 写入；文件命名和 replay 查询仍使用 wall-clock calendar time。
- MP4 写入层将输入 `pts_us / 10` 写入 packet dts/pts，并在同步逻辑中把 first sample rebase 到 0。
- 因此，将 MI_SYS PTS bootstrap 从 wall-clock 改为 monotonic 不应破坏 DVR 录像/回放的相对时间线。需要防范的是跨模块消费者错误地把 frame PTS 当作 Unix epoch 或 wall-clock。

## 代码证据摘要

- `modules/hdi/src/hdi_os/hdi_os.c`: `VSHDIOS_SysInit()` 调用 `MI_SYS_SyncPts(0, u64Pts)`；修改后 `u64Pts` 来自 `clock_gettime(CLOCK_MONOTONIC, ...)`。
- `modules/hdi/src/hdi_os/hdi_os_time.c`: wall-clock 与 monotonic helper 应保持语义分离。
- `modules/api/src/api_dvr/api_dvr_record.c`: 录像切片、文件 duration、MP4 video/audio packet 写入依赖 frame PTS。
- `modules/api/src/api_dvr/api_dvr_file.c`: 文件命名和 replay 查询使用 calendar time / duration。
- `modules/mp4/mp4.c`: `mp4_write_video_packet()` / `mp4_write_audio_packet()` 对 `pts_us` 做 timescale 转换。
- `modules/mp4/mp4write.c`: `mp4_av_sync()` 将 first sample rebase 到 0，文件 duration 来自相对 DTS 差值。

## 验证迹象

- 修改后设备日志出现 `source_timestamp_untrusted=0`。
- main / low 两路都出现合理的 `source_latency_ms(avg/max/samples)`。
- 这支持原来的 `timestamp_untrusted=90/91` 是时钟域不一致，而不是单纯丢帧。

## 设计规则

- monotonic 用于 frame PTS、latency、gap、duration 和 drop diagnosis。
- wall-clock 用于文件命名、用户可见时间、replay 查询和跨系统日志关联。
- SHM metadata 如需 wall-clock 相关性，应单独字段表达，不复用媒体 PTS 的 epoch 语义。
- 评估“时间基准会不会影响播放”时，先检查 muxer 是否做 first-sample rebase 和 relative duration，再判断风险。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/research-notes/20260630-103933-media-monotonic-pts-mp4-impact.md`
- Old source SHA256: `136a6f155823f5f201b6da7f97812a294bfbed5f33762b78e7a3716806f561b0`
- Old source size: `3782` bytes
- Old source lines: `61`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-001`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-041`

## 风险

- 本文不覆盖外部 SDK packetizer、Agora payload 或 H264 packetization 完整根因。
- 若后续 MP4 muxer、DVR record path 或 SHM metadata 语义变化，应重新审计。
