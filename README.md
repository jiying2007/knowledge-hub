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
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id>
rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id> --owner-gates pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section status
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --summary
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
rtk rg -n "PCR02|pcr02-project-docs|owner decision|source coverage" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md
```

`knowledge-status.sh --json` 给出当前 owner gate、source coverage 和下一步命令；`knowledge-final-gate.sh --json` 判断是否只剩 owner 语义门禁；四个索引用于恢复 project、source、topic 和 decision 入口。

## 搜索知识

```bash
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN" --json --limit 10
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "owner decision" --source knowledge-hub --json
rtk rg -n "PCR02|pcr02-project-docs|owner decision" ~/knowledge-hub/indexes/by-project.md ~/knowledge-hub/indexes/by-source.md ~/knowledge-hub/indexes/by-topic.md ~/knowledge-hub/indexes/by-decision.md
```

全文搜索适合找正文和 manifest；核心索引搜索适合恢复项目、source、topic 和 decision 的治理入口。

## 人工维护 5 条最短路径

### 1. 新增一条知识

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner>
```

复制 `templates/` 中合适模板到唯一正文位置，优先中文写清背景、范围、结论、证据、风险和下一步。同步 `registry/items.jsonl`、`indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md`；如涉及项目、source、主题或决策，再同步对应索引。涉及迁移、引用或归档时补 `registry/migrations.jsonl`。最后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

### 2. 新增一个 source

```bash
rtk bash ~/knowledge-hub/tools/knowledge-inventory.sh --markdown
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --source --source-id <source-id> --source-path <path> --role <role> --authority <authority> --write-policy <policy> --no-check-reason "classify-first pending source coverage"
```

人工补 `registry/sources.json` 的 `id`、`path`、`role`、`authority`、`status`、`write_policy`、`migration_strategy`、`owner`、`review_after` 和 `final_disposition`；如果 `check` 为空，必须填写 `no_check_reason`。这里的 `owner` 是 source registry 维护责任人，不是 owner decision 或签收结论。同步 `indexes/by-source.md`，并记录 coverage/classification/source identity 或 no-check reason。新增 source 只代表进入治理控制面，不代表复制正文、关闭 owner gate 或提升 active。最后运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

### 3. 归档一条历史记录

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind project-archive --domain projects/<project> --id <id> --path domains/projects/<project>/archive/<file>.md --owner <owner>
```

复制 `templates/archive-note.md`，正文写清原始来源、归档边界、证据、当前状态和风险；registry item 默认 `status: archived` 或 `reviewing`，不把历史记录写成 active fact。按 `templates/migration-record.md` 追加迁移/归档记录，并同步项目、source、topic 或 decision 索引。

### 4. owner 签收一个 gate

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --next-open --checklist --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --forms-jsonl
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --json
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

建议把 owner 人工填写的临时 JSONL 放在 `artifacts/manifests/<source-id>-owner-decisions-YYYYMMDD.local.jsonl`，先只读校验，再用 landing plan 人工落地。只有真实 owner 填写 decision；AI 不代签、不关闭 gate、不把 owner-gated 内容设为 active。

### 5. 跑一次终态检查

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

如果结果是 `needs-owner-review`，确认唯一 blocker 是否为 `owner-gates-open`；这是人工语义 blocker，不等同于工具失败。
JSON 输出中的 `automatic_governance.status` 会直接标明 Codex 自动治理状态；当值为 `complete-except-owner-review` 且 `gap_map` 只有 `owner-gates-open` 时，说明非 owner 自动治理门禁已闭环，剩余动作只能由 owner 人工签收。
`final_state_audit` 会同时给出 Level 1 PCR02 docs、Level 2 PCR02 candidate sources、Level 3 registered sources 的摘要状态，用于快速判断终态证据缺在哪一层。

## 离线人工维护

AI、Codex、网络或工具不可用时，人工仍可按模板写正文并同步 registry/index。无法立即运行检查时，在正文或相邻维护记录中保留：

```text
manual_validation_pending: true
reason: tools unavailable / AI unavailable / offline field note
required_followup: run knowledge-check and update registry/index
owner: <owner>
review_after: <date>
```

人工可以直接按模板新增内容；脚本只是防漏清单，不是唯一入口。AI 恢复后只能校验、补索引和提示风险，不得覆盖人工结论、自动改 active、关闭 owner gate 或写 memory。
