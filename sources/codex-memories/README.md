# codex-memories

## 定位

- Source ID: `codex-memories`
- Source path: `~/.codex/memories`
- Role: `auxiliary-memory-source`
- Authority: `auxiliary-recall-only`
- Final disposition: `auxiliary-recall-only`
- Migration strategy: `auxiliary-recall-only-no-memory-write`
- Owner: `leiwenjun`
- Review after: `2026-09-20`

## Hub 管理方式

Codex memories 默认只作为辅助召回；写入 memory 必须先有授权账本记录。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

memory candidate 不得静默进入长期记忆或 active facts。

## 维护入口

- 清单：`sources/codex-memories/inventory.jsonl`
- 覆盖：`sources/codex-memories/coverage.md`
- 计划：`sources/codex-memories/migration-plan.md`
