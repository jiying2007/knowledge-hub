# Knowledge Hub owner / automation / template hardening 2026-06-21

## 结论

本轮压实 4 个可由 Codex 自动完成的终态 gap：

- owner 表单校验拒绝把 `routing_owner` 当成真实 `reviewed_by`。
- `knowledge-check` 对 `registry/maintenance-runs.jsonl` 增加自动化安全门禁，要求 automation 记录保持 `enabled=false`、`mode=report-only`、`writes_memory=false`、`writes_team_active_index=false`，并显式填写 `no_memory_write_gate`。
- `knowledge-new.sh` 的普通人工新增入口不再输出可误复制的 `- <source-id>:` 占位行，未知来源保持人工复核。
- `templates/owner-decision-worksheet.md` 改为 owner worksheet 语义，明确它不是 owner decision，不能代签、不能关闭 gate。

## 边界

- 不生成 owner decision。
- 不关闭 PCR02 owner gate。
- 不修改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 变更范围

- `tools/knowledge-owner-gates.sh`
- `tools/knowledge-check.sh`
- `tools/knowledge-new.sh`
- `tools/knowledge-regression.sh`
- `templates/owner-decision-worksheet.md`
- `registry/maintenance-runs.jsonl`
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`

## 回归新增

- `owner-form-routing-owner-reviewed-by-gate`
- `automation-report-only-safety-gate`

同时收紧既有 `manual-entry-project-index-hint`，要求未知 source 不输出可复制的 `- <source-id>:` by-source 占位行。

## 证据

本 manifest 的验证命令：

```bash
rtk bash -n tools/knowledge-check.sh
rtk bash -n tools/knowledge-owner-gates.sh
rtk bash -n tools/knowledge-new.sh
rtk bash -n tools/knowledge-regression.sh
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-21
rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-21
rtk git diff --check
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-21
```

## 剩余阻塞

PCR02 `pcr02-project-docs` 仍有 7 个 owner gate open。该状态是人工语义门禁，不是本轮工具失败。
