# Knowledge Hub Owner Decision Form Validation 2026-06-19

## 目标

为 owner 回填的 JSONL 决策表增加只读校验入口，在人工落地任何 owner decision 前先发现漏字段、错误枚举、日期格式错误和 source identity 不匹配，降低 owner-gated 闭环时的返工和误提升风险。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| ODV-001 | `--forms` 已能输出填报骨架，但 owner 回填后还缺少只读校验入口。 | 缺字段或错误 owner_decision 可能进入人工落地流程。 | 新增 `--validate-forms <jsonl>`。 |
| ODV-002 | owner 可能分批回填 1 个或几个 row。 | 一次性要求覆盖 7 个 row 会让闭环成为瓶颈。 | 校验只检查提交文件中出现的 forms，不要求一次覆盖全部 open rows。 |
| ODV-003 | 校验工具不能代替 owner review。 | 自动校验通过可能被误解为语义通过。 | 校验只检查结构、必填字段、枚举和日期；不写文件、不关闭门禁、不提升 active。 |
| ODV-004 | owner 回填的 `source_sha256/source_size` 可能来自旧源文件。 | landing plan 可能基于过期源文件身份继续推进。 | 2026-06-20 起，`--validate-forms` 必须把回填值与只读观测的当前源文件身份匹配。 |

## 决策

- 新增参数：`rtk bash tools/knowledge-owner-gates.sh --validate-forms <owner-decisions.jsonl>`。
- 可与 `--source-id pcr02-project-docs` 组合，限制校验范围。
- 校验规则：
  - `worksheet_id` 必须匹配当前 open owner gate row。
  - `source_id` 和 `source_path` 必须与 worksheet row 一致。
  - `owner_decision` 必须属于 `decision_options`。
  - worksheet 的 `required_owner_fields` 必须非空。
  - `target_decision`、`reviewed_by`、`reviewed_at`、`review_after`、`source_status`、`evidence_refs`、`status_reason` 必须非空。
  - `reviewed_at` 和 `review_after` 必须是 `YYYY-MM-DD`。
  - 当前只读观测的 source identity 必须为 `match`。
  - owner 回填的 `source_sha256` 和 `source_size` 必须等于当前只读观测的 `observed_sha256` 和 `observed_size`。
- 校验只读，不执行 apply。

## 非目标

- 不判断 owner 决策语义正确性。
- 不关闭 owner gate。
- 不写 worksheet、registry、index、migration 或 memory。
- 不迁移 owner-gated 正文。
- 不修改源项目 docs。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `/tmp valid owner form fixture` | 0 | 单个已填 AGENTS.md owner form 校验通过，`form_validation.status=pass`、`error_count=0`。 | `/tmp/kh-owner-form-valid.jsonl` | Positive fixture | owner-decision-form-validation |
| `/tmp invalid owner form fixture` | 1 expected | owner_decision 非允许枚举且 `source_sha256` 为空时校验失败，`form_validation.status=fail`、`error_count=2`。 | `/tmp/kh-owner-form-invalid.jsonl` | Negative fixture | owner-decision-form-validation |
| `rtk bash tools/knowledge-owner-gates.sh --help` | 0 | help 展示 `--validate-forms` 参数。 | `tools/knowledge-owner-gates.sh` | Tool smoke | owner-decision-form-validation |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增 form validation 后全仓门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-decision-form-validation |
| `rtk bash tools/knowledge-search.sh owner-decision-form-validation-applied --json` | 0 | 本制品应可检索，命中 registry、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md`、本 manifest | Knowledge Hub | owner-decision-form-validation |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 2026-06-20 增补通过；新增 `owner-form-source-identity-mismatch` 负例，确认旧 hash 会被拒绝。 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-source-identity-validation-20260620` |

## Fixture 复现契约

正负 fixture 不作为长期正文保存，只记录复现方法和预期结果。

1. 运行 `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms --json`，提取第一个 `decision_forms` 条目。
2. 正向 fixture：填写 `owner_decision=reference-only`、`target_decision=reference-only`、`reviewed_by`、`reviewed_at=2026-06-19`、`source_status`、与 `observed_source_identity` 一致的 `source_sha256` / `source_size`、`current_validity`、`scope_statement`、`applicable_project_version`、非空 `evidence_refs` 和 `status_reason`，写入 `/tmp/kh-owner-form-valid*.jsonl`。
3. 负向 fixture：基于正向 fixture，把 `owner_decision` 改为不在 `allowed_owner_decisions` 中的值，或把 `source_sha256` 改成不等于 `observed_source_identity.observed_sha256` 的旧值，写入 `/tmp/kh-owner-form-invalid*.jsonl`。
4. 运行 `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms /tmp/kh-owner-form-valid*.jsonl --json`，预期退出码为 0，`form_validation.status=pass`。
5. 运行 `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms /tmp/kh-owner-form-invalid*.jsonl --json`，预期退出码为 1，`form_validation.status=fail`。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- review_status：`owner-decision-form-validation-applied`
- 下一次复核内容：若 owner decision landing 规则增加新字段、禁用组合、source identity 语义或跨字段语义约束，同步校验规则。
