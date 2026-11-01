# codex-history

## 定位

- Source ID: `codex-history`
- Hub source path: `sources/codex-history`
- Role: `hub-runtime-input`
- Authority: `runtime-input-provenance`
- Final disposition: `runtime-input-reference-only`
- Source strategy: `runtime-input-index-summary-only`
- Owner: `leiwenjun`
- Review after: `2026-11-30`

## Hub 管理方式

codex-history 只作为运行态输入 provenance；Hub source path 为 sources/codex-history，不把 raw history 行复制为正文。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

raw history 行不能直接提升为 active fact。

## 维护入口

- 清单：`sources/codex-history/inventory.jsonl`
- 覆盖：`sources/codex-history/coverage.md`
- 策略：`sources/codex-history/source-policy.md`

## 本次登记契约复核

2026-10-31 由 Codex 核验登记控制面及只读策略；不复核原始输入正文、不代表 owner 签收。证据：`governance/product/validation/provider-58aa0dc4e4ce02e8c6ecd95d00989fcd1ebf08024b88ba8bf9e080d298206d35.md`。
