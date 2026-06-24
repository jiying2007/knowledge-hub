# codex-session-index

## 定位

- Source ID: `codex-session-index`
- Source path: `~/.codex/session_index.jsonl`
- Role: `codex-session-source`
- Authority: `codex-raw-session-history`
- Final disposition: `hub-main-source`
- Migration strategy: `hub-main-index-primary`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

Codex session index 作为跨项目、跨会话恢复主索引来源。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

session index 只说明历史记录位置，不替代项目事实验证。

## 维护入口

- 清单：`sources/codex-session-index/inventory.jsonl`
- 覆盖：`sources/codex-session-index/coverage.md`
- 计划：`sources/codex-session-index/migration-plan.md`
