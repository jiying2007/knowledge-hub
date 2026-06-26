# Knowledge Hub Project Registry Gate 2026-06-19

## 目标

让 `registry/projects.json` 成为可执行的项目控制面。所有 `registry/items.jsonl` 中 `domain=projects/<project>` 的 `<project>` 都必须能在 `registry/projects.json` 找到，避免项目 id 拼写漂移、临时项目目录残留和跨项目边界不清。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| PRG-001 | 当前 items 中只有 `projects/pcr02`，`registry/projects.json` 也只登记 `pcr02`。 | 当前状态一致，但没有门禁防止未来漂移。 | 增加 item project id 注册检查。 |
| PRG-002 | `registry/projects.json` 本身没有 id 唯一性检查。 | 重复 project id 会让后续索引、迁移和 owner review 模糊。 | 增加 project id 缺失和重复检查。 |
| PRG-003 | 项目治理不应升级为复杂生命周期系统。 | 过度治理会拖慢人工新增项目资料。 | 本轮只检查 id 存在和重复，不检查生命周期、owner 或外部路径可用性。 |

## 决策

- `knowledge-check` 默认检查 `registry/projects.json` 中 project id 是否缺失或重复。
- `knowledge-check` 默认检查 `registry/items.jsonl` 中 `domain=projects/<project>` 的 `<project>` 是否已登记。
- 不改变现有项目条目 owner、状态或路径。

## 非目标

- 不引入项目权限、生命周期或归档状态模型。
- 不检查 `legacy_docs`、`legacy_archive` 外部路径是否存在。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/projects.json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-project-registry-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `/tmp` 负向验证：复制仓库后把一个 item domain 改成 `projects/unknown-project`，`knowledge-check` 应报 `project not registered`。
- `/tmp` 负向验证：复制仓库后复制一个 project 对象形成重复 id，`knowledge-check` 应报 duplicate project。
- `rtk bash tools/knowledge-search.sh "project-registry-gate-applied" --json`

## 结果

已落地并验证通过。

- 当前 items 使用的项目域只有 `projects/pcr02`，且 `registry/projects.json` 已登记 `pcr02`。
- `knowledge-check --dry-run --json` 通过。
- `knowledge-check --sources-only --dry-run --json` 通过，保持 source-only 语义不变。
- `/tmp` 负向验证通过：把一个 item domain 改成 `projects/unknown-project` 后，默认检查失败并报告 `project not registered: unknown-project`。
- `/tmp` 负向验证通过：复制一个 `pcr02` project id 后，默认检查失败并报告 `projects:pcr02 duplicate id`。
- `project-registry-gate-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
