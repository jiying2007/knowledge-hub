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

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-status.sh
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id>
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id> --owner-gates pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --evidence-readiness --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>'
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --source <path> --kind <kind> --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-promote.sh --id <id> --target embedded/runbooks --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-retire.sh --id <id> --dry-run
```

## 新会话恢复

新线程或 AI 恢复时，优先用少量命令恢复控制面状态，不需要重读全部历史 manifest：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section manifest --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision|source coverage" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md ~/knowledge-hub/indexes/by-status.md
```

`knowledge-status.sh --json` 给出当前 owner gate、`owner_gates.owner_dispatch[]`、source coverage、source check health、boundary health、下一步命令和 `final_gate_command`；`knowledge-status.sh --strict` 是 blocker dashboard，不是终态完成证据。`knowledge-final-gate.sh --json` 是 terminal gate，会聚合 `knowledge-check`、`knowledge-regression`、`rtk git diff --check` 和 strict status，并判断是否只剩 owner 语义门禁；它的 `owner_recovery` 会透传 open owner 数量、owner-ready 覆盖、`owner_dispatch[]` 和下一条 open gate，便于新线程直接恢复人工分派。`source_check_health` 只静态检查 `registry/sources.json` 的 `rtk` check / `no_check_reason` 契约，不执行外部命令；`boundary_health` 只检查 Knowledge Hub 内部 PCR02 Level 2 boundary manifest、registry 和 index 证据，不读取源项目正文。`knowledge-index-plan.sh --section manifest --json` 用于恢复最新 manifest、Markdown/JSONL 配对、行数和证据计数，并把历史 unpaired manifest 分类为 `expected` 或 `needs_review`；这是 report-only 恢复视图，不会因为历史例外自动失败。`owner_dispatch[].owner_route` 来自 `registry/owner-routing.json`，只说明抽象 decision owner role 的分派和升级路径，不生成 owner decision，不替代 `reviewed_by`。`by-project`、`by-source`、`by-topic`、`by-decision` 用于恢复项目/source/topic/decision 入口，`by-status` 用于恢复 owner-ready、owner-dispatch、terminal gate 和 reviewing bucket 的收口线索。

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

## 人工维护 5 条最短路径

### 1. 新增一条知识

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner>
```

离线、现场或 AI 辅助起草时可追加：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner> --manual-source-reason field-debug --manual-validation-pending --manual-validation-reason "offline note awaiting rtk validation"
```

最小落盘文件：唯一正文 `domains/.../<file>.md` 或 `artifacts/manifests/...`、`registry/items.jsonl`、`indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md`；如涉及项目、source、主题或决策，再同步对应索引。若 `source.from` 或后续人工 `source_id` 指向 `registry/sources.json` 中的已登记 source，同步 `indexes/by-source.md`；未知来源保持 manual source reason 或 no-source reason，不伪造 source id。若 `kind=decision`，或内容承载真实 registry/migration/owner decision 入口，同步 `indexes/by-decision.md`；owner-ready package 不能写成已签收 owner decision。registry 草稿必须补清 `summary_zh`、`primary_language`、`source_language`、`translation_status`、`terminology_status`、`review_status`、`evidence_strength`、`evidence_refs` 和 AI provenance 字段；2026-06-21 及之后 `generated_by_ai=true` 的 registry item 必须填写 `ai_role`、`ai_model_or_tool` 和 `ai_generated_at`。涉及迁移、引用或归档时补 `registry/migrations.jsonl`，2026-06-21 及之后的 migration row 必须包含 `notes_zh`，普通新知识不强制 migration。

复制 `templates/` 中合适模板到唯一正文位置，优先中文写清背景、范围、结论、证据、风险和下一步。最后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<id-or-keyword>" --json
```

### 2. 新增一个 source

```bash
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --check "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --no-check-reason "classify-first pending source coverage"
```

最小落盘文件：`registry/sources.json`、`indexes/by-source.md`、最新或相邻 source coverage / source identity manifest（例如 `artifacts/manifests/<source-id>-source-coverage-YYYYMMDD.{md,jsonl}` 或全局 closeout manifest），必要时同步 `indexes/by-project.md`、`indexes/by-topic.md`。

人工补 `registry/sources.json` 的 `id`、`path`、`role`、`authority`、`status`、`write_policy`、`migration_strategy`、`owner`、`review_after` 和 `final_disposition`；这里的 `owner` 是 source registry 维护责任人，必须已登记在 `registry/owners.json`，不是 owner decision 或签收结论。`knowledge-new.sh --source` 要求 `--check` 或 `--no-check-reason` 二选一。优先使用稳定只读 `--check "rtk ..."` 记录可复核检查命令；只有暂时没有稳定检查入口时才使用 `--no-check-reason`，且如果 `check` 为空，必须填写 `no_check_reason`。使用 `--check` 时，registry source object 和 source coverage JSONL row 草稿都应记录 `check`，不再补 JSON 形式的 `no_check_reason`。同步 `indexes/by-source.md`，并记录 coverage/classification/source identity 或 no-check reason。新增 source 只代表进入治理控制面，不代表复制正文、关闭 owner gate 或提升 active。最后运行：

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
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --owner <owner> --evidence-readiness --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --landing-audit --json
```

建议把 owner 人工填写的临时 JSONL 放在 `artifacts/manifests/<source-id>-owner-decisions-YYYYMMDD.local.jsonl`，先只读校验，再用 landing plan 人工落地，并用 landing audit 复核 worksheet、registry、migration 和 index 人工落点。多 owner 分派时先运行 `--summary` 查看 `owner_dispatch` 分派包，再用 `--owner <owner> --evidence-readiness --json` 查看只读证据准备度和候选值，用 `--owner <owner> --forms-jsonl` 导出对应责任人的骨架。`read_only_prefill_candidates` 只帮助 owner 找 `source_sha256`、`source_size`、`review_after` 和 evidence ref 候选，不会写入正式 owner 字段，也不能替代签收。`target_decision` 必须从表单里的 `target_candidates` 选择，不能手写到候选目标之外；表单和 landing plan 会带出 `verification_cwd` / `worksheet_verification_cwd` 与 `verification_commands` / `worksheet_verification_commands`，相对命令必须在该 cwd 下执行，不是在 Knowledge Hub root 下执行。`--landing-audit` 会显式提醒 `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl` 的对应 worksheet 行也必须进入 resolved/owner-approved/closed 状态，否则 owner JSONL 即使有效，gate 仍会 open。人工落地后按这些命令或等价证据复核。只有真实 owner 填写 decision；AI 不代签、不关闭 gate、不把 owner-gated 内容设为 active。

### 5. 跑一次终态检查

```bash
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

如果结果是 `needs-owner-review`，确认唯一 blocker 是否为 `owner-gates-open`；这是人工语义 blocker，不等同于工具失败。
JSON 输出中的 `automatic_governance.status` 会直接标明 Codex 自动治理状态；当值为 `complete-except-owner-review` 且 `gap_map` 只有 `owner-gates-open` 时，说明非 owner 自动治理门禁已闭环，剩余动作只能由 owner 人工签收。
`final_state_audit` 会同时给出 Level 1 PCR02 docs、Level 2 PCR02 candidate sources、Level 3 registered sources 的摘要状态，用于快速判断终态证据缺在哪一层。

## 常用辅助路径

### 复核过期项

```bash
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-date
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

先看 `knowledge-status.sh --json` 的 `registry.stale_review_after_count` 和 `registry.review_after_command`。过期项不等于工具失败，但必须由 owner 复核 current validity、适用范围、证据是否仍有效和下一次 `review_after`；不确定时保持 `reviewing`，不得自动改 `active`、关闭 owner gate 或提升标准。

## 离线人工维护

AI、Codex、网络或工具不可用时，人工仍可按模板写正文并同步 registry/index。无法立即运行检查时，在正文或相邻维护记录中保留：

```text
manual_validation_pending: true
reason: tools unavailable / AI unavailable / offline field note
required_followup: run knowledge-check and update registry/index
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
