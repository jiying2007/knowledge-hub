---
title: SIGBUS 对齐与映射排查指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [sigbus, alignment, mmap, crash]
related: [crash-triage-checklist.md, gdb-debug-guide.md, offline-gdb-core-fastpass-guide.md]
validation_refs: [tools/debug/gdb-core-fastpass.sh, tools/debug/gdb-core-deeppass.sh]
---

# 1. 目的

针对 `SIGBUS` 提供统一排查流程，重点覆盖未对齐访问与非法映射场景。

# 2. 常见根因

1. 结构体/指针未对齐访问（尤其是跨平台 packed 结构）。
2. `mmap` 区域访问越界或底层文件截断。
3. 错误的类型强转导致总线访问异常。
4. 驱动/共享内存返回地址不满足 CPU 对齐要求。

# 3. 最小排查步骤

## 3.1 获取 FastPass 证据

```bash
rtk bash tools/debug/gdb-core-fastpass.sh --bin <bin.debug.full> --core <core>
```

关注：

1. `Program terminated with signal SIGBUS`
2. `#0` 函数及文件行号
3. 当前访问地址（寄存器/局部变量）

## 3.2 升级 DeepPass 看栈与指令

```bash
rtk bash tools/debug/gdb-core-deeppass.sh --bin <bin.debug.full> --core <core>
```

重点检查：

1. `x/32wx $sp` 是否出现明显越界痕迹
2. `disassemble /m` 中崩溃指令是否为宽访存（4/8 字节）

# 4. 代码层检查清单

1. 是否对可能未对齐内存做了直接结构体解引用。
2. 是否应改为字节拷贝后再解析（避免未对齐读取）。
3. 是否存在大块 `memcpy` 写越界污染后续访问。
4. `mmap` 数据是否在读期间被并发截断/重映射。

# 5. 修复建议

1. 统一使用安全读取辅助函数（字节级或对齐安全宏）。
2. 边界前置校验（长度、剩余字节、目标偏移）。
3. 关键路径增加 guard 日志（大小、偏移、对齐状态）。

# 6. 验证要求

1. 同场景复现：确认 `SIGBUS` 消失。
2. 回归关键功能：确认无新性能/行为回归。
3. 输出 crash 签名前后对比，确认签名变化符合预期。
