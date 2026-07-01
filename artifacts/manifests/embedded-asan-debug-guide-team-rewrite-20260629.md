# Embedded ASAN Team Rewrite 2026-06-29

## 结论

`domains/embedded/runbooks/asan-debug-guide.md` 已从项目特例材料重写为团队级 ASAN 调试方法论，并在 2026-06-29 经用户明确授权提升为 `active`。

本重写记录保留去项目化证据；active promotion 证据见 `artifacts/manifests/embedded-asan-active-promotion-20260629.md`。本次仍不提升到 `domains/embedded/standards/`，不写 memory，不修改源项目。

## 改动边界

- 团队级正文只保留 ASAN 通用方法：编译 flag 检查、运行期参数、首发错误、BuildID/符号匹配、离线符号化、最小调用链和复现闭环。
- PCR02 的构建变量、程序名、部署路径、运行时库路径和项目命令保留在 `projects/pcr02/current/runbooks/asan-debug-guide.md`。
- `registry/items.jsonl` 中团队级 runbook 条目 `embedded-asan-debug-guide-20260629` 已提升为 `active`。
- 相关索引表达 active discoverability，并引用 active promotion 证据。

## 证据

- PCR02 ASAN split-approved owner decision：`artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl`
- PCR02 项目本地 ASAN runbook：`projects/pcr02/current/runbooks/asan-debug-guide.md`
- 团队级 ASAN runbook：`domains/embedded/runbooks/asan-debug-guide.md`（本重写记录形成时为候选，现已按 active promotion 生效）
- ASAN 离线符号化参考：`domains/embedded/runbooks/asan-offline-symbolize-guide.md`
- 崩溃 triage 参考：`domains/embedded/runbooks/crash-triage-checklist.md`

## 后续增强项

- 非 PCR02 项目的 ASAN 实操记录仍建议补充，用于增强团队 runbook 证据厚度；当前已登记 follow-up：`artifacts/manifests/embedded-asan-non-pcr02-evidence-followup-20260629.md`，但不阻塞当前 active 状态。
