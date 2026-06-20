# Knowledge Hub owner placeholder quoting（2026-06-20）

## 结论

面向人工复制的 owner form 校验命令示例现在统一写成：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

这样可以避免维护者直接复制 Markdown 示例时，shell 把 `<owner-decisions.jsonl>` 误解释为输入重定向。

## 范围

已统一以下人读文档和治理包中的命令示例：

- `README.md`
- `tools/README.md`
- PCR02 consolidated owner decision intake execution package
- 7 个 PCR02 single-item owner-ready package
- `knowledge-hub-owner-decision-form-validation-20260619.md`
- `knowledge-hub-status-owner-landing-command-20260620.md`

## 边界

- 不改变 `tools/knowledge-owner-gates.sh` 行为。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改源项目 docs。
- 不自动写 owner 表单文件。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk rg -n -- "--validate-forms <owner-decisions\\.jsonl>" README.md tools/README.md artifacts/manifests/*.md` | expected 1 | 通过；未发现面向人工 Markdown 中未加引号的 owner form 占位符命令。 | `README.md`; `tools/README.md`; `artifacts/manifests/*.md` | Docs | owner-placeholder-quoting |
| `rtk rg -n -- "--validate-forms '<owner-decisions\\.jsonl>'" README.md tools/README.md artifacts/manifests/*.md` | 0 | 通过；22 处人读命令示例使用带引号占位符。 | `README.md`; `tools/README.md`; `artifacts/manifests/*.md` | Docs | owner-placeholder-quoting |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，本 manifest、registry、migration 和索引登记一致。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-placeholder-quoting |
| `rtk bash tools/knowledge-final-gate.sh --json` | expected 1 | 终态门禁仍返回 `needs-owner-review`，因为 7 条 owner gate 尚未由 owner 人工签收。 | `tools/knowledge-final-gate.sh` | Knowledge Hub | owner-placeholder-quoting |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`owner-placeholder-quoting-applied`
- 下一次复核内容：新增人读 shell 命令模板时，带占位符的路径参数应使用引号或改用明确的真实示例路径，避免 shell 重定向歧义。
