# Knowledge Hub Owner Registry Gate 2026-06-19

## 目标

让 `registry/owners.json` 成为可执行的 owner 控制面，而不是只登记一个默认人名的静态文件。所有 `registry/items.jsonl` 条目的 `owner` 都必须能在 `registry/owners.json` 找到，避免 owner 拼写漂移、临时责任人残留和后续人工复核无人接手。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| ORG-001 | `registry/items.jsonl` 使用了 `leiwenjun`、`pcr02-registry-owner`、`team-core` 三类 owner。 | owner id 已经形成事实集合。 | 以当前 item owner 集合为准补齐 `registry/owners.json`。 |
| ORG-002 | `registry/owners.json` 只登记 `leiwenjun`。 | owner registry 与 items 漂移，人工维护时无法判断 owner 是否拼写正确。 | 增加 owner 注册门禁。 |
| ORG-003 | 直接引入复杂 owner 权限模型会增加维护负担。 | 过度治理会让人工新增内容变慢。 | 本轮只检查 owner id 存在和重复，不做权限、组织层级或审批流。 |

## 决策

- `registry/owners.json` 补齐 `pcr02-registry-owner` 和 `team-core`。
- `knowledge-check` 默认检查所有 item owner 是否已注册。
- `knowledge-check` 检查 owner id 是否缺失或重复。
- 不改变 item 的现有 owner，不做责任重分配。

## 非目标

- 不引入团队组织架构或权限模型。
- 不要求 owner 必须是个人；允许 `team-core` 这类团队 owner。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/owners.json`
- `rtk jq -c . artifacts/manifests/knowledge-hub-owner-registry-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `/tmp` 负向验证：复制仓库后把一个 item owner 改成未登记 owner，`knowledge-check` 应报 `owner not registered`。
- `/tmp` 负向验证：复制仓库后复制一个 owner 对象形成重复 id，`knowledge-check` 应报 duplicate owner。
- `rtk bash tools/knowledge-search.sh "owner-registry-gate-applied" --json`

## 结果

已落地并验证通过。

- `registry/owners.json` 已登记当前 item 使用的 `leiwenjun`、`pcr02-registry-owner` 和 `team-core`。
- `knowledge-check --dry-run --json` 通过。
- `knowledge-check --sources-only --dry-run --json` 通过，保持 source-only 语义不变。
- `/tmp` 负向验证通过：把一个 item owner 改成 `unknown-owner` 后，默认检查失败并报告 `owner not registered: unknown-owner`。
- `/tmp` 负向验证通过：把一个 owner id 改成重复的 `leiwenjun` 后，默认检查失败并报告 `owners:leiwenjun duplicate id`。
- `owner-registry-gate-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
