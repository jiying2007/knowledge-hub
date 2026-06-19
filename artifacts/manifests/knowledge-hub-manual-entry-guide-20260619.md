# Knowledge Hub Manual Entry Guide 2026-06-19

## 目标

把新增知识条目的入口从“空壳报错”改为“只读人工向导”，降低人工维护成本，同时避免引入复杂生成器或强制自动化。

## 源事实

- `templates/` 已经提供常用条目模板。
- `registry/items.jsonl`、核心索引和 `registry/migrations.jsonl` 已有机器门禁。
- 人工仍应能够直接新增内容；脚本只能降低遗忘步骤的概率，不能成为唯一入口。

## 问题地图

| ID | 发现 | 风险 | 本次动作 |
|---|---|---|---|
| MEG-001 | `tools/knowledge-new.sh` 只提示 bootstrap 未启用并退出 3 | README 或人工新增入口不友好 | 改为只读人工新增向导 |
| MEG-002 | 人工新增需同步 registry、index、migration，步骤分散 | 容易漏登记或形成漂移 | 向导输出最小同步清单 |
| MEG-003 | 直接实现写入生成器会增加维护复杂度 | 自动化入口可能成为新瓶颈 | 本次不写文件、不启用 apply |

## 已落盘

- 更新 `tools/knowledge-new.sh`：支持 `--kind`、`--domain`、`--project`、`--id`、`--path`，只输出人工维护清单。
- 更新 `README.md`：新增人工新增最短路径和 `knowledge-new.sh` 常用命令。
- 更新 `tools/knowledge-new.sh`：补充 usage 示例和缺少参数值的友好错误。
- 更新 `tools/README.md`：登记 `knowledge-new.sh` 为只读人工新增向导。
- 更新 `templates/README.md`：说明模板仍可人工复制，脚本不是唯一入口。
- 更新 registry、migration 和索引，登记本治理制品。

## 非目标

- 不生成 registry 行。
- 不创建正文文件。
- 不自动修改索引。
- 不提交、发布、提升或写 memory。

## 验证计划

- `rtk bash tools/knowledge-new.sh --help`
- `rtk bash tools/knowledge-new.sh --kind runbook --domain projects/pcr02 --project pcr02 --id sample --path domains/projects/pcr02/current/runbooks/sample.md`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-search.sh "manual-entry-guide-applied" --json`
- `rtk git diff --check`

## 状态

- `review_status`: manual-entry-guide-applied
- `status`: reviewing
- `owner`: leiwenjun
- `review_after`: 2026-09-19
