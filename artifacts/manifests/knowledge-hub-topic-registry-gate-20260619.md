# Knowledge Hub Topic Registry Gate 2026-06-19

## 目标

让 `registry/topics.json` 成为可执行的主题导航控制面。每个 topic 必须有唯一 `id`、存在的本地 `domain` 路径，以及来自 registry item kind 枚举的 `allowed_kinds`，避免主题导航、检索入口和人工分类长期漂移。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| TRG-001 | `topics.json` 当前指向的目录存在，但没有门禁防止未来路径漂移。 | 主题入口可能指向已删除或拼错目录。 | 增加 topic domain 相对路径和存在性检查。 |
| TRG-002 | `allowed_kinds` 当前与 item kind 枚举一致，但没有门禁防止拼写漂移。 | 人工分类时可能出现无法被 registry 接受的 kind。 | 增加 allowed kind 枚举检查。 |
| TRG-003 | topic registry 不应升级成复杂分类生成器。 | 过度治理会增加人工新增主题成本。 | 本轮只检查 id、domain、allowed_kinds，不自动生成索引。 |

## 决策

- `knowledge-check` 默认检查 topic id 是否缺失或重复。
- `knowledge-check` 默认检查 topic domain 必须是存在的相对本地路径。
- `knowledge-check` 默认检查 `allowed_kinds` 必须是非空列表，且每个值属于 item kind 枚举。
- 不改变现有 topic 内容。

## 非目标

- 不自动生成 `indexes/by-topic.md`。
- 不要求每个 item 必须匹配某个 topic。
- 不引入复杂主题层级或标签系统。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/topics.json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-topic-registry-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `/tmp` 负向验证：复制仓库后把一个 topic domain 改成不存在路径，`knowledge-check` 应报 `domain path missing`。
- `/tmp` 负向验证：复制仓库后把一个 `allowed_kinds` 值改成未登记 kind，`knowledge-check` 应报 `invalid allowed_kind`。
- `rtk bash tools/knowledge-search.sh "topic-registry-gate-applied" --json`

## 结果

已落地并验证通过。

- 当前 `registry/topics.json` 中所有 topic domain 都是存在的相对本地路径。
- 当前 `registry/topics.json` 中所有 `allowed_kinds` 都属于 registry item kind 枚举。
- `knowledge-check --dry-run --json` 通过。
- `knowledge-check --sources-only --dry-run --json` 通过，保持 source-only 语义不变。
- `/tmp` 负向验证通过：把一个 topic domain 改成不存在路径后，默认检查失败并报告 `domain path missing`。
- `/tmp` 负向验证通过：把一个 `allowed_kinds` 值改成 `not-a-kind` 后，默认检查失败并报告 `invalid allowed_kind`。
- `topic-registry-gate-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
