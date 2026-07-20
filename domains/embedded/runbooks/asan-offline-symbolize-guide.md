---
title: ASAN 日志离线符号化指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [asan, symbolize, addr2line, debug]
related: [asan-debug-guide.md, crash-triage-checklist.md]
validation_refs: [tools/debug/asan-log-symbolize.sh, docs/runbooks/asan-debug-guide.md]
---

# 1. 目的

将目标板 ASAN 日志中的地址快速映射到函数和源码行，减少人工查找时间。

# 2. 输入要求

1. 同版本符号文件：`out/arm/app/<exe>.debug.full`
2. ASAN 日志文件：如 `/tmp/asan.*`

# 3. 操作步骤

## 3.1 从日志批量符号化

```bash
rtk bash tools/debug/asan-log-symbolize.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --log out/arm/app/asan.log \
  --out out/arm/app/asan-symbolized.txt
```

## 3.2 手工指定地址符号化

```bash
rtk bash tools/debug/asan-log-symbolize.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --addr 0x12345678 --addr 0x23456789
```

# 4. 结果解读

输出按地址分段：

1. 地址
2. 函数名
3. 文件与行号

若出现 `??:0`：

1. 先检查 `core/binary/debug.full` 是否同版本
2. 再检查地址是否属于当前可执行文件映射区间

# 5. 常见问题

1. 地址很多但有效行少：日志中混入共享库地址，需结合 gdb 二次确认。
2. 全部无法符号化：通常是符号文件版本不对或被错误 strip。

# 6. 关联流程

1. 内存问题首轮：参考 [asan-debug-guide.md](asan-debug-guide.md)
2. 仍需 core 交叉验证：参考 [offline-gdb-core-fastpass-guide.md](offline-gdb-core-fastpass-guide.md)
