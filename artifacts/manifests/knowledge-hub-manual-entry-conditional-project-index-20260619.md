# Knowledge Hub manual entry conditional project index 2026-06-19

## 结论

`knowledge-new.sh` 的 `indexes/by-project.md` 草稿现在只在 `--domain projects/...` 时输出。项目条目仍能看到项目导航索引提示，governance 等非项目条目不再被无关项目索引步骤干扰。

这个修复继续保持人工新增向导只读，不创建、不修改、不提交任何文件。

后续增强：`knowledge-hub-manual-entry-project-derivation-20260619` 进一步从 `projects/<project>` 自动推导项目名，并对 `--project` 不一致给出 warning。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| CPI-001 | 上一轮补充项目索引提示后，非项目域条目也会看到 `indexes/by-project.md` 草稿。 | 人工新增 governance、patent、codex 等条目时出现无关步骤，增加维护噪音。 | `knowledge-new.sh` 按 `domain=projects/...` 条件输出项目索引草稿。 |
| CPI-002 | 只验证项目域“有提示”不足以防止非项目噪音回归。 | 后续修改可能再次把项目索引提示变成全局提示。 | `manual-entry-project-index-hint` 回归同时校验项目域有、非项目域无。 |

## 决策

- `by-owner`、`by-review-date`、`by-status` 仍作为所有条目的核心索引提示。
- `by-project` 只对项目域条目输出。
- 不把 `by-project` 改成强覆盖门禁；它仍是导航型人工索引。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-regression-decision --path governance/regression-decision.md` | 0 | 通过；非项目域新增向导不输出 `indexes/by-project.md` | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-conditional-project-index-20260619` |
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id pcr02-regression-runbook --path domains/projects/pcr02/current/runbooks/regression.md` | 0 | 通过；项目域新增向导输出 `indexes/by-project.md` 和目标正文路径 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-conditional-project-index-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；8 个回归场景全部 pass，`manual-entry-project-index-hint` 同时校验项目域和非项目域行为 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-conditional-project-index-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-conditional-project-index-20260619` |

## 边界

- 不自动创建正文、registry、migration 或 index。
- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
