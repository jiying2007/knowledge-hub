---
name: field-issue-intake-normalizer
description: 将现场问题、客户反馈、日志片段、崩溃现象和复现描述整理为可排查输入包，避免遗漏版本、环境、时间线、证据和验收标准。
version: 1.0.0
last_updated: 2026-05-18
---

# Field Issue Intake Normalizer

## 1. 触发条件

- 用户提供现场问题、客户反馈、零散日志、崩溃现象或“帮我整理问题单”。
- 输入材料混乱，需要转为可执行排查包。

## 2. 处理范围

- 处理问题背景、版本、环境、复现步骤、实际/预期、影响范围、证据路径和下一步动作。
- 不把客户敏感信息、私有路径或原始大日志写入长期知识库。

## 3. 工作流

1. 提取现象、触发条件、预期、实际、影响范围和严重程度。
2. 标记缺失字段：版本、commit、SDK、设备、配置、时间线、日志、core、manifest。
3. 判断应路由到 crash、media、AI、resource leak、build release 或 artifact audit。
4. 输出标准化问题单和下一步证据采集命令。
5. 明确哪些信息只归档，不进入长期 memory。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出问题单摘要、已知事实、缺失证据、推荐 skill、下一步命令和敏感信息处理建议。
