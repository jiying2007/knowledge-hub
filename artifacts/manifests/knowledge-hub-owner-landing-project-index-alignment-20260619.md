# Knowledge Hub owner landing project index alignment 2026-06-19

## 结论

`tools/knowledge-owner-gates.sh --landing-plan` 的人工落地文件清单已补齐 `indexes/by-project.md`，与 `pcr02-owner-resolution-playbook-20260618` 中的 owner 决策落地规则保持一致。

这个修复不关闭 owner gate，不生成 owner decision，不自动修改 registry/index，也不修改源项目 docs。它只让 owner 决策返回后的人工落地计划不再漏掉项目导航索引。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| OPI-001 | owner resolution playbook 要求 owner 决策落地至少同步 `indexes/by-project.md`，但 landing plan 的 `required_manual_files` 未列出。 | owner 决策人工落地时可能只改 status/owner/date/topic 索引，遗漏项目导航入口。 | 在 landing plan required files 中加入 `indexes/by-project.md`。 |
| OPI-002 | 该规则如果只靠文档提醒，后续工具改动可能再次退化。 | 维护者在真正 owner 决策返回后才发现索引缺失。 | 在 `tools/knowledge-regression.sh` 增加 `owner-landing-plan-project-index` 回归场景。 |

## 决策

- `required_manual_files` 包含：
  - `artifacts/manifests/<owner-decision-landing-YYYYMMDD>.jsonl`
  - `registry/items.jsonl`
  - `registry/items.jsonl`
  - `indexes/by-project.md`
  - `indexes/by-status.md`
  - `indexes/by-owner.md`
  - `indexes/by-review-date.md`
  - `indexes/by-topic.md`
- landing plan 的中文人工动作同步提示 `by-project`。
- 回归场景使用 `/tmp` owner decision fixture，只验证计划结构，不落地 owner decision。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；7 个回归场景全部 pass，包含新增 `owner-landing-plan-project-index` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-owner-landing-project-index-alignment-20260619` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-001 --validate-forms <fixture> --landing-plan --json` | 0 | 通过；`landing_plan.required_manual_files` 包含 `indexes/by-project.md` 和 `indexes/by-status.md` | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-landing-project-index-alignment-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-landing-project-index-alignment-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不自动改 registry/index/migration。
- 不启用自动化，不写 memory。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
