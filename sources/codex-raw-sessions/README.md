# codex-raw-sessions

## 定位

- Source ID: `codex-raw-sessions`
- Source path: `~/.codex/sessions`
- Role: `codex-session-source`
- Authority: `codex-raw-session-history`
- Final disposition: `hub-main-source`
- Migration strategy: `hub-main-reference-summary-only`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

Codex raw sessions 进入 Hub 主库 source registry；只做引用、摘要和证据定位。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

raw session 可能包含上下文噪音或敏感信息，不进入正文层。

## 维护入口

- 清单：`sources/codex-raw-sessions/inventory.jsonl`
- 覆盖：`sources/codex-raw-sessions/coverage.md`
- 计划：`sources/codex-raw-sessions/migration-plan.md`
