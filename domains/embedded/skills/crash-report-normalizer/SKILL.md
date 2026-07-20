---
name: crash-report-normalizer
description: 崩溃分析输出规范化技能，统一结论、证据、置信度与验证命令结构。
version: 1.0.0
last_updated: 2026-05-15
---

# Crash Report Normalizer Skill

## 1. 触发条件

- 用户要求“整理崩溃报告/统一输出模板/汇总多次 core 分析结果”。
- 分析结果来自 gdb fastpass/deeppass 或 ASAN 日志。
- 需要交付团队可复用的问题单内容。

## 2. 处理范围

- 仅做输出结构规范化，不替代底层证据采集。
- 可接收文本日志、摘要笔记、脚本输出作为输入。
- 输出面向工程执行，不写空泛结论。

## 3. 强制检查

1. 结论必须包含 signal、线程/函数、文件行号（若可得）。
2. 证据必须可回溯到命令或日志来源。
3. 置信度必须分级（高/中/低）并说明依据。
4. 必须包含最小验证命令。
5. 代码风格参考 `domains/embedded/standards/c-coding-standards.md` 的冻结历史基线；如与当前项目规范冲突，以项目规范为准。
6. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 固定结构：
  1. 崩溃结论
  2. 关键证据（最多 5 条）
  3. 根因假设（含置信度）
  4. 修复建议（1 到 3 条）
  5. 验证命令
