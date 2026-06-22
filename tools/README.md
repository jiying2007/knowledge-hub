# Knowledge Hub Tools

All tools are conservative by default.

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

## 低复杂度入口速查

| 层级 | 使用场景 | 稳定入口 | 边界 |
|---|---|---|---|
| 日常路径 | 人工新增、检索、索引计划和全仓检查 | `knowledge-new.sh`、`knowledge-search.sh`、`knowledge-index-plan.sh`、`knowledge-check.sh --dry-run --json --diagnostics` | 只输出草稿或检查结果，不自动落盘、不伪造 source/owner/evidence |
| owner gate | 导出、校验和审计人工 owner decision JSONL | `knowledge-owner-gates.sh --forms-jsonl`、`--validate-forms`、`--landing-plan`、`--landing-audit` | 不生成 owner decision，不代签 `reviewed_by`，不关闭 gate |
| 终态检查 | 证明自动治理是否闭环，区分 `needs-owner-review` 和 `needs-fix` | `knowledge-final-gate.sh --json` | 必须包含 regression、diff check、strict status；不能只看单个 status pass |
| 高级写入计划 | copy-first、artifact-ref、capture、promote、retire 等需要 reviewed manifest 的流程 | 对应工具默认 dry-run；`--apply` 只允许人工在证据齐备后触发 | 自动化不得删除、发布、提升 active、关闭 owner gate、写 memory 或改源项目 |

- `knowledge-check.sh`: read-only validation.
  覆盖 registry JSON/JSONL 解析、owner/project/topic 登记、source index 和 source coverage 收口、source registry 终态字段、source check/no-check 静态契约、PCR02 Level 2 boundary 内部证据链、owner-gated active 阻断、owner gate 字段阻断、item 日期和 source reference、validation reference 结构与路径、tag/promotion、registry 字段/路径/枚举/边界、migration record、template 必填字段、personal-local active 阻断、AI-generated active 人工复核门禁、2026-06-21 及之后 AI-generated item provenance 字段、source enum、文本知识和 `artifacts/manifests/` secret-pattern scan、核心索引缺失/过期/重复 item ref、`indexes/*.md` 本地 path/glob 引用、`--explain <item-id>` 条目诊断，以及 `--diagnostics` 中文错误分组。JSON 输出包含 `source_coverage_selection`、`source_coverage_health`、`source_check_health` 和 `boundary_health`，用于在通过状态下也能审计 latest closeout 的选择策略、source check/no-check 契约和 PCR02 Level 2 boundary manifest/registry/index 内部证据链。`source_check_health` 不执行 registry check 命令；`boundary_health` 不读取 PCR02 源项目正文。
- `knowledge-check.sh`、`knowledge-status.sh` 和 `knowledge-final-gate.sh` 支持 `--as-of YYYY-MM-DD`；未传时可用环境变量 `KNOWLEDGE_TODAY=YYYY-MM-DD` 固定日期，再未设置时才使用系统日期。`--as-of` 用于复现 `review_after` 过期判断和终态证据，不生成 owner decision，不改变 registry。
- Stale `review_after` values in registry items and registered sources are warnings/status surfaces, not blocking errors; invalid date format and `updated_at < created_at` remain errors.
- `knowledge-search.sh`: read-only text search across registered sources and local domains. It also supports registry-backed filters for local registered items: `--owner`、`--status`、`--kind`、`--domain` and `--source-id`. `--source` keeps the old physical scan source meaning, while `--source-id` filters `registry/items.jsonl` item `source.source_id`.
- `knowledge-status.sh`: read-only control-plane dashboard; summarizes `knowledge-check`, registry counts, source coverage, source check health, boundary health, migrations, stale review dates, owner gate status, structured `owner_gates.owner_dispatch[]`, all-open owner summary commands, by-owner owner summary commands, all-open and by-owner owner forms JSONL commands, all-open and by-owner owner evidence-readiness commands, all-open and by-owner owner filled-form validation command templates, no-write landing-plan command templates, the next open owner gate commands, `final_gate_command` and structured `strict_blockers`. `sources.latest_coverage_selection` records latest source coverage closeout 的选择策略、候选数量、候选路径、按 `YYYYMMDD` 识别的候选、被忽略的非日期候选和选中路径；当前策略是只从 `knowledge-hub-source-coverage-closeout-YYYYMMDD.jsonl` 中按日期取最新。Use `--strict` as a final-state blocker dashboard, but use `final_gate_command` / `knowledge-final-gate.sh --json` as the terminal gate because it also runs regression; `strict_blockers[].commands` contains directly executable commands, while `strict_blockers[].command_templates` contains commands that require replacing placeholders such as `<owner-decisions.jsonl>`.
- `knowledge-final-gate.sh`: repository read-only final-state gate; runs `knowledge-check --diagnostics`, `knowledge-regression --json`, `rtk git diff --check` and `knowledge-status --strict --json` together so terminal validation cannot miss regression drift or whitespace/conflict-marker drift. JSON output includes `today`、`as_of_source`、`automatic_governance`, `owner_recovery`, `final_state_audit` and `gap_map` so automation and humans can distinguish `complete-except-owner-review` from real tool/registry/index/source-coverage failures, and can recover `owner_dispatch[]` plus next open gate directly from final gate output. `final_state_audit.level2_pcr02_candidate_sources.boundary_health` reports PCR02 Level 2 boundary manifest/internal-index health；`final_state_audit.level3_registered_sources.source_check_health` reports source registry check/no-check 契约和 non-rtk/missing 状态。它们都只消费 `knowledge-check` 的只读结果，不执行外部 source check。所有 gate 达到 terminal-ok 前，本命令仍会返回非零。The regression subcommand may create and clean temporary fixtures under `/tmp`; it must not modify Knowledge Hub content, registry, indexes or source project docs.
- `knowledge-doctor.sh`: read-only maintenance helper; runs `knowledge-check --diagnostics`, optional `--explain <item-id>`/search and optional `--owner-gates <source-id>` board without writing files.
- `knowledge-index-plan.sh`: read-only core index planner; prints registry-derived `by-owner`、`by-review-date`、`by-status`、`by-project`、`by-source`、`by-topic`、`by-decision` and `manifest` recovery views without writing files. JSON 输出包含 `source_coverage_selection`，用于追溯 `by_source[*].coverage` 来自哪个 latest closeout manifest；`--section manifest` 用于恢复 manifest 最新项、Markdown/JSONL 配对、行数、证据计数和 unpaired 分类。历史 unpaired 会标记为 `expected` 或 `needs_review`，这是 report-only 恢复视图，不会自动作为 hard failure。
- `knowledge-owner-gates.sh`: read-only owner gate board; prints unresolved owner decision worksheet rows, required owner fields, active exposure status, owner route and read-only current source identity without writing files. Use `--summary` to show all open gates, owner distribution, owner dispatch packages, owner route, source identity counts and focus commands, `--owner <owner>` to filter one exact owner role for assignment, `--checklist` to merge owner intake questions, owner route, hard gates and source identity into a closure checklist, `--forms` to print human-readable context plus copyable owner decision JSONL skeletons, `--forms-jsonl` to print only one compact JSONL skeleton per open row on stdout, `--evidence-readiness` to print read-only field readiness、source identity candidates、owner-ready evidence ref candidates and safe/project command candidates, `--validate-forms <jsonl>` to check filled owner forms including required fields, owner decision enums, target decision candidates, worksheet guardrails, date formats and `source_sha256/source_size` matching the observed current source identity, `--landing-plan` with validation to print a no-write manual landing plan that carries per-step `worksheet_verification_cwd` and `worksheet_verification_commands`, `--landing-audit` with validation to print a no-write worksheet/registry/migration/index manual-delta audit, `--worksheet-id <id>` to focus one owner gate, and `--next-open` to focus the next open owner gate by `review_after, worksheet_id`. `read_only_prefill_candidates` 只给候选值，正式 owner 字段仍需人工填写；`landing_audit` 只提示人工落点，不生成 owner decision、不关闭 gate；`owner_route` comes from `registry/owner-routing.json` and only describes routing/escalation; it does not generate owner decision or replace `reviewed_by`.
- `knowledge-regression.sh`: read-only regression fixture runner; copies the repo to `/tmp`, mutates only temporary fixtures, and verifies key negative gates such as status bucket mismatch and partial owner resolution. It cleans temporary fixtures after each scenario by default, records structured failure details for internal exceptions, emits JSON in `--json` mode, supports `--as-of YYYY-MM-DD` / `KNOWLEDGE_TODAY` for date-sensitive fixture commands, and honors `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES` for low-space preflight.
- `knowledge-inventory.sh`: read-only inventory for registered sources.
- `knowledge-copy-first-plan.sh`: creates a reviewed JSONL copy-first manifest for a registered source; writes only the manifest under `artifacts/manifests/`.
- `knowledge-copy-first.sh`: reviewed copy-first migration from a JSONL manifest; dry-run by default.
- `knowledge-artifact-ref-plan.sh`: creates a JSONL artifact reference manifest with source URI, size and sha256 for non-text source files; it does not copy binary content.
- `knowledge-new.sh`: read-only manual-entry guide; prints template, registry, index, conditional migration, validation steps and copyable manual skeletons without writing files. Supports `--owner <owner>`、`--manual-source-reason <reason>`、`--manual-validation-pending --manual-validation-reason <reason>`、`--generated-by-ai --ai-role <role>`; defaults owner to `leiwenjun`, derives project from `--domain projects/<project>` when `--project` is omitted, honors `KNOWLEDGE_TODAY=YYYY-MM-DD` for deterministic draft dates, and prints UTC default dates plus `summary_zh`、`primary_language`、`source_language`、`translation_status`、`terminology_status`、`review_status`、`evidence_strength` and AI provenance fields for registry drafts. 普通知识新增会提示条件索引：已登记 source 才同步 `indexes/by-source.md`，decision 类条目同步 `indexes/by-decision.md`，未知 source 不伪造 source id。Use `--source` to print source registry、by-source and source coverage JSONL skeletons without writing files；如果 `--owner` 未登记在 `registry/owners.json`，只输出中文 warning，不代替后续 `knowledge-check` 的正式 owner gate。
- `knowledge-capture.sh`: dry-run candidate capture.
- `knowledge-promote.sh`: dry-run promotion plan.
- `knowledge-retire.sh`: dry-run retirement plan.

Writing requires explicit future implementation and must not be used by unattended automations.

## `knowledge-check.sh` 参数语义

`knowledge-check.sh` 是全仓一致性门禁。`--project` 和 `--domain` 目前只是兼容保留参数，不会缩小检查范围；传入时会在 `warnings` 中提示仍执行全仓检查。

`--explain <item-id>` 是只读人工诊断入口，用于解释单个 registry item 的基础字段、正文路径是否存在、核心索引引用计数、`by-status` bucket 和维护提示。它不修复文件、不生成索引、不执行 `validation_refs`，适合在 `knowledge-check` 报缺失或重复引用后定位人工修改点。

`--diagnostics` 是只读错误分组入口，用于把原始 errors 按 registry、source、migration、template、manual-entry、item、index、secret 和 explain 等类别生成中文摘要与人工修复提示。它不隐藏原始错误、不改变退出码、不自动修复，适合在全仓门禁失败后快速判断先改哪个文件。

示例：

下面的 `pcr02-project-docs` 是 owner-gated source-id 示例；维护其他 source 时替换为对应 `source_id`。

按场景复制：

```bash
# 新增一条知识
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline note awaiting rtk validation"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind debug-record --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/archive/debug/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind external-source-note --domain codex --owner <owner> --id <id> --path artifacts/manifests/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind owner-decision-worksheet --domain projects/pcr02 --owner <owner> --id <id> --path artifacts/worksheets/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind patent-disclosure --domain patents --owner <owner> --id <id> --path domains/patents/disclosures/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<id-or-keyword>" --json

# 新增一个 source
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --no-check-reason "classify-first pending source coverage"
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<source-id>" --source knowledge-hub --json

# 归档一条历史记录
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind project-archive --domain projects/<project> --owner <owner> --id <id> --path domains/projects/<project>/archive/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<archive-id-or-keyword>" --domain projects/<project> --kind project-archive --json

# 复核过期项
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics

# owner 签收一个 gate
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --evidence-readiness --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json

# 跑一次终态检查
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

`owner-decision-worksheet` 只输出人工签核草稿建议，不代表 owner decision 已签收，也不能关闭 owner gate。

新增 source 时，`registry/sources.json` 的 `owner` 必须是 `registry/owners.json` 中已有的 source registry 维护责任人。`knowledge-new.sh --source` 要求 `--check` 或 `--no-check-reason` 二选一。优先使用稳定只读 `--check "rtk ..."`；只有没有稳定检查入口时才使用 `--no-check-reason`，并在 source coverage 或相邻 manifest 写清 no-check reason。使用 `--check` 时，registry source object 和 source coverage JSONL row 草稿都应记录 `check`，不再补 JSON 形式的 `no_check_reason`。

查看 JSON 中的 `automatic_governance.status`、`owner_recovery`、`final_state_audit` 和 `gap_map`：`complete-except-owner-review` 表示自动治理已闭环但仍需人工 owner decision，只有 final gate 为 `needs-owner-review` 且唯一 gap 是 `owner-gates-open` 时才成立；`owner_recovery.owner_dispatch[]` 和 `owner_recovery.next_open` 可直接恢复人工分派队列；`final_state_audit` 分层显示 Level 1/2/3 终态摘要；`needs-fix` 表示还有非 owner blocker 需要先修复。`knowledge-status.sh --strict` 是 blocker dashboard，`knowledge-final-gate.sh --json` 才是 terminal gate。

`<owner-decisions.jsonl>` 是 owner 人工填写后的临时 JSONL 路径；工具只校验和生成 no-write landing plan，不代签、不关闭 gate。表单中的 `owner_route` 只说明抽象 decision owner role 的分派责任人、真实签收人待确认说明和升级路径；不能把 `routing_owner` 自动填成 `reviewed_by`。表单中的 `verification_cwd` 和 landing plan step 中的 `worksheet_verification_cwd` 是项目侧命令执行目录；相对命令必须在该目录下运行，而不是在 Knowledge Hub root 下运行。

搜索和恢复入口：

```bash
rtk git rev-parse --short HEAD
rtk git status --branch --short
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --json --limit 10
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "owner decision" --source knowledge-hub --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --domain projects/pcr02 --kind project-current --status reviewing --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "diag" --source-id pcr02-project-docs --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md ~/knowledge-hub/indexes/by-status.md
```

先用 git 命令固定 HEAD、分支和工作区状态，再运行 status/final gate 或结构化搜索，避免把旧 handoff、旧 manifest 或外部脏工作区当成当前事实。
结构化过滤只对能关联到 `registry/items.jsonl` 的本仓登记条目生效；使用 `--owner`、`--status`、`--kind`、`--domain` 或 `--source-id` 时，未登记普通文件会被排除，避免把外部原始文件误当治理条目。JSON 输出保留旧的 `query/count/results` 字段，并在命中 registry item 时附带 `item_id/title/kind/domain/status/owner/source_id/review_after/tags`。

| 场景 | 最小落盘文件 | 关键验证 |
|---|---|---|
| 新增知识 | 唯一正文、`registry/items.jsonl`、核心索引；已登记 source 才同步 `indexes/by-source.md`，decision 类条目同步 `indexes/by-decision.md`，未知 source 不伪造 source id；人工来源、中文摘要、语言/术语、review/evidence、AI provenance 字段必须清楚；2026-06-21 及之后 `generated_by_ai=true` 的 item 必须带 `ai_role`、`ai_model_or_tool` 和 `ai_generated_at`；涉及迁移/引用/归档时补 `registry/migrations.jsonl`，2026-06-21 及之后的 migration row 必须带 `notes_zh` | `knowledge-index-plan --section all`、`knowledge-check --diagnostics`、定向 `knowledge-search` |
| 新增 source | `registry/sources.json`、`indexes/by-source.md`、source coverage/source identity manifest | `knowledge-index-plan --section source`、`knowledge-check --diagnostics`、`knowledge-search "<source-id>" --source knowledge-hub --json` |
| 新增治理 manifest | `artifacts/manifests/*.md`、`artifacts/manifests/*.jsonl`、必要的 registry/index 登记 | `knowledge-index-plan --section manifest --json`、`knowledge-check --diagnostics`、`knowledge-regression --json` |
| 归档历史 | `domains/projects/<project>/archive/...`、`registry/items.jsonl`、`registry/migrations.jsonl`、相关索引 | `knowledge-check --diagnostics`、`knowledge-search "<keyword>" --domain projects/<project> --kind project-archive --json` |
| owner signoff | owner 人工填写的临时 JSONL；真正落地文件以 `--landing-plan` 输出为准 | `--validate-forms '<owner-decisions.jsonl>' --json`、`--landing-plan --json` |
| 终态检查 | 通常不新增文件；需要保存证据时落相邻 manifest | `rtk git diff --check`、`knowledge-final-gate.sh --json` |

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-status.sh
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id knowledge-hub-root --owner-gates pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section decision
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>'
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-audit
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
```

## Evidence

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。
