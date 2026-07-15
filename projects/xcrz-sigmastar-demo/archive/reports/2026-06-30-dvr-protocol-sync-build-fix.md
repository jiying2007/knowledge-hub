---
title: PCR02 DVR 协议手工同步与 sensor include 构建修复
doc_type: project-archive
status: archived
owner: leiwenjun
created: 2026-07-11
last_updated: 2026-07-11
tags: [pcr02, dvr, proto, sensor, build-fix, codex-archive-migration]
---

# PCR02 DVR 协议手工同步与 sensor include 构建修复

## 边界

本文从旧 Codex archive `debug-notes/20260630-034504-pcr02-dvr-protocol-sync-build-fix.md` 抽取，记录 2026-06-30 对 DVR 协议文本改动的手工同步、协议编号重排和 include 修复。本文不声明 DVR record/replay 行为已完成端到端联调。

## 背景

- `git cherry-pick 02b7383c` 被本地改动阻挡。
- 用户明确要求手动同步 `02b7383c` 关于 DVR 的代码，不合入库。
- 后续约束要求 `SOC_REBOOT`、`SOC_SLEEP`、`SOC_SHUTDOWN` 连续，DVR 命令排在后面。

## 决策

- 只同步文本协议/API: `include/api/api_dvr.h`、`modules/proto/sensor_ctrl.proto`、`modules/proto/sensor_info.proto`。
- 不同步来源提交中的 `libapi.so`、`libsensor.so`、`libapi.a`、`libsensor.a`。
- 当前分支已有 `SOC_REBOOT`，不能机械沿用来源提交的 DVR 编号。
- `DeviceType` 与 `oneof payload` 必须成组审计，不能只改枚举。

## 协议落点

`DeviceType`:

- `SOC_REBOOT = 18`
- `SOC_SLEEP = 19`
- `SOC_SHUTDOWN = 20`
- `DVR_RECORD = 21`
- `DVR_REPLAY = 22`

`oneof payload`:

- `soc_reboot = 27`
- `soc_sleep = 28`
- `soc_shutdown = 29`
- `dvr_record = 30`
- `dvr_replay = 31`

新增空占位消息:

- `SocSleepPayload`
- `SocShutdownPayload`

## 构建问题与修复

`./make.sh -c` 暴露的首个 fatal error 是 `video/video_raw_frame_hub.h` 找不到。当前 include path 包含 `$(BUILD_TOP)/modules`，因此 sensor 内部头文件应使用 `sensor/...` 前缀。

修复点:

- `modules/sensor/display/qr/qr_scene.cpp`
- `modules/sensor/qr/qr_capture.cpp`

统一 include 为:

```cpp
#include "sensor/video/video_raw_frame_hub.h"
```

## 验证摘要

- `protoc --proto_path=modules/proto --descriptor_set_out=/tmp/pcr02_sensor_dvr.pb modules/proto/sensor_ctrl.proto modules/proto/sensor_info.proto` 通过。
- `git diff --check` 对目标协议/API 文件通过。
- `./make.sh -c` 修复 include 后退出码为 0，仍有 warning，但无 fatal/error。

## 可复用规则

- 手工同步提交时，先用 `git show --stat --name-status <commit>` 找出文本文件和二进制文件边界。
- 协议编号冲突时，以当前分支现有 wire number 为准，不能照搬来源提交编号。
- `DeviceType` 与 `oneof payload` 必须成组审计。
- 构建日志先处理第一处真实 fatal，再用 `rg` 找同类 include 模式，避免下一轮构建换文件失败。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/debug-notes/20260630-034504-pcr02-dvr-protocol-sync-build-fix.md`
- Old source SHA256: `e96038f4e2da3c46baa5ac26d23db4d9a8276c01d3c1325b63f66e21854db45b`
- Old source size: `3337` bytes
- Old source lines: `93`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-003`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-043`
