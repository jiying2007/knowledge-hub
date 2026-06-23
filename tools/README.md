# Knowledge Hub Tools

所有工具默认保守：优先只读、dry-run、report-only；不会自动删除、发布、提升 active、关闭 owner gate、写 memory 或修改源项目。

用户、文档和自动化默认只调用稳定 shell 入口：

```bash
rtk bash ~/knowledge-hub/tools/<tool>.sh ...
```

不要在长期文档中直接引用内部 Python 入口，也不要绕过 `rtk` 裸跑 shell 命令。

## 低复杂度入口速查

| 层级 | 使用场景 | 稳定入口 | 边界 |
|---|---|---|---|
| 日常路径 | 人工新增、检索、索引计划和全仓检查 | `knowledge-new.sh`、`knowledge-search.sh`、`knowledge-index-plan.sh`、`knowledge-check.sh --dry-run --json --diagnostics` | 只输出草稿或检查结果，不自动落盘、不伪造 source/owner/evidence |
| owner gate | 导出、校验和审计人工 owner decision JSONL | `knowledge-owner-gates.sh --owner-inbox`、`--forms-jsonl`、`--validate-forms`、`--landing-plan`、`--landing-audit` | 不生成 owner decision，不代签 `reviewed_by`，不关闭 gate |
| 终态检查 | 证明自动治理是否闭环，区分 `needs-owner-review` 和 `needs-fix` | `knowledge-final-gate.sh --json` | 必须包含 regression、diff check、strict status；不能只看单个 status pass |
| 高级写入计划 | copy-first、artifact-ref、capture、promote、retire 等需要 reviewed manifest 的流程 | 对应工具默认 dry-run；`--apply` 只允许人工在证据齐备后触发 | 自动化不得删除、发布、提升 active、关闭 owner gate、写 memory 或改源项目 |

- `knowledge-check.sh`: 只读一致性门禁。
  - 用途：检查 registry JSON/JSONL、owner/project/topic/source 登记、核心索引、migration record、template 必填字段、secret-pattern、owner-gated active 阻断、AI provenance 和中文 diagnostics。
  - 主要输出：JSON 中包含 `source_coverage_selection`、`source_coverage_health`、`source_check_health`、`boundary_health` 和 `--diagnostics` 中文错误分组，便于在 pass 状态下继续审计 latest closeout、source check/no-check 静态契约和 PCR02 Level 2 boundary 内部证据链。
  - 不会做什么：`source_check_health` 不执行 registry check 命令；`boundary_health` 不读取 PCR02 源项目正文；本工具不修复文件、不关闭 owner gate、不写 memory。
- `knowledge-check.sh`、`knowledge-status.sh` 和 `knowledge-final-gate.sh` 支持 `--as-of YYYY-MM-DD`；未传时可用环境变量 `KNOWLEDGE_TODAY=YYYY-MM-DD` 固定日期，再未设置时才使用系统日期。`--as-of` 用于复现 `review_after` 过期判断和终态证据，不生成 owner decision，不改变 registry。
- registry item 和 registered source 的 stale `review_after` 只是 warning/status surface，不是阻断错误；日期格式非法和 `updated_at < created_at` 仍是错误。
- `knowledge-review-after.sh`: 只读复核排期报告入口。它按 `--as-of` 和 `--window-days` 输出 stale / near-due registry item、source 统计和 owner gate open 计数；near-due 只是人工提醒，不作为 blocking gate，不自动修改 `review_after`，不关闭 owner gate。
- `knowledge-source-check.sh`: 只读 source availability 报告入口。首版只支持 `--scope pcr02-level2`，只执行 allowlist 中 `rtk bash -lc 'test -d ...'` / `test -f ...` 的路径存在性检查；它不读取 PCR02 source 正文，不运行项目脚本，不改变 `knowledge-check` 的 `source_check_health.mode=static-registry-only` 和 `executed=false` 语义。
- `knowledge-search.sh`: 只读检索入口。它支持全文检索，也支持 registry-backed 过滤：`--owner`、`--status`、`--kind`、`--domain`、`--source-id`；`--source` 仍表示物理扫描源，`--source-id` 表示 registry item 的 `source.source_id`。
- 结构化过滤只返回已登记 registry item；未登记 raw file 即使命中关键词，也不能在 `--source-id` / `--status` 等过滤模式下混入结果。
- `knowledge-status.sh`: 只读控制面 dashboard。
  - 用途：汇总 `knowledge-check`、registry/source/migration、owner gate、`owner_gates.owner_dispatch[]`、下一条 open gate、`owner_gates.next_open_queue[]`、`final_gate_command` 和 `strict_blockers`。
  - 主要输出：`owner_dispatch[].owner_inbox_json_command` 是按 owner 恢复的默认单屏入口；`owner_dispatch[].suggested_owner_packet` 先排列 owner-inbox，再排列 summary、evidence-readiness、forms-jsonl、validate、landing-plan 和 landing-audit；`next_open_queue[]` 按 `review_after, worksheet_id` 给出 open gate 领取队列；`sources.latest_coverage_selection` 记录 latest source coverage closeout 选择策略；`sources.source_recovery_rows[]` 合成 source 当前状态恢复行。
  - 不会做什么：不生成或应用 owner decision；`--strict` 只作为 blocker dashboard；terminal gate 仍以 `knowledge-final-gate.sh --json` 为准。`strict_blockers[].commands` 可直接执行，`strict_blockers[].command_templates` 需要替换 `<owner-decisions.jsonl>`。
- `knowledge-final-gate.sh`: 仓库只读终态门禁。
  - 用途：聚合 `knowledge-check --diagnostics`、`knowledge-regression --json`、`rtk git diff --check` 和 `knowledge-status --strict --json`，防止 terminal validation 漏掉回归漂移、空 JSON、whitespace 或 conflict marker。
  - 主要输出：JSON 包含 `today`、`as_of_source`、`automatic_governance`、`owner_recovery`、`final_state_audit`、`maintenance_entry_audit`、`linking_audit`、`source_check_runtime`、`highest_priority_rules_audit`、`evidence_index` 和 `gap_map`；`owner_recovery.next_open_queue[]` 会透传 status dashboard 的下一批 open worksheet；`maintenance_entry_audit` 只证明第七节 8 类长期维护入口存在且边界清楚；`linking_audit` 只证明 registry/index/search 恢复链路覆盖跨会话、项目、source、topic 和 decision；`source_check_runtime` 当前执行一次 PCR02 Level 2 report-only 路径存在性检查；`highest_priority_rules_audit` 用 10 条高优先级规则说明哪些规则已由运行证据覆盖、哪些只能过程审计；`evidence_index` 逐条记录命令证据；纯 owner-review 终态还会包含 `owner-blocker-provenance`。
  - 不会做什么：所有 gate 达到 terminal-ok 前仍会返回非零；回归子命令只在 `/tmp` 创建并清理临时 fixture，不修改 Knowledge Hub、registry、index 或源项目 docs。
- `knowledge-doctor.sh`: 只读维护辅助入口；运行 `knowledge-check --diagnostics`，可选输出 `--explain <item-id>`、搜索结果和 `--owner-gates <source-id>` 看板，不写文件。
- `knowledge-index-plan.sh`: 只读核心索引规划入口；输出由 registry 派生的 `by-owner`、`by-review-date`、`by-status`、`by-project`、`by-source`、`by-topic`、`by-decision`、`manifest` 和 `linking` 恢复视图，不写文件。JSON 输出包含 `source_coverage_selection`，用于追溯 `by_source[*].coverage` 来自哪个 latest closeout manifest；如 latest source coverage 里同一 `source_id` 重复，`duplicate_source_ids` 和 warnings 会显式暴露，并保留第一行作为恢复视图。`--section manifest` 用于恢复 manifest 最新项、Markdown/JSONL 配对、行数、证据计数和 unpaired 分类；latest 只按文件名 `YYYYMMDD` 排序，row 内日期只作为 `row_date` 辅助字段。manifest 文本和 JSON 输出都会显示 `profile_health`、`summary_source` 和 `evidence_source`：这些字段只说明恢复质量和派生来源，不回填历史 manifest 正文，不新增硬门禁。历史 unpaired 会标记为 `expected` 或 `needs_review`，这是 report-only 恢复视图，不会自动作为硬失败。`--section linking` 汇总 `by-project`、`by-source`、`by-topic`、`by-decision` 和 Markdown index 锚点，证明跨会话/项目/source/topic/decision 恢复链路存在；它不读取 PCR02 源项目正文，不关闭 owner gate。
- `knowledge-owner-gates.sh`: 只读 owner gate 看板。它输出 unresolved worksheet、必填 owner 字段、active exposure、owner route 和 source identity；`--summary` 会给出 owner 分布、`owner_dispatch[]` 和 `suggested_owner_packet`，后者把 summary、evidence-readiness、forms-jsonl、validate、landing-plan、landing-audit 排成 owner handoff 顺序。`--forms-jsonl` 只打印骨架，`--validate-forms <jsonl>` 只校验人工回填，`--landing-plan` 和 `--landing-audit` 只输出 no-write 人工落地计划与审计。`form_validation.errors[]` 保留兼容的人类可读错误，`form_validation.diagnostics[]` 提供逐字段 `code/field/actual/expected/action_zh`，方便 owner 或 UI 定位问题；`owner_decision` 与 `target_decision` 会做保守成对兼容检查，避免 `reference-only` / `no-migration` 和项目落地路径混用。两者都不生成 owner decision、不代签、不关闭 gate。`read_only_prefill_candidates` 只给候选值；正式 owner 字段仍需真实 owner 填写。`owner_route` 只来自 `registry/owner-routing.json`，不生成 owner decision，也不能替代 `reviewed_by`。
- `knowledge-owner-gates.sh --owner-inbox`: 单屏 owner 待办入口。它按 worksheet 汇总 owner 中文问题、路由、字段分组、只读候选、owner-ready package、verification commands、forms-jsonl 和 validate/landing 模板，适合从 `owner_recovery.next_open_queue[]` 或 `owner_gates.owner_dispatch[].owner_inbox_json_command` 之后给真实 owner 使用；它不生成 owner decision，不写本地 JSONL，不关闭 gate。
- `knowledge-regression.sh`: 只读回归 fixture 入口；把仓库复制到 `/tmp`，只修改临时副本，用于验证 status bucket mismatch、partial owner resolution 等关键负向门禁。默认每个场景后清理临时 fixture，内部异常会记录结构化失败细节；`--json` 模式输出 JSON，支持 `--as-of YYYY-MM-DD` / `KNOWLEDGE_TODAY` 固定日期敏感命令，并使用 `KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES` 做低空间预检。
- `knowledge-inventory.sh`: 只读 source inventory；列出已登记 source 的 owner、路径、状态、复核日期和维护字段。
- `knowledge-copy-first-plan.sh`: 为已登记 source 生成经审查的 JSONL copy-first manifest；只在 `artifacts/manifests/` 下写 manifest。
- `knowledge-copy-first.sh`: 按 JSONL manifest 执行 copy-first 迁移；默认 dry-run，需显式确认后才会复制已批准正文。
- `knowledge-artifact-ref-plan.sh`: 为非文本 source 文件生成 artifact 引用 manifest，记录 source URI、size 和 sha256；不复制二进制内容。
- `knowledge-new.sh`: 只读人工新增向导。它只打印模板、registry 草稿、索引提示、条件 migration 草稿、验证步骤和可复制骨架，不写文件。支持 `--owner <owner>`、`--item-source-id <source-id>`、`--item-source-path <source-path>`、`--manual-source-reason <reason>`、`--manual-validation-pending --manual-validation-reason <reason>`、`--generated-by-ai --ai-role <role>`；默认 owner 为 `leiwenjun`，可从 `--domain projects/<project>` 推导 project，并支持 `KNOWLEDGE_TODAY=YYYY-MM-DD` 固定草稿日期。草稿默认包含 `summary_zh`、语言/术语、review/evidence 和 AI provenance 字段；默认 `validation_refs` 与 Evidence Index 使用 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`。普通条目指定 `--item-source-id` 时会先校验该 source 已登记，再输出 `source.source_id`、可选 `source.source_path`、`indexes/by-source.md` 草稿和带 `--source-id` 的定向检索命令；未知 source 不伪造 source id。模板别名会映射为合法 registry kind。`--source` 只打印 source registry、by-source 和 source coverage JSONL 骨架；未知 owner 只输出中文 warning，不替代正式 owner gate；coverage row 的 `status` 跟随 `--source-status` 输出为 `<status>-pending-classification`。
- `knowledge-capture.sh`: dry-run 候选捕获入口；只输出待审查候选，不写 active 知识。
- `knowledge-promote.sh`: dry-run 提升计划入口；只输出提升前检查和人工步骤，不自动提升。
- `knowledge-retire.sh`: dry-run 退役计划入口；只输出退役影响和人工步骤，不自动删除或移动正文。

写入必须走显式 reviewed manifest、dry-run、owner、rollback 和验证证据；无人值守自动化不得使用写入入口。

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
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md --item-source-id pcr02-project-docs --item-source-path runbooks/<file>.md
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
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of 2026-06-22 --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics

# owner 签收一个 gate
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json
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

终态 JSON 先看 4 组字段：

- `automatic_governance.status` 和 `gap_map[]`：判断自动治理是否 `complete-except-owner-review`，以及唯一缺口是否为 `owner-gates-open`。
- `owner_recovery`：恢复下一批 open worksheet、owner 分派、owner handoff packet 和单条 gate 入口；只服务真实 owner 人工签收。
- `maintenance_entry_audit`、`linking_audit`、`final_state_audit`、`source_check_runtime` 和 `highest_priority_rules_audit`：证明长期维护入口、跨索引恢复、分层终态、report-only source availability 和高优先级规则证据边界。
- `evidence_index[]`：记录本次 terminal gate 采信的每条命令证据、退出码、状态和中文摘要。

`knowledge-status.sh --strict` 是 blocker dashboard，`knowledge-final-gate.sh --json` 才是 terminal gate；`needs-fix` 表示还有非 owner blocker 需要先修复。

如果离线或工具不可用，不能把终态写成 `ok` / `pass`。在相邻维护记录中写 `manual_validation_pending: true`，并记录 owner、日期、当前 `cwd`、阻塞原因和 `required_followup: rtk git diff --check; rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json`；恢复后先补跑命令再更新证据。

失败恢复决策树以根 README 为准，本文件只补工具字段和边界。简要顺序：

1. `needs-fix`: 先看 `evidence_index[]`，定位哪条命令不是 `pass` 或 `owner-review`；再看对应 `blockers[]` / `gap_map[]` 的 `fix_action`。
2. `needs-owner-review`: 只在 `gap_map[]` 唯一项为 `owner-gates-open` 时进入 owner 人工签收路径；从 `owner_recovery.owner_dispatch[]` 选择 owner，先运行 `owner_inbox_json_command`，再按 handoff packet 运行 summary、evidence-readiness、forms-jsonl、validate、landing-plan、landing-audit。
3. `ok`: 终态完全通过；仍需用 `evidence_index[]` 留存命令证据，不用 owner handoff。

`<owner-decisions.jsonl>` 是 owner 人工填写后的临时 JSONL 路径；工具只校验和生成 no-write landing plan，不代签、不关闭 gate。表单中的 `owner_route` 只说明抽象 decision owner role 的分派责任人、真实签收人待确认说明和升级路径；不能把 `routing_owner` 自动填成 `reviewed_by`。`target_decision` 不仅要在 `target_candidates` 内，还要和 `owner_decision` 成对兼容。表单中的 `verification_cwd` 和 landing plan step 中的 `worksheet_verification_cwd` 是项目侧命令执行目录；相对命令必须在该目录下运行，而不是在 Knowledge Hub root 下运行。

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
| owner 人工签收 | owner 人工填写的临时 JSONL；真正落地文件以 `--landing-plan` 输出为准 | `--validate-forms '<owner-decisions.jsonl>' --json`、`--landing-plan --json` |
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
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json
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

## 命令证据

命令证据应记录执行目录、完整 `rtk ...` 命令、日期、退出码、覆盖范围和中文结果摘要。写入计划工具默认先 dry-run；`--apply` 只能由人工在 reviewed manifest、owner、rollback policy、hash 校验和验证命令齐备后触发。

## 离线人工维护

工具不可用时，人工仍可按 `README.md`、`templates/`、`registry/schema.md` 和 `indexes/README.md` 写唯一正文、registry 草稿和索引 TODO。恢复后先运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
```

离线记录必须保留 `manual_validation_pending: true`、owner、review_after 和 required_followup；AI 恢复后只做校验、补索引和提示风险，不自动改 active、不关闭 owner gate、不写 memory。
