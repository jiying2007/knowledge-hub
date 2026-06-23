# Knowledge Hub

统一知识控制面，用于治理工程知识、项目事实、归档证据、专利材料、Codex 工作流和个人草稿。

## 角色

- `domains/`：人读知识正文。
- `registry/`：机器可校验的索引与治理记录。
- `indexes/`：按项目、主题、状态、owner 和决策生成的导航入口。
- `governance/`：维护方案、迁移策略、自动化边界和提升规则。
- `tools/`：只读检查、检索、候选登记、提升和退役入口。
- `templates/`：新增知识条目的模板。
- `artifacts/`：大文件、日志、SDK、制品的 manifest；不保存大文件正文。

## 中文长期资产规范

- 人读正文默认简体中文，命令、路径、协议字段、API 名称和代码标识保留原样。
- 结论、证据、推断、建议和风险分开写，长期条目必须可复核。
- 详细规范见 `governance/chinese-readability.md`、`governance/glossary.md`、`governance/evidence-rules.md`、`governance/naming-boundaries.md`、`governance/ai-generated-content-labeling.md`。
- 模板入口见 `templates/README.md`。

## 权威边界

1. 团队标准和跨项目 runbook 进入 `domains/embedded/`。
2. 当前项目事实进入 `domains/projects/<project>/current/`。
3. 项目历史证据进入 `domains/projects/<project>/archive/`。
4. 当前有效项目决策进入 `domains/projects/<project>/decisions/`。
5. 专利材料进入 `domains/patents/`。
6. Codex 会话、工作流和记忆治理进入 `domains/codex/`。
7. 个人草稿进入 `domains/personal/`，默认不进入团队 active index。

`~/.codex/memories` 只作为辅助召回层，不作为规则或工程事实权威来源。

## 常用命令

下面的 `pcr02-project-docs` 是 owner-gated source-id 示例；维护其他 source 时替换为对应 `source_id`。

## 低复杂度入口速查

| 层级 | 何时使用 | 入口命令 | 禁止事项 |
|---|---|---|---|
| 新增一条知识 | 新增、检索、复核普通知识条目 | `rtk bash ~/knowledge-hub/tools/knowledge-new.sh ...`；`rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<keyword>" --json`；`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 不伪造 source id、owner、hash、验证结果或 active 状态 |
| 人工复核 | 领取 AI 生成或外部资料待复核条目 | `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json --review-queue-limit 10`；`rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 20 --json`；同一过滤条件追加 `--queue-forms-jsonl` 可导出表单骨架 | 不写 registry，不自动填 `human_reviewed_by`，不把 queue 当 owner decision 或 active 提升依据 |
| owner 签收一个 gate | 处理 PCR02 owner-gated worksheet 和人工签收材料 | `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json` | 不代签 `reviewed_by`，不把 `routing_owner` 当真实 reviewer，不关闭 gate |
| 跑一次终态检查 | 判断是否只剩 owner 语义门禁或存在工具/索引/registry 漂移 | `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 不把 `needs-owner-review` 当工具失败，不跳过 regression 证明 terminal 状态 |
| 新增一个 source / 归档一条历史记录 / 高级写入计划 | 登记新 source、归档历史材料，或处理 copy-first、artifact-ref、promote、retire 等 reviewed manifest 流程 | `rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source ...`；`rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind project-archive ...`；`rtk bash ~/knowledge-hub/tools/knowledge-copy-first.sh ... --dry-run` | 不启用无人值守写入，不绕过 owner、rollback、hash 和验证命令 |

首屏只负责选入口：字段规范以 `templates/README.md` 的字段填写矩阵为准，索引同步以 `indexes/README.md` 为准，工具语义以 `tools/README.md` 为准。新增知识时先用 `knowledge-new.sh` 生成只读草稿，再按模板字段矩阵和索引最小同步补齐；不要在 README 复制出另一套字段权威。

人工新增草稿默认把 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` 写入 `validation_refs` 和 Evidence Index；离线待验证路径还必须保留 `manual_validation_pending: true` 与同一条 diagnostics follow-up，避免只留下普通 check 而缺少中文分组修复入口。

AI / external source 人工复核队列按批次处理：优先用 `knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 20 --json` 领取一页，继续翻页读取 `pagination.next_command`。需要交给人工填写时，再用同一组过滤条件加 `--queue-forms-jsonl` 导出 JSONL 表单骨架；`--queue-forms-jsonl` 是 JSONL-only 输出，不能和 `--json` 同用。该输出只包含只读上下文和空白人工字段，不写 registry、不自动回填、不提升 active、不关闭 owner gate。人工填写后可用同一组过滤条件加 `--validate-queue-forms <review-queue-forms.jsonl> --json` 做 report-only 校验；校验通过只说明结构、必填人工字段、枚举、日期和 queue id 覆盖有效，不代表 registry 已更新，也不代表 owner gate 已关闭。每条 row 的 `next_commands[]` 只用于打开只读 explain/诊断入口；人工复核结论仍必须由人填写 `human_reviewed_by`、`human_reviewed_at` 和 `review_basis`。

终态失败恢复决策树：

1. 先看 `knowledge-final-gate.sh --json` 的 `final_status`。
2. `final_status=needs-owner-review` 时，只在 `automatic_governance.status=complete-except-owner-review` 且 `gap_map[]` 只有 `owner-gates-open` 时停给真实 owner；按 `owner_recovery.next_open_queue[]` 领取下一批 open worksheet，或按 `owner_recovery.owner_dispatch[].suggested_owner_packet` 分 owner 导出、校验和生成 landing plan。
3. `final_status=needs-fix` 时，不处理 owner 表单，先看 `evidence_index[]` 中 status 非 `pass` / `owner-review` 的命令，再按 `blockers[]` 和 `gap_map[]` 修 registry、index、manifest、工具或环境缺口。
4. `final_status=ok` 时才说明终态完全通过；当前 PCR02 owner gate 未签收前不应期待该状态。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --owner-inbox --json
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --check "rtk ..."
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

更多 owner gate、doctor、inventory、capture、promote、retire 和 landing-audit 示例见 `tools/README.md`；根 README 只保留能选入口的最短路径。

## 新会话恢复

新线程或 AI 恢复时，优先用少量命令恢复控制面状态，不需要重读全部历史 manifest：

```bash
rtk git rev-parse --short HEAD
rtk git status --branch --short
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section manifest --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision|source coverage" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md ~/knowledge-hub/indexes/by-status.md
```

`rtk git rev-parse --short HEAD` 和 `rtk git status --branch --short` 先固定当前基线、分支和工作区状态，防止新线程把旧 handoff 当成当前事实。

恢复时按 5 个层面读取，不需要一次性重读全部 manifest：

- 先固定 HEAD、分支和工作区状态，避免把旧 handoff 当成当前事实。
- 看 `knowledge-status.sh --json` 恢复 owner queue、source coverage、source check、boundary health 和下一步命令。
- 看 `knowledge-final-gate.sh --json` 判断 `ok`、`needs-owner-review` 或 `needs-fix`；`needs-owner-review` 只有在唯一 gap 是 `owner-gates-open` 时才交给真实 owner。
- 从 `owner_gates.next_open_queue[]` 或 `owner_gates.owner_dispatch[]` 领取 owner gate；默认先用 `owner_inbox_json_command` 单屏查看问题、字段分组和候选证据，需要离线交给 owner 时使用 `handoff_packet_json_command` 输出 one-shot JSON 包，再导出、校验和规划。`next_open_queue[].owner_ready_package_status` 只来自 owner-gates 逐行强校验，不用 registry item presence 推断；不生成 owner decision、不关闭 gate。
- 用 `knowledge-index-plan.sh --section linking --json` 和 `knowledge-search.sh` 恢复跨会话、project、source、topic、decision 入口；字段级说明见 `tools/README.md`。

## 搜索知识

```bash
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --json --limit 10
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "owner decision" --source knowledge-hub --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --domain projects/pcr02 --kind project-current --status reviewing --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "diag" --source-id pcr02-project-docs --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md ~/knowledge-hub/indexes/by-status.md
```

全文搜索适合找正文和 manifest；结构化过滤适合按 registry item 的 `owner`、`status`、`kind`、`domain` 和 `source.source_id` 缩小结果。`--source` 表示物理扫描源，`--source-id` 表示 registry item 的来源 source。核心索引搜索适合恢复项目、source、topic、decision 和 status 治理入口。owner decision 的责任 owner 以 worksheet / `knowledge-owner-gates.sh --owner <owner>` 为准，registry item 的 `owner` 仍表示条目维护责任人；如果 worksheet owner 是抽象角色，先看 `registry/owner-routing.json` 的 `routing_owner`、`required_real_owner_zh` 和 `escalation_zh`。
使用 `--owner`、`--status`、`--kind`、`--domain` 或 `--source-id` 时，搜索结果必须能关联到 `registry/items.jsonl`；同关键词但未登记的 raw file 会被排除，不能作为 current fact 或 source-specific 证据。

## 人工维护 5 条最短路径

### 1. 新增一条知识

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner>
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner> --item-source-id <source-id> --item-source-path <source-relative-path>
```

常用专用模板入口：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind debug-record --domain projects/pcr02 --id <id> --path domains/projects/pcr02/archive/debug/<file>.md --owner <owner>
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind external-source-note --domain codex --id <id> --path artifacts/manifests/<file>.md --owner <owner>
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind owner-decision-worksheet --domain projects/pcr02 --id <id> --path artifacts/worksheets/<file>.md --owner <owner>
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind patent-disclosure --domain patents --id <id> --path domains/patents/disclosures/<file>.md --owner <owner>
```

`owner-decision-worksheet` 只是 owner gate 的人工签核草稿入口，不生成 owner decision、不代签、不关闭 gate。完整映射见 `templates/README.md`。

离线、现场或 AI 辅助起草时可追加：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner> --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline note awaiting rtk validation"
```

最小落盘按 5 组核对：

- 必须落盘：唯一正文 `domains/.../<file>.md` 或 `artifacts/manifests/...`、`registry/items.jsonl`、`indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md`。
- 按条件同步：涉及项目、source、主题或决策时，再同步对应索引。若已知来源已经登记在 `registry/sources.json`，优先用 `--item-source-id` 生成 `source.source_id` 和 `indexes/by-source.md` 草稿；未知来源保持 manual source reason 或 no-source reason，不伪造 source id。
- 决策边界：若 `kind=decision`，或内容承载真实 registry/migration/owner decision 入口，同步 `indexes/by-decision.md`；owner-ready package 不能写成已签收 owner decision。
- 字段权威：registry 草稿字段、AI provenance、`personal-local` 默认值、owner 归属和 migration 触发条件以 `templates/README.md` 的字段矩阵、`registry/schema.md` 的 allowed enum / invariants、以及 `tools/README.md` 的工具语义为准；根 README 只保留最短路径和同步位置，避免复制出另一套字段权威。`knowledge-new.sh` 的 warning 只提示人工补 owner/source，不替代签收或校验。

复制 `templates/` 中合适模板到唯一正文位置，优先中文写清背景、范围、结论、证据、风险和下一步。最后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<id-or-keyword>" --json
```

### 2. 新增一个 source

```bash
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --no-check-reason "classify-first pending source coverage"
```

新增 source 要求 `--check` 或 `--no-check-reason` 二选一。优先使用稳定只读 `rtk` check；提供 `--check` 时，registry source object 和 source coverage JSONL row 草稿都应记录 `check`，不再补 JSON 形式的 `no_check_reason`。

新增 source 时按 4 组核对：

- 最小落盘：`registry/sources.json`、`indexes/by-source.md`、最新或相邻 source coverage / source identity manifest（例如 `artifacts/manifests/<source-id>-source-coverage-YYYYMMDD.{md,jsonl}` 或全局 closeout manifest）；必要时同步 `indexes/by-project.md`、`indexes/by-topic.md`。
- 字段权威：source registry 字段、`--check` / `--no-check-reason` 二选一、`recommended_final_disposition` / `recommended_migration_strategy` 等 role-aware 推荐终态、以及 copyable JSON 保守默认值以 `registry/schema.md` 和 `tools/README.md` 为准；这里的 `owner` 是 source registry 维护责任人，不是 owner decision 或签收结论。推荐提示不替代 owner decision、不关闭 owner gate。
- 覆盖语义：同步 `indexes/by-source.md`，并记录 coverage/classification/source identity 或 no-check reason。`source coverage` 是 source 覆盖/分类证据；`source identity manifest` 是 source 身份与哈希等元信息记录。新增 source 只代表进入治理控制面，不代表复制正文、关闭 owner gate 或提升 active。

最后运行：

`knowledge-check --json` 会输出 `source_check_health`：它只做静态契约检查，统计 registered source、`rtk` check、`no_check_reason`、缺失项和不可达 source path；不会执行 registry 里的 check 命令。PCR02 Level 2 边界由 `boundary_health` 证明：它只读 Knowledge Hub 内部 manifest、registry 和 index，确认 7 组 boundary 证据链齐全；不会读取 PCR02 源项目正文、写 memory、关闭 owner gate 或启用自动化。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<source-id>" --source knowledge-hub --json
```

### 3. 归档一条历史记录

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind project-archive --domain projects/<project> --id <id> --path domains/projects/<project>/archive/<file>.md --owner <owner>
```

最小落盘文件：`domains/projects/<project>/archive/<file>.md`、`registry/items.jsonl`、`registry/migrations.jsonl`、相关 `indexes/*.md`。

复制 `templates/archive-note.md`，正文写清原始来源、归档边界、证据、当前状态和风险；registry item 默认 `status: archived` 或 `reviewing`，不把历史记录写成 active fact。按 `templates/migration-record.md` 追加迁移/归档记录，并同步项目、source、topic 或 decision 索引。最后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<archive-id-or-keyword>" --domain projects/<project> --kind project-archive --json
```

### 4. owner 签收一个 gate

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --owner-inbox --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --handoff-packet --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --evidence-readiness --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
```

owner gate 人工签收按 6 步走：

1. 准备临时 JSONL：建议放在 `artifacts/manifests/<source-id>-owner-decisions-YYYYMMDD.local.jsonl`。该类 `.local.jsonl` 已被 `.gitignore` 排除，只是 owner 草稿，不登记 registry/index，不作为 landing artifact。
2. 选择分派方式：多 owner 分派时先运行 `--summary` 查看 `owner_dispatch` 分派包，再用 `--owner <owner> --evidence-readiness --json` 查看只读证据准备度和候选值。
3. 导出表单骨架：用 `--owner <owner> --forms-jsonl` 或全量 `--forms-jsonl` 导出骨架；`read_only_prefill_candidates` 只帮助 owner 找 `source_sha256`、`source_size`、`review_after` 和 evidence ref 候选，不会写入正式 owner 字段，也不能替代签收。
4. 人工填写并校验：真实 owner 填写 decision 后先只读 `--validate-forms '<owner-decisions.jsonl>' --json`。`target_decision` 必须从表单里的 `target_candidates` 选择，不能手写到候选目标之外；同时 `owner_decision` 与 `target_decision` 必须成对兼容，不能把 `reference-only` / `no-migration` 和项目落地路径混用。校验可以合法只覆盖本批 JSONL 子集；批量处理时必须查看 `form_validation.coverage_status` 和 `missing_open_worksheet_ids`，单条处理优先带 `--worksheet-id`。
5. 生成落地计划和审计：校验通过后再跑 `--landing-plan --json` 和 `--landing-audit --json`。表单和 landing plan 会带出 `verification_cwd` / `worksheet_verification_cwd` 与 `verification_commands` / `worksheet_verification_commands`，相对命令必须在该 cwd 下执行，不是在 Knowledge Hub root 下执行。`landing_scope` 和 `remaining_open_after_this_batch` 只提示本批覆盖范围；是否全部闭环仍以 owner gate `open_count` 和 final gate 为准。
6. 复核 worksheet 状态：`--landing-audit` 会显式提醒 `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl` 的对应 worksheet 行也必须进入 resolved/owner-approved/closed 状态，否则 owner JSONL 即使有效，gate 仍会 open。AI 不代签、不关闭 gate、不把 owner-gated 内容设为 active。

### 5. 跑一次终态检查

```bash
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

如果结果是 `needs-owner-review`，确认唯一 blocker 是否为 `owner-gates-open`；这是人工语义 blocker，不等同于工具失败。
JSON 输出中的 `automatic_governance.status` 会直接标明 Codex 自动治理状态；当值为 `complete-except-owner-review` 且 `gap_map` 只有 `owner-gates-open` 时，说明非 owner 自动治理门禁已闭环，剩余动作只能由 owner 人工签收。复核证据时优先看 `maintenance_entry_audit`、`linking_audit`、`proof_artifacts` 和 `evidence_index[]`：前两者证明长期维护入口和跨索引恢复链路，`proof_artifacts` 证明终态 proof 主制品在 registry、migration 和核心索引中可恢复，后者逐条记录 `knowledge-check`、`knowledge-regression`、`rtk git diff --check` 和 `knowledge-status --strict` 等命令的退出码、状态和中文摘要；纯 owner-review 终态还会有 `owner-blocker-provenance` 行，指向 `automatic_governance.owner_blocker_source`。旧字段 `proof_artifacts_20260622` 仅为兼容保留，新消费方优先使用稳定字段 `proof_artifacts`。
`final_state_audit` 会同时给出 Level 1 PCR02 docs、Level 2 PCR02 candidate sources、Level 3 registered sources 的摘要状态，用于快速判断终态证据缺在哪一层。

离线或工具不可用时，不得声明终态 `ok` / `pass`。在维护记录中保留 `manual_validation_pending: true`，写清 `owner`、日期、当前 `cwd`、阻塞原因，并把 `required_followup` 写成完整命令：`rtk git diff --check` 和 `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json`。AI 或工具恢复后先补跑这些命令，再更新 registry、index 或 manifest 的验证证据。

## 常用辅助路径

### 复核过期和即将到期项

```bash
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-06-22 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-source-check.sh --scope pcr02-level2 --as-of 2026-06-22 --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

先看 `knowledge-status.sh --json` 的 `registry.stale_review_after_count` / `registry.review_after_command` / `registry.review_after_near_due_command`，以及 `sources.stale_review_after_count` / `sources.review_after_command` / `sources.source_check_report_command`。`knowledge-review-after.sh` 只生成过期和 30 天内到期的人工维护报告；`knowledge-source-check.sh` 只对 PCR02 Level 2 allowlist 做 report-only 路径存在性检查。过期项和 near-due 项都不等于工具失败，但必须由 owner 或 source registry 维护人复核 current validity、适用范围、证据是否仍有效和下一次 `review_after`；不确定时保持 `reviewing` 或 source 现有 final disposition，不得自动改 `active`、关闭 owner gate 或提升标准。

## 离线人工维护

AI、Codex、网络或工具不可用时，人工仍可按模板写正文并同步 registry/index。无法立即运行检查时，在正文或相邻维护记录中保留：

```text
manual_validation_pending: true
reason: tools unavailable / AI unavailable / offline field note
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics; rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
owner: <owner>
review_after: <date>
```

离线人工新增 registry item 时，默认保持未完成复核，不得直接设为 active 或 promotion。`promotion` 当前只允许 `none`；`promotion_decision` 用中文说明“不提升 / 候选 / 拒绝 / 待 owner review”等决策背景，不能拿它替代 owner decision。推荐最小字段如下：

```json
{
  "source": {
    "type": "manual",
    "from": "field-debug / meeting / code-review / lab-test / owner-decision / design-review"
  },
  "status": "reviewing",
  "review_status": "manual-entry-pending-review",
  "promotion": "none",
  "promotion_decision": "none",
  "validation_refs": ["manual_validation_pending: true"]
}
```

人工可以直接按模板新增内容；脚本只是防漏清单，不是唯一入口。AI 恢复后只能校验、补索引和提示风险，不得覆盖人工结论、自动改 active、关闭 owner gate 或写 memory。
