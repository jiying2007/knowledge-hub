# Knowledge Hub Item Discoverability Gate 2026-06-19

## 目标

把 `registry/items.jsonl` 中影响人工检索和提升状态判断的基础字段压实为低复杂度门禁，避免新增条目缺少 `tags`、遗漏 `promotion` 或写出未定义 promotion 状态。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| IDG-001 | `tags` 虽然在现有条目中普遍存在，但此前不是 schema 必填门禁。 | 人工新增条目后可能可登记但不可稳定检索，AI 也缺少召回锚点。 | `knowledge-check` 要求 item 有非空 `tags`，且每个 tag 是非空 string。 |
| IDG-002 | `promotion` 在现有条目中全部为 `none`，但此前不是必填字段。 | 新条目可能遗漏 promotion 状态，后续无法区分“未提升”和“漏登记”。 | `knowledge-check` 要求 item 有 `promotion` 字段。 |
| IDG-003 | 未定义 promotion 值可能被直接写入 registry。 | promotion 状态漂移会绕过 owner review 和长期提升流程。 | 当前只允许 `promotion=none`；未来新增状态必须先扩展 schema 和门禁。 |

## 决策

- `tags` 成为 item 必填字段，必须是非空 list。
- `tags` 每个元素必须是非空 string。
- `promotion` 成为 item 必填字段。
- 当前允许的 item `promotion` 值仅为 `none`。
- 更新 item 模板，人工新增条目默认从 `promotion: none` 开始。

## 非目标

- 不启用 promotion 自动化。
- 不改变现有条目的 owner、status、review_after 或 promotion。
- 不引入新的 promotion 状态。
- 不修改源项目 docs。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-discoverability-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后删除一个 item 的 `tags`，`knowledge-check` 应报 missing tags。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `tags` 改成字符串，`knowledge-check` 应报 tags must be list。
- `/tmp` 负向验证：复制仓库后删除一个 item 的 `promotion`，`knowledge-check` 应报 missing promotion。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `promotion` 改成未定义值，`knowledge-check` 应报 invalid promotion。
- `rtk bash tools/knowledge-search.sh item-discoverability-gate-applied --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-discoverability-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` missing-tags 负向验证：删除本条目的 `tags` 后，`knowledge-check` 报 `items:knowledge-hub-item-discoverability-gate-20260619 missing tags`。
- `/tmp` tags-type 负向验证：把本条目的 `tags` 改成字符串后，`knowledge-check` 报 `items:knowledge-hub-item-discoverability-gate-20260619 tags must be list`。
- `/tmp` missing-promotion 负向验证：删除本条目的 `promotion` 后，`knowledge-check` 报 `items:knowledge-hub-item-discoverability-gate-20260619 missing promotion`。
- `/tmp` invalid-promotion 负向验证：把本条目的 `promotion` 改成 `candidate` 后，`knowledge-check` 报 `items:knowledge-hub-item-discoverability-gate-20260619 invalid promotion: candidate`。
- `rtk bash tools/knowledge-search.sh item-discoverability-gate-applied --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。
