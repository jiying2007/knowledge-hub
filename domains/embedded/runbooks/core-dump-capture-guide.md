---
title: Core Dump 采集与打包指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [core, crash, debug]
related: [gdb-debug-guide.md, asan-debug-guide.md, offline-gdb-core-fastpass-guide.md]
validation_refs: [tools/debug/core-env-snapshot.sh, docs/runbooks/gdb-debug-guide.md]
---

# 1. 目的

规范目标板崩溃后 `core` 文件采集，避免“有 core 但无法离线定位”的情况。

# 2. 适用范围

适用于本项目用户态程序（如 `prog_pcr02/prog_main/prog_daemon`）崩溃后的离线排查。

# 3. 前置条件

1. 目标板可写目录可用（建议 `/tmp`）。
2. 主机保留同版本符号文件（`out/arm/app/*.debug.full`）。
3. 可执行 `dmesg`、`ulimit`、`cat /proc/sys/...`。

# 4. 目标板开启 core

```bash
ulimit -c unlimited
echo 2 > /proc/sys/fs/suid_dumpable
mkdir -p /tmp/core
chmod 1777 /tmp/core
echo '/tmp/core/core.%e.%p.%t' > /proc/sys/kernel/core_pattern
```

快速核验：

```bash
cat /proc/sys/kernel/core_pattern
cat /proc/sys/fs/suid_dumpable
ulimit -c
```

# 5. 崩溃后采集清单

至少采集以下内容：

1. core 文件：`/tmp/core/core.<exe>.<pid>.<ts>`
2. 崩溃程序：`/customer/bin/<exe>`
3. 对应符号文件：`out/arm/app/<exe>.debug.full`
4. 板端日志：`dmesg | tail -n 300`
5. 环境快照：`core_pattern`、`suid_dumpable`、磁盘空间

建议在目标板执行：

```bash
ls -lh /tmp/core
dmesg | tail -n 300 > /tmp/core/dmesg.tail.txt
```

# 6. 一键环境快照脚本

主机执行：

```bash
rtk bash tools/debug/core-env-snapshot.sh --output out/arm/app/core-env
```

脚本输出包括：

1. 工具链与 gdb 路径检查
2. `out/arm/app` 下 core 与 debug 文件目录快照
3. 关键信息模板（便于粘贴到问题单）

# 7. 常见问题

1. `core_pattern=/dev/null`：core 被丢弃，需改写 `core_pattern`。
2. `Segmentation fault (core dumped)` 但无文件：检查目录权限和空间。
3. core 很大：允许先压缩归档，但需保留原始文件名信息。

# 8. 交付格式建议

提交排障材料时建议包含：

1. 崩溃时间与场景描述
2. core 文件名
3. 对应 `*.debug.full` 文件名
4. `dmesg.tail.txt`
5. 是否可稳定复现
