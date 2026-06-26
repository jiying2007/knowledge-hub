# codex-memories

## 定位

- Source ID: `codex-memories`
- Hub source path: `sources/codex-memories`
- Role: `hub-runtime-input`
- Authority: `runtime-input-provenance`
- Final disposition: `runtime-input-not-migrated`
- Migration strategy: `runtime-input-no-copy-no-memory-write`
- Owner: `leiwenjun`
- Review after: `2026-09-20`

## Hub 管理方式

codex-memories 不是迁移正文源；Hub 只保留 sources/codex-memories 控制面和 runtime provenance，禁止自动写 memory。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

memory candidate 不得静默进入长期记忆或 active facts。

## 维护入口

- 清单：`sources/codex-memories/inventory.jsonl`
- 覆盖：`sources/codex-memories/coverage.md`
- 策略：`sources/codex-memories/source-policy.md`
