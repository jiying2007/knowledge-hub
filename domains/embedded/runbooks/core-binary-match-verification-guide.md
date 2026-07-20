---
title: Core 与 Binary 配对校验指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [core, gdb, buildid, debug]
related: [gdb-debug-guide.md, core-dump-capture-guide.md, offline-gdb-core-fastpass-guide.md]
validation_refs: [tools/debug/verify-core-match.sh, docs/runbooks/gdb-debug-guide.md]
---

# 1. 目的

快速判断 `core` 与 `*.debug.full` 是否匹配，降低误判和无效调试成本。

# 2. 触发信号

出现以下任一提示时应先做配对校验：

1. `warning: core file may not match specified executable file`
2. `warning: Source file is more recent than executable`
3. 回溯函数名异常或大量 `??`

# 3. 操作步骤

## 3.1 自动校验（推荐）

```bash
rtk bash tools/debug/verify-core-match.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --core out/arm/app/core-th_0x283855-913-12
```

结果约定：

1. `LIKELY_MATCH`：未发现明确不匹配提示
2. `MISMATCH`：gdb 报告不匹配，需重新找同构建版本二进制

## 3.2 手工校验（补充）

```bash
rtk /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb \
  -batch -ex "info files" -ex "info threads" \
  out/arm/app/prog_pcr02.debug.full out/arm/app/core-xxxx
```

# 4. 失败处理

1. 更换正确版本的 `*.debug.full`（同一次构建）。
2. 若符号已分离，确认 `*.debug` 与运行二进制是同源产物。
3. 无法确认版本时，先回到 [core-dump-capture-guide.md](core-dump-capture-guide.md) 重新采集标准材料。

# 5. 验证记录

建议在问题单记录：

1. 校验命令
2. 结论（`LIKELY_MATCH/MISMATCH`）
3. 使用的 `bin/core` 文件名
