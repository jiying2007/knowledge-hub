# Automation Policy

## Default

所有 Knowledge Hub 自动化默认：

- `enabled=false`
- `mode=report-only`
- `sandbox=read-only`
- `approval_policy=manual`

## Allowed

- 只读扫描。
- 生成报告。
- 生成候选。
- 检查 registry。
- 检查断链。
- 检查过期 review。
- 检查疑似 secret。
- 记录 automation run summary。

## Forbidden

- 删除文件。
- 写入 `~/.codex/memories`。
- 提升到团队规范。
- 修改 `AGENTS.md`。
- commit 或 push。
- 发布远端。
- 发送消息或提交表单。
- 使用 `knowledge-* --apply`。

## Human Approval Required

- `knowledge-capture --apply`
- `knowledge-promote --apply`
- `knowledge-retire --apply`
- 正文迁移。
- 修改团队 standards。
- 写 memory candidate。
- 将候选提升到 AGENTS、skill 或 workflow。
