# codex-archive-registry

## 定位

- Source ID: `codex-archive-registry`
- Hub source path: `sources/codex-archive-registry`
- Role: `hub-canonical-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hub-canonical`
- Source strategy: `hub-canonical-copy-docs-and-artifacts`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

codex-archive-registry 已终态归位到 Hub Codex archive registry 终态目录；旧 archive registry 不再作为 active source path。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

旧 registry open session 不自动成为当前项目事实。

## 维护入口

- 清单：`sources/codex-archive-registry/inventory.jsonl`
- 覆盖：`sources/codex-archive-registry/coverage.md`
- 策略：`sources/codex-archive-registry/source-policy.md`
