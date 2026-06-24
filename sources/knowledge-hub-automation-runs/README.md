# knowledge-hub-automation-runs

## 定位

- Source ID: `knowledge-hub-automation-runs`
- Source path: `registry/automation-runs.jsonl`
- Role: `codex-automation-source`
- Authority: `codex-automation-ledger`
- Final disposition: `hub-main-source`
- Migration strategy: `hub-main-automation-run-ledger`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

Knowledge Hub 以 registry/automation-runs.jsonl 作为跨项目、跨会话 AI 自动化运行账本。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

apply-with-review 必须引用授权账本；默认 report-only。

## 维护入口

- 清单：`sources/knowledge-hub-automation-runs/inventory.jsonl`
- 覆盖：`sources/knowledge-hub-automation-runs/coverage.md`
- 计划：`sources/knowledge-hub-automation-runs/migration-plan.md`
