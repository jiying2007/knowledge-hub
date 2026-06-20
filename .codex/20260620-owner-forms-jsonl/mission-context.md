# Mission Context: owner forms JSONL-only 输出

## 目标

为 `tools/knowledge-owner-gates.sh` 增加只读、纯 JSONL 的 owner decision skeleton 输出模式，降低人工保存和机器校验成本。

## 非目标

- 不生成 owner decision。
- 不关闭 owner gate。
- 不修改源项目 docs。
- 不迁移 owner-gated source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## 成功标准

- 新 CLI 参数输出每个 open worksheet 一行紧凑 JSONL，stdout 不包含 Markdown 标题、说明或尾部验证段落。
- 现有 `--forms`、`--forms --json`、`--summary`、`--checklist`、`--validate-forms`、`--landing-plan` 行为不回退。
- 回归测试覆盖纯 JSONL 输出，并同步 regression helper manifest 计数。
- 新能力登记到 manifest、registry、migration 和索引。

## 验证命令

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --forms-jsonl
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-final-gate.sh --json
```
