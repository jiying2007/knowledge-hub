---
title: prog_pcr02 core 调试的 GDB 选择经验
doc_type: debug-note
knowledge_type: incident-learning
maturity: candidate
status: archived
owner: team-core
created: 2026-07-02
last_updated: 2026-07-02
tags: [pcr02, prog_pcr02, core, gdb, sigmastar, arm-linux-gnueabihf]
related:
  - ../../current/runbooks/project-debug-tools-guide.md
  - ../../../../domains/embedded/runbooks/gdb-debug-guide.md
  - ../../../../domains/embedded/skills/offline-gdb-core-debug/SKILL.md
---

# prog_pcr02 core 调试的 GDB 选择经验

## 背景

PCR02 现场 core 分析中，目标进程为 `/customer/bin/prog_pcr02`，core 文件形如 `/tmp/core-prog_pcr02-*`。若选错 GDB，可出现无法读取 ARM core registers、缺运行库、ABI 不匹配或 DWARF 兼容性不足，导致 backtrace 不可信或无法继续分诊。

## 结论

PCR02/SigmaStar SSC305 glibc ARM Linux core 默认使用以下平台 GDB：

```bash
/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb
```

不要优先使用 `/usr/bin/gdb`、`arm-none-eabi-gdb` 或旧 `/opt/gcc-linaro.../arm-linux-gnueabihf-gdb`。这些候选在本类 core 上可能无法读取寄存器、依赖缺失，或因 ABI/DWARF 差异使符号级分析低置信。

## 固化规则

1. 用户给出 GDB 路径时，以用户路径为硬约束。
2. 未给出路径时，先检查上述平台 GDB 是否存在并可执行。
3. GDB 必须能打开 core 并读取 ARM registers，才能继续解释 PC、LR、SP、寄存器和 backtrace。
4. 下源码行级结论前，必须匹配 core、设备 `/customer/bin/prog_pcr02`、本地二进制、debug symbol 和关键 shared library 的 BuildID/MD5。
5. BuildID 或符号不匹配时，只输出函数/偏移级低置信结论，不做源码行级断言。

## 本次证据摘要

- 正确 GDB 能读取 ARM core 并完成寄存器/反汇编分析。
- `/usr/bin/gdb` 对 ARM Linux core register note 不可信。
- `arm-none-eabi-gdb` 属于 bare-metal ABI 家族，不应作为 glibc Linux core 的默认候选。
- 旧 `/opt` 交叉 GDB 存在运行库和 DWARF 兼容性风险，应降级为备选或禁用。

## 后续维护

若工具链路径变化，先更新 `projects/pcr02/current/runbooks/project-debug-tools-guide.md` 和 `domains/embedded/skills/offline-gdb-core-debug/SKILL.md`，再同步 Codex managed skill 源文件。
