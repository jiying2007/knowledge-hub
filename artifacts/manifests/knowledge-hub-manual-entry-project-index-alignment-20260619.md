# Knowledge Hub manual entry project index alignment 2026-06-19

## 结论

`knowledge-new.sh` 和 `templates/README.md` 已补充项目域条目的 `indexes/by-project.md` 导航入口要求。人工新增项目知识时，向导不再只提示 registry、owner/date/status 索引和 migration，而会明确提醒维护项目导航索引；非项目域条目不输出 `by-project` 草稿，避免无关维护噪音。

这个修复保持只读，不生成文件，不自动改索引，不启用自动化。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| MPI-001 | 人工新增项目域条目时，`knowledge-new.sh` 没提示 `indexes/by-project.md`。 | registry 和核心门禁可通过，但项目导航入口缺失，长期可发现性下降。 | 在最小人工步骤和可复制索引草稿中加入项目索引提示。 |
| MPI-002 | 模板说明同样只强调核心索引。 | 人工直接复制模板时可能绕过 `knowledge-new.sh`，仍然漏项目入口。 | 更新 `templates/README.md`。 |
| MPI-003 | 仅靠文档提示容易退化。 | 后续修改向导时可能再次漏掉项目索引，或对非项目条目产生噪音。 | 在 `knowledge-regression.sh` 增加 `manual-entry-project-index-hint` 场景，同时校验项目域有提示、非项目域无提示。 |

## 决策

- `knowledge-new.sh` 仍然只读，人工仍可直接按模板新增内容。
- 项目域条目提示 `indexes/by-project.md`，但不把 `by-project` 改成强制覆盖每个 registry item 的门禁。
- 回归校验项目域示例输出包含 `indexes/by-project.md` 和目标正文路径，同时校验 governance 非项目示例不输出项目索引草稿。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id pcr02-regression-runbook --path domains/projects/pcr02/current/runbooks/regression.md` | 0 | 通过；项目域新增向导输出 `indexes/by-project.md` 和目标正文路径 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-project-index-alignment-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；8 个回归场景全部 pass，包含新增 `manual-entry-project-index-hint` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-project-index-alignment-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-project-index-alignment-20260619` |

## 边界

- 不自动创建正文、registry、source policy 或 index。
- 不把 `indexes/by-project.md` 纳入每条 registry item 的强覆盖门禁。
- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
