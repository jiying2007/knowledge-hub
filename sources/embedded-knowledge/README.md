# embedded-knowledge

## 定位

- Source ID: `embedded-knowledge`
- Hub source path: `sources/embedded-knowledge`
- Retired origin path: `~/embedded/knowledge`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-copy-docs`
- Owner: `team-core`
- Review after: `2026-09-20`

## Hub 管理方式

embedded-knowledge 已完整迁移到 Hub canonical embedded domain。正文权威位于 `domains/embedded/*`，`sources/embedded-knowledge` 只保留 source 控制面；旧路径只保留 `origin_path` / tombstone provenance。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- 旧过渡快照目录已被清空并删除；不得作为新增正文、查询入口或自动化目标。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

历史 team knowledge 不自动成为 active standard；后续提升仍需按 Hub owner/review 规则拆分。

## 维护入口

- 清单：`sources/embedded-knowledge/inventory.jsonl`
- 覆盖：`sources/embedded-knowledge/coverage.md`
- 计划：`sources/embedded-knowledge/migration-plan.md`
- 正文：`domains/embedded/`
