# Knowledge Hub Evidence Index Template Alignment 2026-06-19

## 目标

让人工新增、验证报告和治理 manifest 使用同一种命令级证据索引写法，避免后续只留下“已验证”“pass”这类不可复核描述。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| EIT-001 | `governance/evidence-rules.md` 已要求记录 cwd、date、command、exit_code、scope、result_summary 和 artifact_refs，但没有统一表格。 | 不同条目的验证证据结构不一致，人工复核需要重新解释每份文档。 | 增加 Evidence Index 表格规范。 |
| EIT-002 | `templates/item.md` 和 `templates/validation-report.md` 仍使用散列表达命令证据。 | 新条目容易只写少数字段，缺少可横向比较的证据索引。 | 模板改为 Evidence Index 表格，并保留 date/cwd/scope 补充字段。 |
| EIT-003 | `knowledge-new.sh` 的人工向导没有提示写 Evidence Index。 | 人工新增条目可能完成 registry/index/source-policy，但未留下可审查验证证据。 | 只读向导增加 Evidence Index 步骤和可复制表格。 |

## 决策

- Evidence Index 使用固定列：`Command`、`Exit Code`、`Result Summary`、`Evidence Path`、`Layer`、`Related Artifact`。
- `Command` 必须保留完整 `rtk ...` 命令。
- `Result Summary` 必须是中文摘要，说明命令证明了什么。
- 本次只调整文档、模板和只读向导，不新增生成器，不执行 `validation_refs`。

## 非目标

- 不修改源项目 docs。
- 不启用自动化。
- 不生成或自动修复索引。
- 不改变 `knowledge-check`、`knowledge-doctor` 或 `knowledge-search` 的行为。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk rg -n "Evidence Index|Result Summary|Related Artifact" governance/evidence-rules.md templates/README.md templates/item.md templates/validation-report.md tools/knowledge-new.sh`
- `rtk bash -n tools/knowledge-new.sh`
- `rtk bash tools/knowledge-new.sh --kind validation --domain governance --id sample-evidence-index --path artifacts/manifests/sample-evidence-index.md`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-search.sh evidence-index-template-applied --json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-evidence-index-template-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk git diff --check`

## 结果

- `rtk rg -n "Evidence Index|Result Summary|Related Artifact" governance/evidence-rules.md templates/README.md templates/item.md templates/validation-report.md tools/knowledge-new.sh`：通过，规则、模板和只读人工向导均包含 Evidence Index 入口。
- `rtk bash -n tools/knowledge-new.sh`：通过，脚本语法有效。
- `rtk bash tools/knowledge-new.sh --kind validation --domain governance --id sample-evidence-index --path artifacts/manifests/sample-evidence-index.md`：通过，输出验证报告模板、人工步骤和可复制 Evidence Index 表格，未写文件。
- `rtk bash tools/knowledge-check.sh --dry-run --json`：通过，`status=pass`。
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`：通过，`status=pass`，0 errors / 0 warnings。
- `rtk bash tools/knowledge-search.sh evidence-index-template-applied --json`：通过，可检索到 registry、status index 和本 manifest。
- `rtk jq -c . artifacts/manifests/knowledge-hub-evidence-index-template-20260619.jsonl`：通过，JSONL 格式有效。
- `rtk jq -c . registry/items.jsonl`：通过，registry 条目格式有效。
- `rtk jq -c . registry/items.jsonl`：通过，migration 记录格式有效。
- `rtk git diff --check`：通过，无空白错误。
