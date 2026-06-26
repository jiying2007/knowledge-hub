# Knowledge Hub Item Source Reference Gate 2026-06-19

## 目标

让 `registry/items.jsonl` 中的 `source` 引用保持可追溯，避免长期维护时出现 source id 拼写漂移、migration manifest 失效、hash 字段不可验证或 artifact-ref 元数据不可用。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| ISG-001 | item `source.source_id` 引用外部 source registry，但此前没有逐条校验。 | source 改名或人工拼写错误后，迁移和引用来源失去可追溯性。 | `knowledge-check` 要求存在的 `source.source_id` 必须登记在 `registry/sources.json`。 |
| ISG-002 | item `source.source_control_manifest` 是迁移证据入口，但可能残留失效路径。 | 后续无法复核为什么迁移、从哪里迁移、怎样回滚。 | `knowledge-check` 要求存在的 `source_control_manifest` 是相对本地路径且文件存在。 |
| ISG-003 | `source_sha256` 和 artifact-ref `sha256` / `size` 是制品身份字段。 | hash 拼写、大小写或 size 类型漂移会削弱 artifact/ref 治理。 | `knowledge-check` 要求 SHA256 为小写 64 位 hex，artifact size 为正整数。 |

## 决策

- item `source` 必须是 object。
- item `source.source_id` 存在时必须属于 `registry/sources.json`。
- item `source.source_control_manifest` 存在时必须是相对路径，并指向 Knowledge Hub 内已存在文件。
- item `source.source_sha256` 存在时必须是小写 64 位 SHA256 hex。
- `artifact-ref` item 的 `sha256` 必须是小写 64 位 SHA256 hex，`size` 必须是正整数。

## 非目标

- 不访问外部源文件。
- 不重新计算 source hash。
- 不修改 PCR02 源项目 docs。
- 不改变已有 source authority、owner、status 或 promotion。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-source-ref-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后把一个 item 的 `source.source_id` 改成未登记 id，`knowledge-check` 应报 source_id not registered。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `source.source_control_manifest` 改成缺失路径，`knowledge-check` 应报 source_control_manifest missing。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `source.source_sha256` 改成非法 hash，`knowledge-check` 应报 invalid source_sha256。
- `/tmp` 负向验证：复制仓库后把 artifact-ref item 的 `size` 改成字符串，`knowledge-check` 应报 invalid artifact size。
- `rtk bash tools/knowledge-search.sh "item-source-ref-gate-applied" --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-item-source-ref-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` unregistered-source-id 负向验证：把一个 item 的 `source.source_id` 改成 `ghost-source` 后，`knowledge-check` 报 `items:migrated-pcr02-docs-copyfirst-001 source_id not registered: ghost-source`。
- `/tmp` missing-migration-manifest 负向验证：把一个 item 的 `source.source_control_manifest` 改成 `artifacts/manifests/missing-migration.jsonl` 后，`knowledge-check` 报 `items:migrated-pcr02-docs-copyfirst-001 source_control_manifest missing: artifacts/manifests/missing-migration.jsonl`。
- `/tmp` invalid-source-sha 负向验证：把一个 item 的 `source.source_sha256` 改成 `not-a-sha` 后，`knowledge-check` 报 `items:migrated-pcr02-docs-copyfirst-001 invalid source_sha256: not-a-sha`。
- `/tmp` invalid-artifact-size 负向验证：把 artifact-ref item 的 `size` 改成字符串 `"394"` 后，`knowledge-check` 报 `items:pcr02-prog-tool-ci-smoke-session-ref-20260618 invalid artifact size: 394`。
- `rtk bash tools/knowledge-search.sh "item-source-ref-gate-applied" --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。
