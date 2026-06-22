# Knowledge Hub owner landing audit and manual index closeout 2026-06-21

## 结论

本轮把 PCR02 owner gate 人工落地从“有 landing plan”推进到“有只读 landing audit”。`knowledge-owner-gates.sh --landing-audit` 会在 owner 表单通过校验后，显式列出 worksheet、registry、migration 和 index 的人工落点，并提醒 `pcr02-owner-decision-worksheets-20260618.jsonl` 对应行必须进入 resolved / owner-approved / approved / closed 等人工签收状态，否则 owner gate 仍保持 open。

同时补齐两类长期维护入口：

- `knowledge-new.sh` 对普通条目输出条件索引提示：只有 source 已登记时才同步 `indexes/by-source.md`，`kind=decision` 才同步 `indexes/by-decision.md`，未知 source 不伪造 source id。
- `knowledge-index-plan.sh --section manifest` 对历史 unpaired manifest 输出 `expected` / `needs_review` 只读分类，避免历史例外被误当作新增单边文件惯例。

## 改动范围

- `tools/knowledge-owner-gates.sh`：新增 `--landing-audit`，输出只读人工落地审计；`--summary` 增加 owner 级 landing audit 命令模板。
- `tools/knowledge-status.sh`：状态看板、next action、strict blocker 均暴露 owner / source / next-open landing audit 模板。
- `tools/knowledge-new.sh`：普通新增向导增加 by-source / by-decision 条件索引骨架。
- `tools/knowledge-index-plan.sh`：manifest 恢复视图增加 unpaired 分类、原因和中文说明。
- `tools/knowledge-regression.sh`：扩展既有 70 个场景的断言，不新增场景数量；覆盖 landing audit、条件索引和 unpaired 分类。
- `README.md` 与 `tools/README.md`：同步人工维护路径说明。

## 人工边界

- 不生成 owner decision。
- 不关闭 PCR02 7 个 open owner gate。
- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | 语法检查通过，新增 landing audit 参数和输出路径可解析 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash -n tools/knowledge-status.sh` | 0 | 语法检查通过，status landing audit 模板可解析 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash -n tools/knowledge-index-plan.sh` | 0 | 语法检查通过，manifest unpaired 分类路径可解析 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash -n tools/knowledge-new.sh` | 0 | 语法检查通过，条件索引提示路径可解析 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | 语法检查通过，回归断言可解析 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json` | 0 | owner dispatch 输出 landing audit 命令模板 | `tools/knowledge-owner-gates.sh` | Owner Gate | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash tools/knowledge-status.sh --json` | 0 | status dashboard 输出 owner/source/next-open landing audit 恢复模板 | `tools/knowledge-status.sh` | Status | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash tools/knowledge-index-plan.sh --section manifest --json` | 0 | manifest 视图输出 unpaired expected / needs_review 只读分类 | `tools/knowledge-index-plan.sh` | Index Plan | `knowledge-hub-owner-landing-audit-manual-index-20260621` |
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-regression-decision --path governance/regression-decision.md` | 0 | 人工新增向导输出 by-source 条件提示和 by-decision 决策索引提示 | `tools/knowledge-new.sh` | Manual Entry | `knowledge-hub-owner-landing-audit-manual-index-20260621` |

## 后续

1. 等真实 owner 填写 `owner-decisions.jsonl` 后，先运行 `--validate-forms`。
2. 再运行 `--landing-plan` 和 `--landing-audit`，人工核对 worksheet、registry、migration 和 index。
3. 人工落地后运行 `knowledge-owner-gates.sh --status all --json`、`knowledge-check.sh --dry-run --json --diagnostics`、`knowledge-status.sh --strict --json` 和 `knowledge-final-gate.sh --json`。
