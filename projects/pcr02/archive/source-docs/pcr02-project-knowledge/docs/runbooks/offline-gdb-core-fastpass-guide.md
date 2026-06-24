---
title: 离线 GDB Core FastPass 指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [gdb, core, crash, token]
related: [gdb-debug-guide.md, core-dump-capture-guide.md]
validation_refs: [tools/debug/gdb-core-fastpass.sh, tools/debug/gdb-core-deeppass.sh]
---

# 1. 目的

用最小输出完成 core 初判，减少长回溯噪音与 token 消耗。

# 2. 核心策略

两阶段执行：

1. FastPass：只看崩溃线程和关键寄存器/局部变量。
2. DeepPass：仅在 FastPass 证据不足时补充全线程或反汇编。

# 3. 输入要求

1. 程序符号：`out/arm/app/<exe>.debug.full`
2. core 文件：`out/arm/app/core-*`

注意：`gdb` 若提示 `core file may not match specified executable file`，先修正配对关系再继续。

# 4. FastPass（推荐默认）

```bash
rtk bash tools/debug/gdb-core-fastpass.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --core out/arm/app/core-th_0x283855-913-12 \
  --out out/arm/app/gdb-fastpass
```

输出文件内容固定为：

1. `frame 0`
2. `bt 12`
3. `info locals`
4. `info registers`
5. `info threads`

# 5. DeepPass（按需）

```bash
rtk bash tools/debug/gdb-core-deeppass.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --core out/arm/app/core-th_0x283855-913-12 \
  --out out/arm/app/gdb-deeppass
```

DeepPass 额外包含：

1. `thread apply all bt 2`
2. `x/32wx $sp`
3. `disassemble /m`（当前崩溃函数）

# 6. 建议输出模板

1. 崩溃结论：信号 + 线程 + 函数 + 文件行号
2. 关键证据：最多 5 条
3. 根因假设与置信度
4. 下一步最小验证动作

# 7. 常见报错处理

1. `No such file or directory`：检查 `--bin/--core` 路径是否存在。
2. `warning: Source file is more recent than executable`：源码与崩溃包版本不一致。
3. `Could not load shared library symbols`：离线 core 初判可忽略，必要时补 `sysroot`。
