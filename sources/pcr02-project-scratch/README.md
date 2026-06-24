# pcr02-project-scratch

## 定位

- Source ID: `pcr02-project-scratch`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch`
- Role: `project-scratch-source`
- Authority: `legacy-project-scratch`
- Final disposition: `archive-only-registered`
- Migration strategy: `archive-only-no-memory-write`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 scratch 只作为历史证据或 handoff 参考；memory candidates 不写 memory。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

handoff、memory candidates 和 session notes 若直接提升会污染 active facts。

## 维护入口

- 清单：`sources/pcr02-project-scratch/inventory.jsonl`
- 覆盖：`sources/pcr02-project-scratch/coverage.md`
- 计划：`sources/pcr02-project-scratch/migration-plan.md`
