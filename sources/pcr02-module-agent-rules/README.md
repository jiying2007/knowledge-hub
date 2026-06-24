# pcr02-module-agent-rules

## 定位

- Source ID: `pcr02-module-agent-rules`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- Role: `project-agent-rules-source`
- Authority: `legacy-project-agent-rules`
- Final disposition: `owner-gated-pending-decision`
- Migration strategy: `module-local-owner-gated-rule-reference`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 module AGENTS 作为模块本地规则引用登记，不直接提升为 Hub 根规则或团队标准。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

模块本地约束未经 owner review 直接提升会污染全局规则。

## 维护入口

- 清单：`sources/pcr02-module-agent-rules/inventory.jsonl`
- 覆盖：`sources/pcr02-module-agent-rules/coverage.md`
- 计划：`sources/pcr02-module-agent-rules/migration-plan.md`
