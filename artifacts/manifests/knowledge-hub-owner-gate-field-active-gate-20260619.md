# Knowledge Hub Owner Gate Field Active Gate 2026-06-19

## 目标

把 registry item 中显式 owner gate 阻塞信号纳入 `knowledge-check` 默认门禁，防止人工维护时出现“字段写着未过 owner gate，但状态却是 active”的矛盾。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| OGF-001 | owner-gated source_path 门禁已经能拦截 worksheet 中的具体 PCR02 源路径，但 item 自身字段仍可能出现 `owner_gate_verified=false` 与 `status=active` 并存。 | 手工新增条目时可绕过 path-level worksheet 门禁，形成 active 状态漂移。 | `knowledge-check` 拦截 active item 的 `owner_gate_verified=false`。 |
| OGF-002 | `review_status` 已被用于记录 `pending-owner-review`、`needs-owner-resolution`、`source-identity-match` 等 owner 流程状态，但此前没有禁止这些状态进入 active。 | 控制面说明与 registry 状态冲突，后续索引和检索会误把未闭环内容视为可用事实。 | 对明确阻塞型 `review_status` 建立 active hard gate。 |
| OGF-003 | 不能用宽泛关键词扫描所有 `review_status`。 | 可能误伤已经 applied 的治理制品，例如 `owner-gated-active-gate-applied`。 | 只匹配固定阻塞状态集合，不匹配包含 owner 字样的 applied 状态。 |

## 决策

- `status=active` 且 `owner_gate_verified=false` 时失败。
- `status=active` 且 `review_status` 是明确阻塞 owner 状态时失败。
- 当前阻塞状态集合包括：
  - `pending-owner-review`
  - `needs-owner-resolution`
  - `owner-intake-ready`
  - `source-identity-match`
  - `embedded-knowledge-owner-review-required`
  - `blocked-pending-owner-review`
  - `blocked-pending-owner-status-decision`
  - `blocked-personal-local`
  - `blocked-pending-archive-metadata`
- 未设置这些字段的历史条目不受影响。

## 非目标

- 不自动生成 owner 决策。
- 不自动修复 registry item。
- 不修改源项目 docs。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 本门禁默认启用后全仓通过，0 errors，0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | owner-gate-field-active-gate |
| `/tmp owner_gate_verified=false active fixture` | 1 | 临时副本把 active item 设置为 `owner_gate_verified=false` 后，仅触发 `owner-gated-active` 一类错误。 | `/tmp/kh-owner-field-false.*` | Negative fixture | owner-gate-field-active-gate |
| `/tmp blocking review_status active fixture` | 1 | 临时副本把 active item 设置为 `review_status=pending-owner-review` 后，仅触发 `owner-gated-active` 一类错误。 | `/tmp/kh-owner-field-status.*` | Negative fixture | owner-gate-field-active-gate |
| `rtk bash tools/knowledge-search.sh owner-gate-field-active-gate-applied --json` | 0 | 可检索到 3 处登记和说明，包括 registry item、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md` | Knowledge Hub | owner-gate-field-active-gate |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：如需要允许更多 owner gate 终态，应先结构化枚举，再更新 `tools/knowledge-check.sh` 和本 manifest。
