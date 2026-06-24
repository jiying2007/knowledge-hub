# pcr02-project-agent-config

## 定位

- Source ID: `pcr02-project-agent-config`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- Role: `project-agent-config-source`
- Authority: `legacy-project-agent-config`
- Final disposition: `artifact-ref-registered`
- Migration strategy: `config-artifact-ref-report-only-automation-boundary`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 agent config 作为配置/自动化边界登记，不执行 setup/script，不作为 active 团队规则。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

配置可能包含外部依赖或敏感信息；启用自动化前需授权和审计。

## 维护入口

- 清单：`sources/pcr02-project-agent-config/inventory.jsonl`
- 覆盖：`sources/pcr02-project-agent-config/coverage.md`
- 计划：`sources/pcr02-project-agent-config/migration-plan.md`
