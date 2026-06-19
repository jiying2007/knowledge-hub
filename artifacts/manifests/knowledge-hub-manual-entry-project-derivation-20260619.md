# Knowledge Hub manual entry project derivation 2026-06-19

## 结论

`knowledge-new.sh` 现在会从 `--domain projects/<project>` 自动推导项目名。人工新增项目域条目时，即使未传 `--project`，`indexes/by-project.md` 草稿也会使用正确项目段；如果 `--project` 与 `--domain` 推导出的项目不一致，向导只读输出 warning，提醒人工确认。

这个修复降低人工新增项目条目的参数负担，不创建、不修改、不提交任何文件。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| MPD-001 | 项目域条目需要 `--domain projects/<project>`，但 `by-project` 草稿还依赖额外 `--project`。 | 人工忘记 `--project` 时，项目索引草稿出现 `<project>` 占位符。 | 从 `--domain projects/<project>` 自动推导项目名。 |
| MPD-002 | `--project` 与 `--domain` 不一致时没有提示。 | 维护者可能把 registry domain 和项目导航入口写到不同项目。 | 输出 warning，不阻断、不自动修复。 |
| MPD-003 | 手工行为需要可回归。 | 后续改动可能恢复占位符或静默接受不一致。 | 新增 `manual-entry-project-derived-from-domain` 回归场景。 |

## 决策

- `--domain projects/<project>` 是项目名推导权威。
- `--project` 为空时自动使用 domain 中的项目名。
- `--project` 不为空且不一致时只读提示 warning；不阻断命令，避免破坏现有人工流程。
- 非项目域不推导项目名，也不输出 `by-project` 草稿。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --id pcr02-derived-project-runbook --path domains/projects/pcr02/current/runbooks/derived.md` | 0 | 通过；未传 `--project` 时，项目索引草稿使用 `pcr02` | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-project-derivation-20260619` |
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project wrong-project --id pcr02-mismatch-runbook --path domains/projects/pcr02/current/runbooks/mismatch.md` | 0 | 通过；输出 `--project` 与 `--domain` 不一致 warning | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-project-derivation-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；9 个回归场景全部 pass，包含新增 `manual-entry-project-derived-from-domain` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-project-derivation-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-project-derivation-20260619` |

## 边界

- 不自动创建正文、registry、migration 或 index。
- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
