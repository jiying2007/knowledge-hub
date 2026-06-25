# codex-raw-sessions

## 定位

- Source ID: `codex-raw-sessions`
- Hub source path: `sources/codex-raw-sessions`
- Retired origin provenance: `registry/sources.json` origin_path; `registry/source-tombstones.jsonl`
- Role: `hub-runtime-input`
- Authority: `runtime-input-provenance`
- Final disposition: `runtime-input-not-migrated`
- Migration strategy: `runtime-input-reference-summary-only`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

codex-raw-sessions 只作为运行态输入 provenance；Hub source path 为 sources/codex-raw-sessions，不复制 raw session 全文。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

raw session 可能含上下文噪音或敏感信息，不进入正文层。

## 维护入口

- 清单：`sources/codex-raw-sessions/inventory.jsonl`
- 覆盖：`sources/codex-raw-sessions/coverage.md`
- 计划：`sources/codex-raw-sessions/migration-plan.md`
