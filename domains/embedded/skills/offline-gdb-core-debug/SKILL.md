---
name: offline-gdb-core-debug
description: 离线 core 调试最小化工作流，优先低 token 输出崩溃根因与可执行修复路径。
version: 1.0.0
last_updated: 2026-07-02
---

# Offline GDB Core Debug Skill

## 1. 触发条件

- 用户要求分析 `core` 文件、`SIGSEGV/SIGBUS/SIGABRT` 崩溃、`gdb` 离线回溯。
- 用户明确要求“省 token/高效率”进行 core 调试。
- 涉及 `out/arm/app/*.debug(.full)` 与 core 配对分析。

## 2. 处理范围

- 仅做离线 core 分析与证据收敛，不做在线 attach 调试。
- 优先使用交叉 gdb：`/tools/toolchain/.../arm-linux-gnueabihf-gdb`。
- PCR02/SigmaStar SSC305 glibc ARM Linux core 默认使用：`/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb`。
- 不要优先使用 `/usr/bin/gdb`、`arm-none-eabi-gdb` 或旧 `/opt/gcc-linaro.../arm-linux-gnueabihf-gdb`；若这些候选无法读取 ARM registers、缺运行库或 ABI/DWARF 不兼容，必须降级置信度或改用正确平台 GDB。
- 默认两阶段：
  1. `Fast Pass`：只取崩溃线程关键信息，限制回溯深度。
  2. `Deep Pass`：仅在证据不足时补充反汇编、寄存器、跨线程上下文。

## 3. 强制检查

1. 必须确认二进制与 core 配对，若不匹配先显式告警，不直接下结论。
2. 默认禁止输出超长原始回溯；先给“结论 + 证据点 + 风险”。
3. 默认命令模板（Fast Pass）：
   - `rtk <gdb> -batch -ex 'set pagination off' -ex 'set print frame-arguments none' -ex 'set backtrace limit 12' -ex 'frame 0' -ex 'bt 12' -ex 'info locals' -ex 'info registers' -ex 'info threads' <bin> <core>`
4. 仅在必要时追加：
   - `thread apply all bt 2`
   - `disassemble /m <function>`
   - `x/<N>wx $sp`
5. 输出必须包含“下一步最小验证动作”，避免只给静态结论。
6. 代码风格遵循 `$EMBEDDED_KNOWLEDGE_HOME/docs/standards/c-coding-standards.md`。
7. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 固定输出顺序：
  1. 崩溃结论（信号、线程、函数、文件行）
  2. 关键证据（最多 5 条，含寄存器/局部变量/回溯锚点）
  3. 根因假设与置信度
  4. 最小修复建议（1 到 3 条）
  5. 复现场景下的验证命令
- 禁止直接粘贴长段 gdb 原始输出；优先结构化摘要，必要时附短摘录。
