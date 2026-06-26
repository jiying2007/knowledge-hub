# codex-session-index

## 定位

- Source ID: `codex-session-index`
- Hub source path: `sources/codex-session-index`
- Role: `hub-runtime-input`
- Authority: `runtime-input-provenance`
- Final disposition: `runtime-input-reference-only`
- Source strategy: `runtime-input-index-primary`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

codex-session-index 只作为运行态索引输入 provenance；Hub source path 为 sources/codex-session-index。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

session index 只说明历史记录位置，不替代项目事实验证。

## 维护入口

- 清单：`sources/codex-session-index/inventory.jsonl`
- 覆盖：`sources/codex-session-index/coverage.md`
- 策略：`sources/codex-session-index/source-policy.md`
