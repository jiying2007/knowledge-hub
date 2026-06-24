# pcr02-project-knowledge

## 定位

- Source ID: `pcr02-project-knowledge`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge`
- Role: `project-current-knowledge-source`
- Authority: `legacy-project-current-knowledge`
- Final disposition: `mixed-terminal-coverage`
- Migration strategy: `classify-first-secret-boundary-tool-ref`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 knowledge 作为项目知识子源登记；secret/config/tool-ref 需保持边界。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

含配置和 standards-like doc，不能直接提升团队标准。

## 维护入口

- 清单：`sources/pcr02-project-knowledge/inventory.jsonl`
- 覆盖：`sources/pcr02-project-knowledge/coverage.md`
- 计划：`sources/pcr02-project-knowledge/migration-plan.md`
