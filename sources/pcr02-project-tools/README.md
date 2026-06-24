# pcr02-project-tools

## 定位

- Source ID: `pcr02-project-tools`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools`
- Role: `project-current-tools-source`
- Authority: `legacy-project-current-tools`
- Final disposition: `mixed-terminal-coverage`
- Migration strategy: `reference-tool-validation-owner-gated-boundary`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 tools 作为当前项目工具源登记；脚本正文不默认复制，自动化默认 report-only，授权后可 apply-with-review。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

memory 自动化脚本不能无授权写 memory。

## 维护入口

- 清单：`sources/pcr02-project-tools/inventory.jsonl`
- 覆盖：`sources/pcr02-project-tools/coverage.md`
- 计划：`sources/pcr02-project-tools/migration-plan.md`
