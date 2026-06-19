# Knowledge Hub Template Schema Gate 2026-06-19

## 目标

把人工新增知识条目时最容易出现的模板字段漂移纳入 `knowledge-check`。本门禁只检查条目模板是否包含 registry 必填字段，不引入复杂 schema 引擎，不自动生成内容，不自动提升状态。

## 范围

- 检查对象：`templates/*.md` 中用于新增知识条目的模板。
- 显式跳过：`templates/README.md` 和 `templates/migration-record.md`。它们分别是模板说明和迁移记录模板，不是 `registry/items.jsonl` 条目模板。
- 基础字段：`id`、`title`、`kind`、`domain`、`path`、`scope`、`visibility`、`status`、`owner`、`source`、`review_after`、`created_at`、`updated_at`。
- `artifact-ref` 额外字段：`uri`、`size`、`sha256`。

## 非目标

- 不检查正文风格，不做中文润色评分。
- 不生成或改写用户内容。
- 不修改源项目 docs。
- 不启用自动化。
- 不提升任何 `reviewing` 条目到 `active`。
- 不写入 `~/.codex/memories`。

## 维护规则

新增 item template 时，先复制已有模板并保留 registry 必填字段。若新增模板不是 item template，必须在 `tools/knowledge-check.sh` 的 `template_skip` 中显式登记，并在对应 manifest 说明原因。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-template-schema-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `rtk bash tools/knowledge-search.sh "template-schema-gate-applied" --json`
- 负向验证：复制仓库到 `/tmp`，删除 `templates/runbook.md` 的 `domain:` 后应报 `template:templates/runbook.md missing domain`。
- 负向验证：复制仓库到 `/tmp`，删除 `templates/artifact-ref.md` 的 `sha256:` 后应报 `template:templates/artifact-ref.md artifact-ref missing sha256`。

## 结果

已落地并验证通过。

- `knowledge-check` 会在非 `--sources-only` 模式下检查 item template 必填字段。
- `templates/README.md` 和 `templates/migration-record.md` 保持显式跳过。
- `templates/artifact-ref.md` 额外检查 `uri`、`size`、`sha256` 字段存在。
- 正向验证通过：`knowledge-check --dry-run --json`、`knowledge-check --sources-only --dry-run --json`、JSON/JSONL 解析和 `git diff --check`。
- 负向验证通过：删除 `/tmp` 副本中的 `templates/runbook.md` `domain:` 字段会失败；删除 `/tmp` 副本中的 `templates/artifact-ref.md` `sha256:` 字段会失败。
