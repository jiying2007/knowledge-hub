---
title: SPI NAND BusyBox 压测与内核 I/O 监控手册
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-21
last_updated: 2026-05-21
tags: [spi-nand, ubifs, busybox, stress, monitoring]
related: [embedded-linux-performance-triage-guide.md, ../standards/shell-script-style-guide.md, ../../tools/debug/README.md, ../../tools/debug/busybox-kernel-io-watch.sh, ../../tools/debug/busybox-nand-io-pressure.sh, ../../tools/debug/busybox-nand-stress-suite.sh]
validation_refs: [../../tools/debug/busybox-kernel-io-watch.sh, ../../tools/debug/busybox-nand-io-pressure.sh, ../../tools/debug/busybox-nand-stress-suite.sh]
---

# 背景

面向 SigmaStar/BusyBox 设备在现场复现与定位 SPI NAND 异常（`UBIFS/SQUASHFS/decompress/I/O error`）场景。目标是用统一入口稳定采集“内核命中 + 线程 I/O 增量 + 压测过程证据”。

# 前置条件

1. 设备可执行 `sh`、`dmesg`、`awk`、`dd`、`sort`、`grep`、`tar`（可选）。
2. 已部署脚本目录：`tools/debug/`。
3. 可写临时目录：`/tmp` 或 `/data`。
4. 若要联动 OTA，请确认额外命令可独立执行。
5. 注意：`busybox-kernel-io-watch.sh` 在 `--dmesg-mode clear` 下会清空 ring buffer。

# 操作步骤

1. 仅做监控（不压测）：

```bash
rtk sh tools/debug/busybox-kernel-io-watch.sh \
  --proc prog_pcr02 \
  --duration 600 \
  --interval 1 \
  --top 10 \
  --dmesg-mode snapshot \
  --idle-log-every 20 \
  --out /tmp/io-watch.log \
  --stdout 0
```

2. 仅做 I/O 压测：

```bash
rtk sh tools/debug/busybox-nand-io-pressure.sh \
  --target-dir /data/io-stress \
  --duration 1800 \
  --workers 2 \
  --block-kb 256 \
  --block-count 4 \
  --sync-every 5 \
  --readback 1 \
  --meta-burst 20 \
  --out /tmp/io-pressure.log
```

3. 监控+压测一体运行（推荐）：

```bash
rtk sh tools/debug/busybox-nand-stress-suite.sh \
  --duration 2400 \
  --proc prog_pcr02 \
  --out-dir /tmp/nand-stress-suite
```

4. 与 OTA 并行（更接近现场）：

```bash
rtk sh tools/debug/busybox-nand-stress-suite.sh \
  --duration 2400 \
  --proc prog_pcr02 \
  --out-dir /tmp/nand-stress-ota \
  --extra-cmd "sh /data/app_ota/ota_upgrade.sh"
```

# 回滚方案

1. 停止正在运行的压测/监控进程：

```bash
rtk sh -c 'pkill -f busybox-nand-stress-suite.sh || true; pkill -f busybox-nand-io-pressure.sh || true; pkill -f busybox-kernel-io-watch.sh || true'
```

2. 删除压测生成目录（按需）：

```bash
rtk sh -c 'rm -rf /data/io-stress /tmp/nand-stress-suite /tmp/nand-stress-ota /tmp/io-watch-snapshots'
```

3. 若设备出现 I/O 异常后仅冷上电恢复，先断电重启，再保留 `/tmp` 下日志包用于离线分析。

# 验证记录

1. 关键输出文件：
- `watch.log`：关键字命中与线程 I/O 增量。
- `pressure.log`：每 worker 压测统计与失败计数。
- `summary.txt`：整轮统计摘要（命中次数、产物路径）。
- `dmesg-pre.txt`、`dmesg-post.txt`：压测前后内核快照。

2. 成功标准：
- 运行期间无脚本语法/参数错误。
- 能生成至少一组监控与压测日志。
- 若复现异常，可在 `watch.log` 中看到 `UBIFS/SQUASHFS/I/O error` 命中并关联 I/O 增量。

3. 失败标准：
- 日志未生成或被覆盖为空。
- 脚本提前退出且 `summary.txt` 无结果统计。
- `dmesg` 命中与压测时序无法对应（建议提高 `duration` 并固定业务负载）。
