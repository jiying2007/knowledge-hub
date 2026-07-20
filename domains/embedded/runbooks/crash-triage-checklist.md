---
title: 崩溃分诊清单（SIGSEGV/SIGBUS/SIGABRT）
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [crash, triage, segv, sigbus, sigabrt]
related: [core-dump-capture-guide.md, offline-gdb-core-fastpass-guide.md, asan-debug-guide.md]
validation_refs: [docs/runbooks/gdb-debug-guide.md, tools/debug/gdb-core-fastpass.sh]
---

# 1. 目的

统一崩溃初筛动作，避免直接进入高成本全量调试。

# 2. 五步分诊

1. 确认信号类型：`SIGSEGV / SIGBUS / SIGABRT`
2. 确认崩溃线程函数与源码行号（FastPass）
3. 判断是否版本不匹配（binary/core/source）
4. 判断是否输入数据异常（chunk size、长度、边界）
5. 判断是否内存破坏扩散（多线程栈损坏、随机地址）

# 3. 快速判别提示

1. `SIGBUS`：优先怀疑未对齐访问、非法映射、结构体边界越界。
2. `SIGSEGV`：优先怀疑空指针/野指针/越界写后读取。
3. `SIGABRT`：优先看 `assert`、`abort()`、ASAN/库内部主动终止。

# 4. 最小命令集

```bash
rtk bash tools/debug/gdb-core-fastpass.sh --bin <bin.debug.full> --core <core> --out out/arm/app/gdb-fastpass
```

若需要升级：

```bash
rtk bash tools/debug/gdb-core-deeppass.sh --bin <bin.debug.full> --core <core> --out out/arm/app/gdb-deeppass
```

# 5. 升级 DeepPass 的条件

1. `frame 0` 无法解释崩溃点
2. 局部变量被优化不可读且无替代证据
3. 需要跨线程确认并发竞争
4. 崩溃点疑似症状而非根因

# 6. 问题单最小字段

1. 崩溃时间
2. core 文件名
3. 二进制与符号文件名
4. 信号类型与崩溃函数
5. 是否稳定复现
6. 当前根因假设与置信度
