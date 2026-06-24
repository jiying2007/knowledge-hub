# codex-archive-registry

## 定位

- Source ID: `codex-archive-registry`
- Source path: `~/codex/docs/archive/_registry`
- Role: `codex-archive-registry-source`
- Authority: `codex-archive-registry`
- Final disposition: `hub-main-source`
- Migration strategy: `hub-main-registry-federated-migration`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

Codex archive registry 进入 Hub 主库 source registry，用于吸收 project/topic/session/workstream 索引。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

archive registry 的 open session 不自动成为当前项目事实。

## 维护入口

- 清单：`sources/codex-archive-registry/inventory.jsonl`
- 覆盖：`sources/codex-archive-registry/coverage.md`
- 计划：`sources/codex-archive-registry/migration-plan.md`
