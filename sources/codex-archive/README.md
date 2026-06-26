# codex-archive

## 定位

- Source ID: `codex-archive`
- Hub source path: `sources/codex-archive`
- Role: `hub-canonical-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hub-canonical`
- Source strategy: `hub-canonical-copy-docs`
- Owner: `leiwenjun`
- Review after: `2026-09-20`

## Hub 管理方式

codex-archive 已终态归位到 Hub Codex archive 终态目录；旧 Codex archive 入口不再作为新增归档或默认查询入口。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

历史 Codex archive 记录不能直接提升为 active governance rule。

## 维护入口

- 清单：`sources/codex-archive/inventory.jsonl`
- 覆盖：`sources/codex-archive/coverage.md`
- 策略：`sources/codex-archive/source-policy.md`
