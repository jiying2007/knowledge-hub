---
title: PCR02 SIGBUS core 与 debug tools 历史归档 2026-05-15
doc_type: debug-record
knowledge_type: incident-learning
maturity: archived
status: archived
owner: leiwenjun
created: 2026-07-10
last_updated: 2026-07-10
tags: [pcr02, prog_pcr02, sigbus, core, wav, busybox, debug-tools, codex-archive-migration]
related:
  - ../../current/runbooks/project-debug-tools-guide.md
  - ../../../../domains/embedded/tools/debug/README.md
  - ../../../../domains/embedded/runbooks/spi-nand-busybox-io-stress-guide.md
---

# PCR02 SIGBUS core 与 debug tools 历史归档 2026-05-15

## 归档边界

- 状态：历史排障归档，archive-only。
- 当前事实边界：本文只记录 2026-05-15 两次旧 Codex session-wrap 中的排障结论和工具化动作，不声明当前 `prog_pcr02` 根因。
- 删除边界：旧 Codex archive 正文已在独立授权批次中删除；本文保留 source path、hash、风险和覆盖入口。
- 当前调试入口以 `projects/xcrz-sigmastar-demo/current/runbooks/project-debug-tools-guide.md`、`domains/embedded/tools/debug/README.md` 和相关 embedded runbook 为准。

## 来源

| source_path | source_sha256 | size_bytes |
| --- | --- | ---: |
| `domains/codex/archive/codex-archive/session-wrap/20260515-142200-session-wrap-crash-debug-tools.md` | `8dde26d0cd2f20b08e82d3c6b2dfb6654c2b52633a9aea23171ebcf77240d862` | 3900 |
| `domains/codex/archive/codex-archive/session-wrap/20260515-154658-session-wrap-core-debug-and-busybox-tools.md` | `d4e13137ee5d6a9b280706ce9a40dc773ff82e8c655fcf4110add2edd2b916f9` | 2867 |

## 历史结论

2026-05-15 的第一轮排障聚焦 `prog_pcr02` 音频/WAV 路径。旧 core 显示主线程在 `audio_wav.c` 解析链路触发 `SIGBUS`，当时判断与 WAV chunk 解析高度相关。随后对 `api_audio_player` 流层做了健壮性修复，包括 `fd=0` 判定、短读短写、`EINTR` 重试、`StreamRead8` 返回值校验和 endian 读取失败处理。

同轮还在 WAV 入口加入 `[WAV_GUARD]` 防御日志，用于输出异常 chunk、seek 前后上下文和回退路径，方便复现时定位输入数据或解析状态异常。

第二轮排障扩展到多份 core 和设备侧 BusyBox 工具。旧会话记录了三类 SIGBUS：

- `core-AgoraRTC-913-7759`：PC 落在无效代码区特征，符号不足时置信较低。
- `core-sensor_in0-914-416`：落在 `vl53l8x/platform.c::_CopyBytes`，调用链来自 TOF init 固件写入。
- `core-prog_pcr02-913-2235`：落在 `comm::Subscribe::onSensorAudioInfo(...)` 入口。

当时的系统性假设是：多线程随机 SIGBUS 和 `corrupt stack` 特征更偏底层存储、UBIFS 或页读取不稳定，而不是单个业务模块稳定缺陷。该假设后来需要结合 SPI-NAND、UBIFS、I/O 压力和板端日志继续验证，不能作为最终根因。

## 工具化动作

旧会话推动了 debug tools 的早期产品化：

- `match-build-artifact.sh` 改为优先读取 core 内 `execfn`，避免 `core-AgoraRTC-*` 等文件名误匹配。
- `verify-core-match.sh` 改为低噪摘要输出，完整 GDB 输出落盘，并提示 core execfn 与 bin name 一致性。
- `gdb-core-fastpass.sh` / `gdb-core-deeppass.sh` 增加 `--sysroot` 和 `--solib-search-path`。
- 新增 `busybox-kernel-io-watch.sh`，用于 BusyBox 环境下轮询 `dmesg -c`、线程级 `/proc/<pid>/task/*/io` 增量和命中快照。

这些工具入口已经由当前 embedded debug tools 和 PCR02 debug runbook 承接；旧会话正文不再作为入口。

## 风险与保留限制

- 历史 core 存在 `Source file is more recent than executable` 和 `core may not match executable` 风险；源码行级结论低于 BuildID/MD5 完整匹配证据。
- WAV 路径和 UBIFS/存储方向都是历史阶段判断，不能覆盖后续 SPI-NAND、UBIFS、SquashFS/static volume 和运行态 I/O 的更成熟归档。
- 本文不复制 raw core、完整 GDB 输出、运行日志、二进制或 cache。
- 本文不写 memory、不提升 active、不生成 owner decision。

## 相关覆盖

- `projects/xcrz-sigmastar-demo/current/runbooks/project-debug-tools-guide.md`
- `domains/embedded/tools/debug/README.md`
- `domains/embedded/runbooks/spi-nand-busybox-io-stress-guide.md`
- `projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-prog-pcr02-core-gdb-selection.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/ubifs-squashfs/pcr02_ubifs_troubleshooting_20260528.md`
- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/boot-flash/pcr02_spinand_read_path_bdma_riu_20260529.md`
- `artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-019..020`

## 删除记录

旧 source 正文删除记录：

- `artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl#CARE-20260710-027`
- `artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl#CARE-20260710-028`
