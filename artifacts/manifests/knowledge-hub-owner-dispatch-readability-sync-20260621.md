# Knowledge Hub owner dispatch readability sync 2026-06-21

## 结论

本轮继续压实 Knowledge Hub 终态中的人工 owner 签收路径和中文长期维护路径。

主要结果：

- `knowledge-owner-gates.sh --summary` 新增 `owner_dispatch` 只读分派包，按 owner 聚合 open gate、worksheet、source path、forms-jsonl、validate-forms、landing-plan 和 next focus 命令。
- README / tools README / migration template 同步 2026-06-21 后已经生效的中文可读性字段：`translation_status`、`terminology_status` 和 migration `notes_zh`。
- README / tools README / migration template / `knowledge-new.sh` 中的可复制检查命令改成 `rtk bash ~/knowledge-hub/tools/...` 入口，降低从非仓库 cwd 复制后失败的风险。
- 只读复扫 PCR02 docs/tools/knowledge/app_product_test/scratch 后确认：按 2026-06-20 closeout 的全深度排除 `.git` 口径，当前 source 计数与既有 closeout 证据一致；`maxdepth` 摘要属于不同扫描口径，不作为漂移证据覆盖历史 manifest。

本轮不生成 owner decision，不关闭 PCR02 owner gate，不修改 PCR02 源项目 docs / tools / knowledge / app_product_test / scratch / source tree，不复制 owner-gated source 正文，不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`，不启用自动化写操作，不写 `~/.codex/memories`。

## 处理的 Gap

| gap_id | gap_type | evidence | 当前影响 | 本轮动作 | 状态 |
|---|---|---|---|---|---|
| ODR-20260621-001 | manual-maintenance | owner gate summary 需要人工从 rows 中自行过滤每个 owner 的命令 | 多 owner 签收时容易复制错 owner、漏 validate 或 landing-plan 命令 | 增加 `owner_dispatch` 分派包，JSON 和文本 summary 均暴露 | applied |
| ODR-20260621-002 | Chinese-readability | README / tools README 未完整说明 `translation_status`、`terminology_status` 和 `notes_zh` | 人工按旧清单新增后才在 knowledge-check 暴露缺字段 | 同步 README、tools README 和 migration template | applied |
| ODR-20260621-003 | tooling | source `--check`、`knowledge-new.sh` 向导和 migration template 仍有 repo-relative `tools/knowledge-check.sh` 示例 | 从非仓库 cwd 复制后命令可能失败 | 改为 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh ...` | applied |
| ODR-20260621-004 | source-coverage | 本轮 `maxdepth` 摘要与 2026-06-20 closeout 全深度口径不同 | 容易误判 source coverage 计数漂移 | 复跑 closeout 同口径计数并记录无漂移证据 | applied |

## Owner Dispatch 契约

`knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` 的 `owner_summary.owner_dispatch[]` 每行包含：

- `owner`
- `source_id`
- `row_count`
- `open_count`
- `resolved_count`
- `worksheet_ids`
- `source_paths`
- `summary_command`
- `forms_jsonl_command`
- `validate_forms_command_template`
- `landing_plan_command_template`
- `next_focus_command`
- `notes_zh`

这些字段只用于人工分派和签收，不表示 owner 已签收，不写文件，不关闭 gate。

## Source 复扫结论

本轮只读复扫结果：

| source | 2026-06-20 closeout 口径 | 2026-06-21 同口径复扫 | 结论 |
|---|---:|---:|---|
| `pcr02-project-docs` | 32 | 32 | 一致 |
| `pcr02-project-tools` | 19 | 19 | 一致 |
| `pcr02-project-knowledge` | 191 | 191 | 一致 |
| `pcr02-product-test` | 127 | 127 | 一致 |
| `pcr02-project-scratch` | 8 | 8 | 一致 |

`pcr02-module-agent-rules` 和 `pcr02-project-root-artifacts` 已在既有 boundary manifest 中显式记录历史 / 当前口径差异，本轮不覆盖历史事实。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc 'base=...; for d in tools knowledge app_product_test scratch; do ...; done'` | 0 | 通过；全深度排除 `.git` 后计数为 `tools=19`、`knowledge=191`、`app_product_test=127`、`scratch=8`，与 2026-06-20 closeout 口径一致。 | PCR02 source roots | Source metadata | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash -lc 'base=...; find "$base/docs" ... | wc -l'` | 0 | 通过；`docs=32`，与 PCR02 docs 分类基线一致。 | PCR02 docs source | Source metadata | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 通过；owner gate helper shell wrapper 语法有效。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 通过；人工新增向导 shell wrapper 语法有效。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 0 | 通过；输出 7 个 open gate、6 个 owner dispatch rows，project-owner 分派包包含 2 个 open gate 及 forms-jsonl/validate/landing-plan/focus 命令。 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-new.sh --help` | 0 | 通过；help 示例使用 `rtk bash ~/knowledge-hub/tools/...` cwd-stable 入口。 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk rg -n "translation_status|terminology_status|notes_zh|complete-except-owner-review|needs-owner-review|~/knowledge-hub/tools/knowledge-check.sh --dry-run" README.md tools/README.md templates/README.md templates/migration-record.md tools/knowledge-new.sh registry/schema.md` | 0 | 通过；人工维护入口已暴露语言/术语状态、migration `notes_zh` 和 cwd-stable check 示例。 | README / templates / `knowledge-new.sh` | Documentation + Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；全仓 0 errors / 0 warnings。 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 通过；60 个回归场景全部 pass，owner summary 场景覆盖 `owner_dispatch`。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 | 通过预期阻断；`final_status=needs-owner-review`，自动治理面完成，唯一 blocker 为 7 个 PCR02 owner gates。 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-owner-dispatch-readability-sync-20260621` |
| `rtk git diff --check` | 0 | 通过；无 whitespace error。 | git diff | Git | `knowledge-hub-owner-dispatch-readability-sync-20260621` |

## 边界

- 不修改 PCR02 源项目。
- 不复制 owner-gated source 正文。
- 不生成或伪造 owner decision。
- 不关闭任何 owner gate。
- 不把 PCR02 project-specific 内容提升为团队标准。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。
