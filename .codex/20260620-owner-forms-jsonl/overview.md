# Overview

本轮切片继续压实 owner review 工作流的人工维护面。

现状：`--forms` 文本模式已经能打印可复制 JSONL skeleton，但 stdout 仍包含 Markdown 标题、说明和验证提示，适合人工阅读，不适合作为干净 JSONL 输入直接保存或管道处理。

设计：新增 `--forms-jsonl`，复用 `make_decision_form`，只输出 open rows 的紧凑 JSONL。该模式仍然只读，不填 owner 字段，不落地任何 owner decision。

并行方式：两个 subagent 只读审查 CLI 契约和回归缺口，主 agent 负责补丁、登记和最终验证。
