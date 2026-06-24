---
name: asan-crash-triage
description: ASAN 崩溃日志低 token 分诊流程，优先输出可执行结论与复现验证动作。
version: 1.0.0
last_updated: 2026-05-15
---

# ASAN Crash Triage Skill

## 1. 触发条件

- 用户提供 ASAN 崩溃日志并要求快速定位。
- 日志出现 `heap-buffer-overflow/use-after-free/stack-buffer-overflow`。
- 需要从 ASAN 地址映射到函数/源码行号。

## 2. 处理范围

- 处理 ASAN 日志离线分诊与符号化，不替代完整功能测试。
- 优先使用 `tools/debug/asan-log-symbolize.sh` 做地址映射。
- 必要时与 `offline-gdb-core-debug` 组合交叉验证。

## 3. 强制检查

1. 先确认日志、二进制、符号文件来自同一构建版本。
2. 先给结论摘要，再给证据点，避免贴整段日志。
3. 默认提取并输出：
   - 错误类型
   - 第一现场函数
   - 首个可定位源码行
4. 若符号化失败，必须显式标注“不匹配/无法符号化”的原因。
5. 代码风格遵循 `$EMBEDDED_KNOWLEDGE_HOME/docs/standards/c-coding-standards.md`。
6. 结构与验证流程遵循 `docs/standards/agent-skill-engineering-baseline.md`。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出顺序固定：
  1. ASAN 错误结论
  2. 关键证据（最多 5 条）
  3. 根因假设与置信度
  4. 最小修复建议
  5. 验证命令（含符号化命令）
