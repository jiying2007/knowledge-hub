# Templates

新增 Knowledge Hub 条目时优先使用本目录模板。模板的人读部分默认简体中文；命令、路径、协议字段、API 名称和代码标识保留原样。

## 通用要求

- frontmatter 必须对齐 `registry/schema.md` 的 required fields，并优先使用 `summary_zh`、`primary_language`、`source_language`、`translation_status`、`terminology_status`、`review_status`、`evidence_strength`、`evidence_refs`、`promotion_decision` 和 AI provenance 字段；新模板不再新增 `summary` / `language` 双轨字段。
- 正文至少写清摘要、适用范围、权威来源、当前结论、验证与证据、风险与限制、Review。
- 结论、证据、推断、建议分开写。
- 验证与证据优先使用 `governance/evidence-rules.md` 中的 Evidence Index 表格，记录完整 `rtk ...` 命令、退出码、中文摘要和证据路径。
- 外部资料必须提供中文摘要和 source metadata。
- AI 生成、摘要、翻译、分类或重写内容必须标注复核状态。
- 大文件、raw log、SDK、release binary 只登记 artifact 引用，不写入正文。

## 字段填写矩阵

| 场景 | 必须填 | 条件填 | 不得填 | 不能伪造 | 验证入口 |
|---|---|---|---|---|---|
| 通用新增条目 | `id`、`title`、`kind`、`domain`、`path`、`scope`、`visibility`、`status`、`owner`、`source`、`review_after`、`created_at`、`updated_at`、`promotion`、`tags`、`validation_refs`、`summary_zh`、语言/术语/evidence 字段；默认验证命令使用 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | `artifact_refs`、`related`、`promotion_decision`、`manual_validation_pending` 正文块 | 未验证前不得填 `status=active`，不得把 `promotion` 改成非 `none` | 不得伪造 source、owner、验证命令、hash、review 结果 | `rtk bash ~/knowledge-hub/tools/knowledge-new.sh ...`；`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` |
| AI 参与起草、摘要、翻译、分类或重写 | 通用必填字段，且 `generated_by_ai=true`、`ai_role`、`ai_model_or_tool`、`ai_generated_at` | `human_reviewed_by`、`human_reviewed_at`、`review_basis` 只在真实人工复核后填写 | 未人工复核前不得把 `review_status` 写成 owner-reviewed 或 active-ready | 不得把 AI 输出写成人工结论，不得伪造 reviewer | `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` |
| source 相关条目 | `source.source_id` 必须已登记，或明确 `manual-source-reason` / no-source reason；source registry 必须有 owner、review_after、check 或 no-check reason | `source.source_path`、`source_sha256`、`source_size`、coverage / identity manifest | 未登记 source 前不得同步 `indexes/by-source.md` 为真实 source id | 不得伪造 source id、hash、size、check 结果；source owner 不是 owner decision 签收人 | `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section source`；`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` |
| owner decision worksheet | `worksheet_id`、`source_id`、`source_path`、`owner_question`、`target_candidates`、`required_owner_fields`、`must_not`、`verification_cwd` | `observed_source_identity`、候选 target、evidence readiness 只作为只读提示 | worksheet 内不得填写真实 `reviewed_by` 作为签收结论，不得关闭 owner gate | 不得把 `routing_owner`、AI、脚本或占位符伪造成 `reviewed_by` | `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --forms-jsonl`；`rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id <source-id> --validate-forms '<owner-decisions.jsonl>' --json` |
| migration / archive / artifact-ref | migration row 必须写 `migration_id`、`source_id`、`target`、`status`、`checked_at`、`notes_zh`；archive/artifact-ref 必须写边界、hash/size 或 no-copy 原因 | `artifact_refs`、`source_identity`、`rollback_policy` | 不得把 raw log、SDK、release binary、secret-like config 写入正文 | 不得把归档、session、handoff、memory candidates 伪造成 active fact | `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all`；`rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<id>" --json` |

字段矩阵是人工落盘前的速查表；具体 allowed enum 和硬门禁以 `registry/schema.md`、`knowledge-check.sh`、`knowledge-owner-gates.sh` 的当前输出为准。

## 模板清单

| 输入 kind | registry kind | 推荐模板 | 用途 |
|---|---|---|---|
| `item` 或未知 kind | 需人工从 schema 选择 | `item.md` | 通用知识条目 |
| `runbook` | `runbook` | `runbook.md` | 操作手册 |
| `decision` | `decision` | `decision.md` | 决策记录 |
| `validation` / `validation-report` | `validation` | `validation-report.md` | 验证报告 |
| `owner-decision-worksheet` / `owner-worksheet` | `owner-decision-worksheet` | `owner-decision-worksheet.md` | owner 签核草稿入口 |
| `debug-record` | `debug-record` | `debug-record.md` | 排障记录 |
| `external-source-note` / `external-source` | `external-source-note` | `external-source-note.md` | 外部资料吸收记录 |
| `project-archive` / `archive-note` | `project-archive` | `archive-note.md` | 归档说明 |
| `migration-record` / `migration` | `migration-record` | `migration-record.md` | 迁移记录 |
| `artifact-ref` | `artifact-ref` | `artifact-ref.md` | 制品引用 |
| `patent-disclosure` | `patent-disclosure` | `patent-disclosure.md` | 专利披露 |
| `patent` | `patent` | `patent-disclosure.md` | 专利材料通用条目 |

`knowledge-new.sh` 是只读人工新增向导，不自动创建文件。模板别名会映射成合法 `registry kind`；人工直接写 registry 时必须使用 `registry/schema.md` 允许的 kind，不能把未知模板名当自由枚举。模板仍可人工复制使用；复制后必须更新 `id`、`path`、`owner`、`source`、`summary_zh`、`review_status`、`review_after`、`promotion`、`promotion_decision`、`tags` 和 `validation_refs`，确认 `primary_language`、`source_language`、`translation_status`、`terminology_status`、`evidence_strength`、`evidence_refs` 与正文 Evidence Index 一致，并同步 registry、`indexes/by-owner.md`、`indexes/by-review-date.md` 和 `indexes/by-status.md`；如涉及迁移、引用或归档，再补 `registry/migrations.jsonl`；项目域条目还要同步 `indexes/by-project.md` 的项目导航入口；核心索引不得留下 duplicate item reference。

`promotion` 是 registry 当前允许的枚举值，目前只能为 `none`；`promotion_decision` 是人读决策说明，用于写清“不提升、候选、拒绝、待 owner review”等背景。`promotion_decision` 不能替代 owner decision，也不能绕过 active / team-level promotion 门禁。

离线人工新增条目时，默认使用 `source.type=manual`、`source.from=field-debug / meeting / code-review / lab-test / owner-decision / design-review`、`status=reviewing` 和 `review_status=manual-entry-pending-review`，并在 `validation_refs` 或正文 Evidence Index 中保留 `manual_validation_pending: true`。完成工具复核前不得把条目写成 active fact、owner decision 或 promoted 标准。

人工新增普通条目时，`owner` 必须能在 `registry/owners.json` 中登记；`knowledge-new.sh` 对未知 owner 只输出 warning，不替代 owner registry 或 owner decision。`domain=personal` 或目标路径位于 `domains/personal/` 时，默认使用 `visibility=personal-local`、`status=personal`、`scope=team-general`，不得写入团队 active index。

AI 参与起草、摘要、翻译、分类、抽取或重写时，必须填写 `generated_by_ai`、`ai_role`、`ai_model_or_tool` 和 `ai_generated_at`；2026-06-21 及之后的 `generated_by_ai=true` registry item 缺少这些 provenance 字段会被 `knowledge-check` 阻断。进入 `active` 前必须补 `human_reviewed_by`、`human_reviewed_at` 和 `review_basis`，不得用空 reviewer 或占位文本关闭人工复核门禁。

新增或维护 source 相关条目时，source registry 的 `owner` 必须先登记在 `registry/owners.json`；该字段表示 source 维护责任人，不等同于 owner decision。source 可复核时优先登记稳定只读 `--check "rtk ..."`；只有没有稳定检查入口时才使用 `--no-check-reason`，并在 coverage、manifest 或 Evidence Index 中写清原因和后续复核动作。
source 新增向导的 coverage row `status` 跟随 `--source-status`：`registered`、`deprecated`、`retired` 会分别输出 `registered-pending-classification`、`deprecated-pending-classification`、`retired-pending-classification`，不得把退役或废弃 source 静默写成 registered。
source 新增向导会按 `role`、`write_policy` 和 check/no-check 状态输出 `recommended_final_disposition`、`recommended_migration_strategy` 和中文理由；这些只是人工填写提示，不替代 owner decision，不关闭 owner gate。可复制 registry JSON 默认保持保守，落盘前必须按 `registry/schema.md`、coverage manifest 和 owner gate 状态确认。

`indexes/by-status.md` 使用短 canonical 行维护状态归属，例如 `- reviewing: <id>`；不要把新条目只写入说明行，也不要继续扩展超长 status bucket。
