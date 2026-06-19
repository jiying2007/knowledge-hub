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
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --checklist
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --forms
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms <owner-decisions.jsonl>
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms <owner-decisions.jsonl> --landing-plan
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --owner <owner> --id <id> --path domains/projects/pcr02/current/runbooks/<file>.md
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --source <path> --kind <kind> --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-promote.sh --id <id> --target embedded/runbooks --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-retire.sh --id <id> --dry-run
```

## 人工新增最短路径

1. 运行 `knowledge-new.sh` 生成只读清单，不让脚本自动写文件。`--owner` 会写入草稿 registry owner；未传时默认 `leiwenjun`。当 `--domain projects/<project>` 且未传 `--project` 时，脚本会从 domain 推导 project；默认日期按 UTC 生成，`created_at` / `updated_at` / `checked_at` 为当天，`review_after` 默认约 3 个月后。
2. 从 `templates/` 复制合适模板到唯一正文位置。
3. 同步 `registry/items.jsonl`、`indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md` 和 `registry/migrations.jsonl`。
4. 运行 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all`，对照 registry 派生视图复核核心索引。
5. 如涉及 owner-gated 内容，先运行 `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id>`，确认 owner、必填证据和 active exposure；需要一次性分派全部 open gate 时加 `--summary`，需要 owner 签收上下文时加 `--checklist`，需要可复制 JSONL 表单时加 `--forms`。
   也可以先运行 `rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json`，读取 `owner_gates.summary_commands` 查看全部 open gate，再用 `owner_gates.next_open.next_open_command` 聚焦下一条 owner gate；或直接运行 `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --next-open --checklist --forms`。
6. 运行 `rtk bash ~/knowledge-hub/tools/knowledge-doctor.sh --id <id>`；如涉及 owner-gated source，加 `--owner-gates <source-id>`，先看 diagnostics、explain、search 和 owner gate 看板。
7. 运行 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json` 作为提交前全仓门禁。
8. 涉及门禁、索引或 owner gate 工具变更时，运行 `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json`，确认关键负向 fixture 仍会失败。
9. 终态验收运行 `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json`；它聚合 `knowledge-check`、`knowledge-regression` 和 `knowledge-status --strict`，当前 PCR02 owner gate 未签收时应返回 `needs-owner-review`。

人工可以直接按模板新增内容；脚本只是防漏清单，不是唯一入口。
