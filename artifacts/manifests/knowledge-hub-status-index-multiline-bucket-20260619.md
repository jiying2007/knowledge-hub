# Knowledge Hub status index multiline bucket 2026-06-19

## 结论

`indexes/by-status.md` 的 canonical status bucket 已由 `tools/knowledge-check.sh` 按行扫描，支持多个 `- active:`、`- reviewing:`、`- archived:` 条目。后续人工新增 registry item 时，应优先新增短的 bucket 行，而不是继续扩展历史超长单行。

## 问题地图

| ID | 发现 | 风险 | 证据 | 本轮动作 |
|---|---|---|---|---|
| status-index-long-line | `indexes/by-status.md` 存在历史超长 `reviewing` 行 | 人工追加时容易误删、重复或造成冲突 | `indexes/by-status.md` 顶部 canonical bucket | 明确多行短条目维护规则 |
| status-parser-multiline | `knowledge-check` 已支持多条同名 canonical bucket 行 | 能力存在但规则未显式化，后续维护者不易判断 | `tools/knowledge-check.sh` 的 `canonical_status_ids` / `status_bucket_ids` | 将规则写入索引说明并登记证据 |
| duplicate-gate-coverage | 多行维护必须防重复 | 重复 item reference 会造成状态漂移 | `knowledge-hub-index-duplicate-gate-20260619` | 保持 duplicate gate 作为安全网 |

## 维护规则

- `by-status.md` 中 canonical bucket 可使用多条同名短行。
- 新增 `reviewing` 项默认使用独立短行或小批量短行。
- 历史超长行已拆分为短 canonical 行；后续继续保持一 item 一短行，并由 duplicate gate 兜底。
- 每个 registry item 在 canonical status bucket 中只能出现一次。
- 状态解释行不属于 canonical bucket，不应放置新的 registry item 状态归属。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，验证多行 status bucket、重复引用和索引覆盖 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-status-index-multiline-bucket-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-status-index-multiline-bucket-20260619` | 0 | 通过；本条目 path 存在，owner/review/status 索引引用均为 1，bucket 为 `reviewing` | `registry/items.jsonl` | Tool | `knowledge-hub-status-index-multiline-bucket-20260619` |
| `rtk bash tools/knowledge-index-plan.sh --section status` | 0 | 通过；registry-derived status 视图显示 109 items，本条目位于 `reviewing` | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-status-index-multiline-bucket-20260619` |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 | 预期负结果；状态为 `needs-owner-review`，PCR02 仍有 7 个 owner gate，终态门禁不得放行 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-status-index-multiline-bucket-20260619` |
| `rtk bash tools/knowledge-search.sh status-index-multiline-bucket-applied --json` | 0 | 通过；检索到 registry item 与 `by-status` 状态说明 | `tools/knowledge-search.sh` | Tool | `knowledge-hub-status-index-multiline-bucket-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不提升 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化，不写 memory。
