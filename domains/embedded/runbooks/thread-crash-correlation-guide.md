---
title: 多线程崩溃关联分析指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [thread, crash, gdb, correlation]
related: [gdb-debug-guide.md, crash-triage-checklist.md, offline-gdb-core-fastpass-guide.md]
validation_refs: [tools/debug/gdb-core-deeppass.sh, tools/debug/extract-crash-signature.sh]
---

# 1. 目的

在多线程 core 中快速区分“主崩溃线程”与“伴随损坏线程”，避免被噪声线程误导。

# 2. 关键原则

1. 先锁定 `Current thread` 与 `#0`，再看其他线程。
2. `thread apply all bt` 只做短深度（建议 2 到 3 层）。
3. 若多数线程栈都损坏，优先怀疑内存破坏扩散，而非每线程独立问题。

# 3. 推荐步骤

## 3.1 首轮 FastPass

```bash
rtk bash tools/debug/gdb-core-fastpass.sh --bin <bin.debug.full> --core <core>
```

## 3.2 二轮 DeepPass 关联

```bash
rtk bash tools/debug/gdb-core-deeppass.sh --bin <bin.debug.full> --core <core>
```

重点关注：

1. 哪些线程出现在同一模块调用链。
2. 是否出现大量 `corrupt stack`。
3. 崩溃前是否有共享资源竞争迹象（锁、队列、缓冲区）。

# 4. 证据分层

1. 一级证据：崩溃线程 `#0`、signal、源码行号。
2. 二级证据：与一级线程共享模块的短回溯。
3. 三级证据：其余线程状态（阻塞/等待/损坏）。

# 5. 输出模板

1. 主崩溃线程结论
2. 关联线程摘要（最多 3 个）
3. 是否存在“全局内存破坏”迹象
4. 下一步验证动作（复现、加日志、加边界校验）

# 6. 工具协同

1. 使用 `tools/debug/extract-crash-signature.sh` 产出签名，便于跨次崩溃聚类。
2. 使用 `tools/debug/collect-crash-bundle.sh` 保留证据，避免信息丢失。
