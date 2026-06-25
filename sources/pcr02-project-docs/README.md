# pcr02-project-docs

## 定位

- Source ID: `pcr02-project-docs`
- Hub source path: `sources/pcr02-project-docs`
- Retired origin path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-copy-docs-and-artifacts`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-project-docs 的旧正文副本已按终态剪枝；Hub 仅保留 source control、hash/provenance、owner decision 和已落地的 `projects/pcr02/` canonical 项目正文。旧项目 docs 路径只保留 origin_path，不再作为新增归档或知识入口。

## 边界

- `path` 指向 Hub 内 source 控制目录；旧外部路径只允许作为 `origin_path` provenance。
- Hub 统一管理 source 的清单、覆盖状态、迁移证据、退役策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

owner-gated 历史内容仍不能绕过 owner/review 直接提升 active。

## 维护入口

- 清单：`sources/pcr02-project-docs/inventory.jsonl`
- 覆盖：`sources/pcr02-project-docs/coverage.md`
- 计划：`sources/pcr02-project-docs/migration-plan.md`
