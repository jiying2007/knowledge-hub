# pcr02-project-docs

## 定位

- Source ID: `pcr02-project-docs`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Role: `project-current-docs-source`
- Authority: `legacy-project-current-docs`
- Final disposition: `mixed-terminal-coverage`
- Migration strategy: `pcr02-docs-mixed-copy-reference-artifact-owner-gated`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 project docs 32/32 已完成治理覆盖；owner-gated 文件仍需授权或 owner decision 才能落地。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

控制面闭合不等于 owner 决策完成。

## 维护入口

- 清单：`sources/pcr02-project-docs/inventory.jsonl`
- 覆盖：`sources/pcr02-project-docs/coverage.md`
- 计划：`sources/pcr02-project-docs/migration-plan.md`
