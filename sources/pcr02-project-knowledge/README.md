# pcr02-project-knowledge

## 定位

- Source ID: `pcr02-project-knowledge`
- Hub source path: `sources/pcr02-project-knowledge`
- Role: `hub-canonical-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hub-canonical`
- Source strategy: `hub-canonical-copy-docs`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-project-knowledge 的旧正文副本已按终态剪枝；Hub 仅保留 source control、hash/provenance、owner decision 和已落地的 canonical 项目正文。旧项目 knowledge 路径不再作为知识正文入口。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

project-specific 内容不能直接提升团队标准。

## 维护入口

- 清单：`sources/pcr02-project-knowledge/inventory.jsonl`
- 覆盖：`sources/pcr02-project-knowledge/coverage.md`
- 策略：`sources/pcr02-project-knowledge/source-policy.md`
