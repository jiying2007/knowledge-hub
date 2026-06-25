---
name: sigbus-memory-triage
description: SIGBUS/SIGSEGV 内存访问异常分诊技能，优先定位对齐与映射边界问题。
version: 1.0.0
last_updated: 2026-05-15
---

# SIGBUS Memory Triage Skill

## 1. 触发条件

- 崩溃信号为 `SIGBUS`（或疑似未对齐访问导致的 `SIGSEGV`）。
- gdb 回溯指向内存读写、结构体解析、mmap 访问路径。
- 用户要求快速内存类崩溃归因。

## 2. 处理范围

- 仅处理内存访问异常分诊与证据收敛。
- 优先检查对齐、长度边界、偏移合法性。
- 必要时联动 `offline-gdb-core-debug` 获取线程与指令证据。

## 3. 强制检查

1. 必须输出崩溃信号、崩溃函数、源码行号。
2. 必须判断是否存在未对齐访问风险。
3. 必须判断是否存在映射越界/底层文件截断风险。
4. 必须给出“边界校验/字节读取替代”修复建议。
5. 代码风格遵循 `$EMBEDDED_KNOWLEDGE_HOME/docs/standards/c-coding-standards.md`。
6. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出顺序：
  1. 结论（SIGBUS 根因方向）
  2. 关键证据（最多 5 条）
  3. 根因假设与置信度
  4. 修复建议（1 到 3 条）
  5. 验证命令
