# Templates

新增 Knowledge Hub 条目时优先使用本目录模板。模板的人读部分默认简体中文；命令、路径、协议字段、API 名称和代码标识保留原样。

## 通用要求

- frontmatter 必须对齐 `registry/schema.md` 的 required fields。
- 正文至少写清摘要、适用范围、权威来源、当前结论、验证与证据、风险与限制、Review。
- 结论、证据、推断、建议分开写。
- 验证与证据优先使用 `governance/evidence-rules.md` 中的 Evidence Index 表格，记录完整 `rtk ...` 命令、退出码、中文摘要和证据路径。
- 外部资料必须提供中文摘要和 source metadata。
- AI 生成、摘要、翻译、分类或重写内容必须标注复核状态。
- 大文件、raw log、SDK、release binary 只登记 artifact 引用，不写入正文。

## 模板清单

- `item.md`：通用知识条目。
- `runbook.md`：操作手册。
- `decision.md`：决策记录。
- `validation-report.md`：验证报告。
- `owner-decision-worksheet.md`：owner 签核表。
- `debug-record.md`：排障记录。
- `external-source-note.md`：外部资料吸收记录。
- `archive-note.md`：归档说明。
- `migration-record.md`：迁移记录。
- `artifact-ref.md`：制品引用。
- `patent-disclosure.md`：专利披露。

`knowledge-new.sh` 是只读人工新增向导，不自动创建文件。模板仍可人工复制使用；复制后必须更新 `id`、`path`、`owner`、`source`、`review_after`、`promotion`、`tags` 和 `validation_refs`，补齐 Evidence Index，并同步 registry、`indexes/by-owner.md`、`indexes/by-review-date.md` 和 `indexes/by-status.md`；如涉及迁移、引用或归档，再补 `registry/migrations.jsonl`；项目域条目还要同步 `indexes/by-project.md` 的项目导航入口；核心索引不得留下 duplicate item reference。

离线人工新增条目时，默认使用 `source.type=manual`、`source.from=field-debug / meeting / code-review / lab-test / owner-decision / design-review`、`status=reviewing` 和 `review_status=manual-entry-pending-review`，并在 `validation_refs` 或正文 Evidence Index 中保留 `manual_validation_pending: true`。完成工具复核前不得把条目写成 active fact、owner decision 或 promoted 标准。

新增或维护 source 相关条目时，source registry 的 `owner` 必须先登记在 `registry/owners.json`；该字段表示 source 维护责任人，不等同于 owner decision。source 可复核时优先登记稳定只读 `--check "rtk ..."`；只有没有稳定检查入口时才使用 `--no-check-reason`，并在 coverage、manifest 或 Evidence Index 中写清原因和后续复核动作。

`indexes/by-status.md` 使用短 canonical 行维护状态归属，例如 `- reviewing: <id>`；不要把新条目只写入说明行，也不要继续扩展超长 status bucket。
