# Knowledge Hub owner-ready 覆盖状态（2026-06-20）

## 结论

- `pcr02-project-docs` 当前 owner decision worksheet 共 7 条。
- 7 条均已有强校验通过的 `owner-ready` 单项签收包。
- 当前覆盖为 `7/7`，缺失 0 条，无效 0 条，重复 0 条。
- 7 条 owner gate 仍全部处于 `open`，`resolved_count=0`。
- 本状态只表示“材料已准备好交给 owner 人工签收”，不表示 owner decision 已落地。

## 强校验口径

每条 worksheet 的 `owner-ready` 覆盖必须同时满足：

- registry item 是 `kind=audit`、`status=reviewing`。
- registry item 的 `review_status=owner-ready-no-decision`。
- registry item 的 `tags` 同时包含 `owner-gate` 和 `owner-ready`。
- registry item 的 `source.source_id/source.source_path` 与 worksheet 一致。
- registry item 的 `path` 指向 `artifacts/manifests/*owner-ready-package-*.md`。
- 对应 `.jsonl` 存在且只有一行。
- package JSONL 的 `classification=single-owner-ready-package`。
- package JSONL 的 `worksheet_id/source_id/source_path` 与 worksheet 一致。
- package JSONL 的 `decision=owner-ready-no-decision`。
- package JSONL 的 `status=reviewing`。
- package JSONL 的 `open_gate_remains=true`。
- package JSONL 的 `observed_source_identity.status=match`。
- 同一 worksheet 恰好只有一个有效 package；缺失、无效、重复都不能计入覆盖。

## 当前覆盖

| worksheet | source path | owner-ready package | package status |
|---|---|---|---|
| `pcr02-owner-decision-worksheet-001` | `AGENTS.md` | `artifacts/manifests/pcr02-agents-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-002` | `standards/diag-command-metadata-standard.md` | `artifacts/manifests/pcr02-diag-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-003` | `runbooks/asan-debug-guide.md` | `artifacts/manifests/pcr02-asan-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-004` | `runbooks/memory-auto-curation-guide.md` | `artifacts/manifests/pcr02-memory-auto-curation-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-005` | `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `artifacts/manifests/pcr02-dvr-plan-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-006` | `reports/2026-05-29-motor-mcu-debug-record.md` | `artifacts/manifests/pcr02-motor-mcu-owner-ready-package-20260620.md` | covered |
| `pcr02-owner-decision-worksheet-007` | `reports/2026-06-16-dvr-record-replay-session-archive.md` | `artifacts/manifests/pcr02-dvr-session-archive-owner-ready-package-20260620.md` | covered |

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不新增或修改 worksheet row。
- 不迁移 source 正文。
- 不修改源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## 验证命令

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash tools/knowledge-status.sh --json
rtk bash tools/knowledge-status.sh --strict --json
rtk bash tools/knowledge-regression.sh --json
rtk git diff --check
```

`tools/knowledge-status.sh --strict --json` 预期仍返回非 0，因为 7 条 owner gate 尚未由 owner 人工签收。
