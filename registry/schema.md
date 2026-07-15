---
title: Registry 中文可读性与证据字段扩展
summary_zh: 登记 registry/schema 中面向中文可读性、证据强度、AI provenance、人审状态和边界声明的字段扩展。该 active 条目只约束 registry 字段语义，不允许用字段补充伪造人工复核或绕过 owner
  gate。
tags:
- registry
- schema
- readability
- evidence
- ai-provenance
id: knowledge-hub-registry-schema-readability-extension
kind: standard
domain: governance
path: registry/schema.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- Registry 中文可读性与证据字段扩展
related:
- indexes/obsidian-home.md
---

# Registry Schema

## items.jsonl

每行一个知识条目。

Required fields:

- `id`
- `title`
- `kind`
- `domain`
- `path`
- `scope`
- `visibility`
- `status`
- `owner`
- `source`
- `review_after`
- `validation_refs`
- `review_status`
- `created_at`
- `updated_at`
- `promotion`
- `tags`

Recommended readability fields:

- `summary_zh`
- `source_language`
- `primary_language`
- `translation_status`
- `terminology_status`
- `glossary_refs`

Recommended evidence fields:

- `evidence_strength`
- `evidence_refs`
- `review_status`
- `owner_gate_verified`

Recommended AI provenance fields:

- `generated_by_ai`
- `ai_role`
- `ai_model_or_tool`
- `ai_generated_at`
- `human_reviewed_by`
- `human_reviewed_at`
- `review_basis`
- `human_review_decision`

AI human review decision values:

```text
accept-as-review-record
needs-edits
archive-only
reject
defer
```

`human_review_decision` 记录真实人工复核结论，不等同于 owner decision、active promotion 或 source 项目授权。`needs-edits` 和 `defer` 表示复核未闭环，在 product strict status 中仍是 blocker。

Recommended external-source fields:

- `retrieved_at`
- `read_status`
- `source_license`
- `promotion_decision`

Date invariants:

- `created_at`, `updated_at` and `review_after` must use ISO date format: `YYYY-MM-DD`.
- `updated_at` must be the same date as or later than `created_at`.
- stale `review_after` is a warning, not an error; it should guide human review without blocking unrelated maintenance.

Markdown frontmatter mirror invariants:

- 已登记 Markdown 正文若声明 `status`、`owner`、`review_after`，这些字段必须与 `registry/items.jsonl` 一致。历史正文不强制批量补 frontmatter；一旦声明就进入漂移门禁。
- registry 是生命周期和责任字段权威；`current/`、`decisions/` 等 canonical 路径不隐含 active 状态。
- frontmatter 漂移必须修正文镜像或 registry 事实，不能通过改变目录名掩盖。

## body-coverage.json

`registry/body-coverage.json` 仅为冻结历史语料和领域/治理基线提供集合级正文路径覆盖，避免对低价值索引页机械创建 item。精确 `items.jsonl` path 始终优先。

- 每个 collection 必须包含唯一 `id`、规范化 `path_prefix`、`coverage_mode`、已登记 `owner`、ISO `review_after`、正整数 `expected_markdown_count`、小写 64 位 `inventory_sha256` 和中文 `reason_zh`。
- `coverage_mode` 只允许 `archive-corpus`、`domain-baseline`、`governance-baseline`。
- inventory hash 只对该前缀下纳入正文扫描范围的 repo-relative Markdown 路径排序后计算；正文内容变化不改变集合身份，路径新增、删除或改名会使门禁失败。
- 集合覆盖不创建 registry item，不赋予 status，不生成 owner decision 或 promotion，也不替代新增当前事实、决策、验证和治理规范的逐条登记。
- `knowledge-orphan-files.sh --all --strict --json` 是集合契约的直接验证入口；`knowledge-check` 会复用该结果。

Source reference invariants:

- item `source` must be an object.
- item `source.source_id`, when present, must be registered in either `registry/sources.json` current sources or `registry/retired-sources.jsonl` provenance ledger.
- item `source.source_manifest`, when present, must be a relative existing Knowledge Hub local path.
- item `source.source_sha256`, when present, must be a lowercase 64-character SHA256 hex string.
- active item `source.source_id` + `source.source_path` must not match an unresolved owner-gated row in owner decision worksheet manifests.
- active item must not use `owner_gate_verified=false`.
- active item must not use blocking owner-gate `review_status` values such as `pending-owner-review`, `needs-owner-resolution`, `owner-intake-ready`, `source-identity-match` or `embedded-knowledge-owner-review-required`.
- `artifact-ref` item `sha256` must be a lowercase 64-character SHA256 hex string, and `size` must be a positive integer.

Source control directory invariants:

- 每个 current 或 retired source 必须有 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- `inventory.jsonl` 每行至少包含：`id`、`source_id`、`source_path`、`object_type`、`hub_disposition`、`target_path`、`status`、`reason_zh`、`risk_zh`、`checked_at`。
- `object_type` 允许值：`markdown`、`session`、`history`、`tool`、`source-code`、`config`、`artifact`、`binary`、`log`、`archive`、`manifest`、`automation-run`、`unknown`。
- `hub_disposition` 允许值：`copy-body`、`summary-only`、`artifact-ref`、`reference-only`、`archive-only`、`hash-only-provenance`、`exclude`。
- `status` 允许值：`pending`、`covered`、`blocked`、`excluded`。
- `target_path` 必须是 repo-relative local path、source-local reference 或空值；不得使用绝对路径、`./` 或 `../`。
- `session`、`history`、`source-code`、`binary`、`log` 不能使用 `copy-body`，只能使用摘要、引用、artifact-ref、archive-only、hash-only-provenance 或 exclude。
- 正文最大迁移 profile 下，`copy-body` 只允许用于 `object_type=markdown` 且 `target_path` 指向 Hub 正文目录 `projects/`、`domains/` 或 `notes/` 下的现存路径；其他正文迁移动作必须改为 summary-only、artifact-ref、reference-only、archive-only 或 exclude。
- 正文最大迁移 profile 下，`status=pending` 的 inventory row 是 blocker；`covered`、`blocked`、`excluded` 才能表达已分类终态，其中 `blocked` 必须写清 `reason_zh` 和 `risk_zh`。
- owner decision landing 产生本地 target 时，`knowledge-check` 按硬切换后的 canonical path 校验目标存在；`domains/projects/<project>/...` 与 `domains/personal/...` 不再自动映射，当前 owner decision 不得继续使用旧入口。

Validation reference invariants:

- `active` and `reviewing` items must have non-empty `validation_refs`.
- `validation_refs`, when present, must be a list of non-empty strings.
- validation refs that are plain local Knowledge Hub paths must be normalized repository-relative paths and must exist.
- absolute paths, `./` paths, `../` paths, and unsupported path-like refs are rejected unless they are part of a command-shaped ref.
- command-shaped refs are recorded but not executed by `knowledge-check`.

Manual offline minimum fields:

- 人工在 AI、Codex、网络或工具不可用时也可以先写正文和 registry/index，但必须保留 `validation_refs` 与 `review_status`。
- 证据暂时不足时，`status` 使用 `reviewing`，`review_status` 使用 `manual-entry-pending-review`，`validation_refs` 至少填写人工可复核路径、现场记录或 no-check reason。
- 无法立即运行工具时，在正文或相邻维护记录中保留 `manual_validation_pending: true`、原因、后续检查命令、owner 和 review_after。

Discoverability and promotion invariants:

- `tags` must be a non-empty list of non-empty strings.
- `promotion` must be present.
- currently allowed item `promotion` value is `none`; future promotion states must be added to schema and `knowledge-check` before use.
- `promotion_decision` is a human-readable decision note for promotion boundary or non-promotion rationale; it does not replace `promotion`, owner decision, active review or team-level promotion gates.

Allowed `kind`:

```text
standard
runbook
architecture
decision
project-current
project-archive
validation
audit
patent
debug-record
external-source-note
owner-decision-worksheet
patent-disclosure
codex-session
codex-workflow
personal-note
artifact-ref
authorization
automation-run
```

Allowed `status`:

```text
draft
active
reviewing
archived
superseded
rejected
personal
```

Allowed `scope`:

```text
team-general
project-specific
codex-memory-curation-governance
```

Allowed `visibility`:

```text
team-internal
personal-local
```

Allowed `promotion`:

```text
none
```

Allowed `domain` roots:

```text
root
governance
projects
notes
embedded
patents
codex
```

Domain/path invariants:

- `root` domain path must be `README.md` or `AGENTS.md`.
- `governance` domain path must live under `governance/`, `registry/`, `indexes/`, `tools/`, `templates/`, `docs/goals/` or `artifacts/manifests/`.
- `projects/<project>` domain path must live under `projects/<project>/` or `artifacts/manifests/`.
- `notes` domain path must live under `notes/` or `artifacts/manifests/`.
- `embedded` domain path must live under `domains/embedded/` or `artifacts/manifests/`.
- `patents` domain path must live under `domains/patents/` or `artifacts/manifests/`.
- `codex` domain path must live under `domains/codex/` or `artifacts/manifests/`.
- `personal` 不是当前合法 domain；个人内容必须使用 `domain=notes` 和 `path=notes/personal/**`。
- `project-specific` scope must use `projects/<project>` domain.
- `codex-memory-curation-governance` scope must use `codex` domain.

## project-groups.json

登记产品组、项目组和工具组。项目组只负责聚合，不替代成员 Git 仓库项目的事实边界。

Required fields:

- `id`
- `name`
- `type`
- `entry`
- `member_project_ids`
- `status`

Invariants:

- `id` 必须唯一。
- `entry` 必须是 Knowledge Hub repo-relative path，不能是本机绝对路径。
- `member_project_ids` 必须指向 `registry/projects.json` 中已登记项目。
- `status` 只能使用 `registered` 或 `retired`；当前可路由记录使用 `registered`。

## projects.json

登记 Knowledge Hub 项目入口。项目可以是产品组、Git 仓库项目或 runtime/domain 项目，但长期事实必须落到明确的 `entry`。

Required fields:

- `id`
- `name`
- `type`
- `domain`
- `entry`
- `current`
- `archive`
- `decisions`
- `validation`
- `groups`
- `repo_boundary`
- `status`

Invariants:

- `id` 必须唯一。
- `domain`、`entry`、`current`、`archive`、`decisions`、`validation` 必须是 Hub repo-relative path。
- `groups` 必须指向 `registry/project-groups.json` 中已登记项目组。
- `entry` 必须存在。
- `status` 只能使用 `registered` 或 `retired`；当前可路由记录使用 `registered`。

## repositories.json

登记 Git 仓库到 Hub 项目的映射，是跨路径、跨机器路由的主要真源。

Required fields:

- `repo_id`
- `project_id`
- `remote_key`
- `remote_kind`
- `workspace_ref`
- `groups`
- `aliases`
- `lifecycle`
- `status`

Invariants:

- `repo_id` 必须唯一。
- `remote_key` 必须是规范化逻辑 key，不包含 scheme、host credential、`.git` 后缀或机器路径。
- `project_id` 必须指向 `registry/projects.json`；仅 `lifecycle=external-reference` 允许为空。
- `workspace_ref` 只能使用逻辑引用 `workspace://...`，或保留约定 `~/knowledge-hub`、`~/codex`、`~/.codex`。
- 不得写入 `/home/...`、`/vsdata/...`、`~/work/...`、`~/bin/...` 等机器路径。
- `lifecycle` 允许值：`first-party`、`external-reference`、`workspace-only`、`retired`。
- `status` 只能使用 `registered` 或 `retired`；当前可路由记录使用 `registered`。

## components.json

登记无独立 Git remote、局部源码目录、示例、临时本地聚合或外部参考组件。

Required fields:

- `component_id`
- `parent_project_id`
- `component_uri`
- `kind`
- `relative_path`
- `status`

Invariants:

- `component_uri` 必须以 `component://` 开头。
- `parent_project_id` 必须指向 `registry/projects.json`。
- `relative_path` 是 source-local 逻辑路径，不能是绝对路径、`~/...`、`./...` 或 `../...`。
- `status` 允许值：`registered`、`workspace-only`、`external-reference`、`retired`。

## workspaces.example.json

说明本机 workspace 适配格式，不记录真实路径。真实路径应写入未纳入 Git 的 `local/workspaces.json`。

本机映射通过 `knowledge-workspace-discover.sh --plan --json` 只读发现；`--apply` 只能事务化写入 `local/workspaces.json`。该文件遵循 `schemas/local-workspaces.schema.json`，其中 `path`、`alternate_paths`、`git_ref` 和 `git_head` 都是 machine-local 派生证据，不得复制到 tracked registry、managed Markdown、团队导出或 owner decision。

Allowed references:

- `workspace://<logical-name>`
- `~/knowledge-hub`
- `~/codex`
- `~/.codex`

禁止把 `/home/<user>/...`、`/vsdata/<user>/...`、`~/work/...` 或 `~/bin/...` 写入 Git 管理的 registry。

发现规则：

- 只接受与 `repositories.json.remote_key` 规范化后完全一致的 Git remote，不按目录名或模糊字符串猜测。
- 重复 remote 必须保留确定性选中结果和 `alternate_paths` 诊断；候选副本不自动删除或修改。
- `source_evidence` 仅证明本机路径、根级入口和 HEAD 可读取，不证明构建、测试、设备、发布或 owner gate 已通过。
- 无映射或 fresh clone 时必须安全降级为 `unmapped`/pending，不能改变 tracked 文档内容或生成伪 current。

## project-routes.json

登记跨项目组的预检路由。路由只引用 repo、project group 和 Hub 内入口，不直接匹配本机源码路径。

Required fields:

- `project_id`
- `group_id`
- `type`
- `aliases`
- `repo_refs`
- `workspace_refs`
- `hub_entry`
- `current_path`
- `archive_path`
- `decisions_path`
- `validation_path`
- `default_source_ids`
- `route_key_policy`

Invariants:

- `repo_refs` 必须指向 `registry/repositories.json`。
- `workspace_refs` 只能使用允许的逻辑 workspace 或保留本地约定。
- `domain_refs` 可选；用于非 `projects/<project_id>` 的控制面或运行时域路由，例如 `root`、`governance`、`codex`。未显式填写时，工具按 `projects/<project_id>` 或项目 `domain` 派生。
- `default_source_ids` 只能引用 `registry/sources.json` 中当前 `registered` source；历史 source 账本不得参与默认路由或上下文加权。
- `route_key_policy=control-plane-query-aware` 只允许用于 Knowledge Hub 这类控制面路由：当前 cwd 属于控制面时，query 明确命中其他项目 alias 则路由到目标项目，否则回到控制面自身。
- `cwd_patterns`、`engineering_archive_path` 和 `retired_route_ids` 不属于当前 route contract；归档统一使用 `archive_path`。

## sources.json and retired-sources.jsonl

`registry/sources.json` 是当前 source 主表，只保留仍参与默认 source 恢复、上下文路由或新增入口的 source。

`registry/retired-sources.jsonl` 是历史 source provenance ledger。它保存已经硬切到 Hub canonical 位置、但仍被 registry item、coverage、source-control、owner gate 或历史审计引用的 source 元数据。retired source 不应重新出现在 current source 主表；如需按旧 source id 审计，工具应显式读取 current + retired 的 all-source view。

item `source.source_id` 指向 all-source registry。`indexes/by-source.md`、source coverage 和 source-control 目录可以覆盖 all-source；成熟态 current source 检查只能扫描 `registry/sources.json`。

`registry/retired-process-ledger.jsonl` 是迁移过程账本封存清单，用于保存已经退出 `registry/items.jsonl` 的 dry-run、applied、classification、source-inventory 等过程 item。它不是 item registry、source registry 或 active index，不得作为新增知识入口、owner approval、active promotion 或默认查询路由；只能在人工审计迁移来源和回滚历史时显式读取。

登记 Knowledge Hub 的 source 控制面。终态下 `path` 必须指向 Hub 内 `sources/<source_id>`；旧外部路径只能写入 `origin_path` 作为 provenance，不得作为 active source、check command 或新增归档入口。

Required source fields:

- `id`
- `path`
- `role`
- `authority`
- `status`
- `write_policy`
- `source_strategy`
- `owner`
- `review_after`
- `final_disposition`

Recommended source fields:

- `origin_path`
- `canonical_target`
- `artifact_target`
- `canonical_manifest`
- `decommission_manifest`
- `source_language`
- `expected_normalization`
- `translation_required`
- `retrieved_at`
- `review_status`
- `check`
- `no_check_reason`

Allowed source `role`:

```text
hub-canonical-source
hub-runtime-input
hub-native-source
```

Allowed source `authority`:

```text
knowledge-hub-canonical
runtime-input-provenance
knowledge-hub-ledger
```

Allowed source `status`:

```text
registered
retired
```

`registry/sources.json` 只接受 `registered`；`registry/retired-sources.jsonl` 只接受 `retired`。

Allowed source `write_policy`:

```text
knowledge-hub-only
runtime-read-only-input
hub-native-registry
```

Allowed source `final_disposition`:

```text
hub-canonical
runtime-input-reference-only
hub-native-source
```

Source path invariants:

- `path` must be a Hub-relative `sources/<source_id>` path and must exist.
- `origin_path`, when present, is historical provenance only; it must not be used as a default scan path, search source, check command, active index entry, or new archive destination.
- `check` must validate the Hub control directory or Hub-native ledger; it must not call retired external tools or depend on `~/embedded`, `~/codex/docs/archive`, `~/work`, `~/.codex`, or `/vsdata`.
- Former external sources use `status=retired`, `role=hub-canonical-source`, `authority=knowledge-hub-canonical`, `write_policy=knowledge-hub-only`, and `final_disposition=hub-canonical`.
- Runtime inputs such as Codex history, raw sessions, session index, and memories use `role=hub-runtime-input` and `final_disposition=runtime-input-reference-only`; they are not deleted and are not copied as knowledge正文.

## authorizations.jsonl

登记 AI / Codex 或自动化执行高风险动作前的授权账本。没有匹配授权记录时，AI / Codex 仍可执行 Git 可回滚的 Hub 本仓 L1/L2 维护和本地 commit；高风险动作只能输出 plan、diff、manifest、review package 或 report-only 报告。

Required authorization fields:

- `authorization_id`
- `authorized_by`
- `authorized_at`
- `scope`
- `allowed_actions`
- `expires_at`
- `evidence_refs`
- `rollback_path`
- `validation_commands`
- `status`

Allowed authorization `allowed_actions` values:

```text
owner-decision-landing
active-promotion
memory-write
source-project-write
automation-apply-with-review
external-publish
delete-or-prune
remote-git-write
```

Allowed authorization `status` values:

```text
active
expired
revoked
used
superseded
```

Authorization invariants:

- `authorized_at` and `expires_at` must use ISO date format: `YYYY-MM-DD`.
- `allowed_actions` must be a non-empty list.
- `scope` must be narrow enough to identify project/source/path/action boundary.
- `evidence_refs` must reference an existing local path, command-shaped evidence, or current-session explicit user instruction.
- `rollback_path` and `validation_commands` must be non-empty for write actions.
- AI / Codex may be executor, but must not pretend to be a human reviewer unless the authorization explicitly says it is acting on behalf of that owner.

## content-review-attestation local forms

`artifacts/manifests/*.local.jsonl` 可保存由 `knowledge-review-attest.sh` 机械生成的临时内容复核确认。该表单绑定精确 `item_id`、`expected_before_status`、`target_status`、`content_sha256` 和 `confirmation_token`，但禁止包含 `authorization_id`；它证明真人决定，不授予执行权限，也不进入 tracked manifest。

Required fields and invariants are defined by `schemas/review-attestation.schema.json`。额外运行时约束：

- `attestation_statement` 必须包含 item、原状态、目标状态、完整正文 hash、确认码和有效 reviewer 身份。
- `human-reviewed` 表示真人直接复核，`reviewed_by` 等于 `attested_by`。
- `human-directed-delegation` 只表示真人明确作出非 active 生命周期决定并委托机械落表，`reviewed_by` 必须为 `<attested_by>-via-codex-delegation`。
- `active` promotion 禁止 delegated mode。
- 表单生成不消费 authorization；实际 `promote` / `retire` 必须再独立校验有效授权账本记录。
- apply 后长期账本只保留 attestation id/mode/source ref、正文 hash、确认码和确认文本 hash；原始确认文本继续留在未跟踪本地表单，不复制聊天正文。
- 生命周期工具只接受 `content-review-attestation`；任何包含 `authorization_id` 的复核表单均拒绝，执行授权必须单独来自 `registry/authorizations.jsonl`。

## lifecycle-events.jsonl

登记 `capture`、`promote` 和 `retire` 的可审计生命周期事件。该账本记录实际 apply 结果；dry-run 不得写入。`capture` 可在无高风险授权时创建 `draft`、`reviewing` 或 `personal`，但不得直接创建 `active`。`promote` 和 `retire` 必须分别引用匹配、未过期且处于 `active` 状态的 execution authorization，以及绑定当前正文的 content review attestation，并提供预期正文 hash 和事务 journal。

Required lifecycle event fields:

- `event_id`
- `event_type`
- `item_id`
- `before_status`
- `after_status`
- `authorization_id`
- `executed_by`
- `executed_at`
- `evidence_refs`

Lifecycle invariants:

- `capture` 的 `authorization_id` 可以为空；其他事件不得为空。
- `promote` 仅支持 `reviewing -> active`，且 authorization 必须允许 `active-promotion`。
- `retire` 只支持 schema 明确允许的终态转换，不移动正文、不删除历史证据。
- registry、正文 frontmatter、核心索引、authorization 消费状态和 lifecycle event 必须在同一 recoverable transaction 内更新。
- `.tmp/transactions/<transaction_id>/journal.json` 是本地恢复证据，不作为长期正文或发布制品。

## automation-runs.jsonl

登记跨项目、跨会话 AI 自动化运行。它是 Hub 主库串联 project、session、source、authorization 和输出证据的最小账本。

Required automation run fields:

- `run_id`
- `automation_id`
- `project_id`
- `trigger`
- `mode`
- `status`
- `started_at`
- `input_refs`
- `output_refs`
- `validation_refs`

Recommended automation run fields:

- `session_id`
- `workstream_id`
- `source_ids`
- `authorization_id`
- `rollback_ref`
- `notes_zh`

Allowed automation `mode` values:

```text
read-only
report-only
plan-only
local-commit
apply-with-review
forbidden
```

Automation run invariants:

- `apply-with-review` requires an `authorization_id` registered in `registry/authorizations.jsonl`.
- `remote-git-write` 类动作必须使用 authorization `allowed_actions=["remote-git-write"]` 或更窄授权，不能用本地 commit 代替。
- `read-only`、`report-only`、`plan-only` 和 `local-commit` 不得写 memory、源项目、team active index、owner gate closure 或远端 Git 状态。
- 每次自动化运行必须能从 `input_refs` 找到来源，从 `output_refs` 找到产物，从 `validation_refs` 找到验证或待验证原因。

Source/index invariants:

- source `id` must be unique.
- `indexes/by-source.md` main source table must include every source `id`.
- `indexes/by-source.md` main source table must not include unregistered source ids.
- source `owner` is the maintenance owner for registry/source governance; it is not an owner decision or owner sign-off.
- source `owner` must be registered in `registry/owners.json`.
- source `review_after` must use ISO date format: `YYYY-MM-DD`.
- stale source `review_after` is a warning/status surface, not a blocking error; `knowledge-check --json` should expose the source id in `source_check_health.stale_review_after_ids`, and `knowledge-status --json` should expose `sources.stale_review_after_count` and `sources.stale_review_after_sample`.
- source `source_strategy` must explain how the source enters Knowledge Hub control-plane governance without implying copied正文 or active promotion.
- source `final_disposition` must use the allowed enum and describe control-plane disposition, not owner approval.
- source `check`, when present, records a read-only validation command or inventory command.
- if source `check` is empty, source registry must record `no_check_reason`; the latest source coverage manifest should also record or reference the reason.
- source coverage rows should include `source_id`, `status`, `classification`, `decision`, `risk`, `owner` and `checked_at`.
- source coverage rows should include `source_identity` or `evidence_refs` when a directory source cannot be represented by one stable file hash.
- tools that select the latest source coverage manifest should expose `source_coverage_selection` with `pattern`, `strategy`, `candidate_count`, `candidates`, `selected` and `reason_zh`.
- `knowledge-check --json` should expose `source_coverage_health` with registered、row、unique、missing、stale、duplicate、missing-field and invalid-date summaries so pass results are still auditable.
- core item indexes `indexes/by-owner.md`, `indexes/by-review-date.md` and canonical status buckets in `indexes/by-status.md` must not duplicate registry item ids.

## owners.json

登记 registry item 可使用的 owner id。每个 `registry/items.jsonl` 条目的 `owner` 必须能在这里找到，避免责任人拼写漂移或临时 owner 长期残留。

Required owner fields:

- `id`

Recommended owner fields:

- `display_name`
- `default_review_cycle_days`

## owner-routing.json

登记 owner decision worksheet 中抽象签收角色的人工分派路由。它只解决“应该找谁分派/升级”，不生成 owner decision，不替代 `reviewed_by`，不关闭 owner gate。

Required route fields:

- `decision_owner_role`
- `source_id`
- `routing_status`
- `routing_owner`
- `required_real_owner_zh`
- `escalation_zh`
- `notes_zh`

Recommended route fields:

- `candidate_registry_owners`
- `must_not`

Allowed route `routing_status`:

```text
mapped-to-registry-owner
needs-human-assignment
unmapped
retired
```

Owner routing invariants:

- `decision_owner_role` must match an owner role used by owner decision worksheets, such as `owner_required` or `owner_candidate`.
- `source_id` must be registered in `registry/sources.json`.
- `routing_owner` is a registered maintenance owner responsible for分派和升级，不是最终 decision owner。
- `routing_owner` and `candidate_registry_owners[]` must be registered in `registry/owners.json`.
- Every open owner decision worksheet role should have one route. Missing routes are blocking governance drift, not owner approval.
- `owner-routing.json` must keep `notes_zh` and `required_real_owner_zh` readable in Chinese.
- A route must not be used as `reviewed_by` unless the same human owner actually fills and signs the owner decision form.

## projects.json

登记 registry item 可使用的 project id。每个 `registry/items.jsonl` 条目若使用 `domain=projects/<project>`，则 `<project>` 必须能在这里找到，避免项目 id 拼写漂移或临时项目目录长期残留。

Required project fields:

- `id`

Recommended project fields:

- `name`
- `domain`
- `entry`
- `current`
- `archive`
- `status`

Project registry must be Hub-first: `entry`, `current` and `archive` point to local Knowledge Hub paths. Retired external locations are not current project facts; when needed, recover them from Git history instead of adding current registry fields.

## topics.json

登记主题导航入口及允许的 item kind。每个 topic 必须有唯一 `id`、存在的相对本地 `domain` 路径和非空 `allowed_kinds` 列表；`allowed_kinds` 只能使用 `items.jsonl` 的 allowed `kind`。

Required topic fields:

- `id`
- `domain`
- `allowed_kinds`

## artifacts/manifests JSONL lightweight contract

`artifacts/manifests/*.jsonl` 是治理证据、source coverage、artifact-ref、owner worksheet 和回归记录的结构化制品。它不是 `registry/items.jsonl`，不得强行套用完整 item schema。

新增或 2026-06-21 及之后的 `knowledge-hub-*.jsonl` governance manifest 至少保持：

- `id`
- `status`
- 日期证据：`checked_at`、`created_at`、`updated_at`、`review_after` 或文件名中的 `YYYYMMDD`
- 中文可读说明：`summary_zh` 或 `notes_zh`
- 证据字段：`evidence`、`evidence_refs`、`validation_refs`、`verification_commands` 或 `source_refs`
- 边界字段：`boundaries`、`must_not`、`non_goals`、`rollback_policy` 或 `risk`

Manifest profile invariants:

- 2026-06-21 之前的历史 manifest 不反向强制改写。
- artifact-ref、owner worksheet、owner form、source coverage 和 mature closeout 清单按各自类型字段保持兼容，不为美化字段而改变语义。copy-first 只作为历史迁移 provenance，不再作为成熟态新增或默认工具入口。
- source coverage row 继续遵守 source coverage 字段要求。
- owner worksheet/form 结构门禁不得生成 owner decision，不得关闭 owner gate。
- 机器清单可以保留英文 key，但 `summary_zh`、`notes_zh`、`decision`、`risk` 或相邻 Markdown 必须给中文维护者足够上下文。

Artifact vault invariants:

- vault 清单行默认 `vault_presence=required`，对应 `artifacts/vault/<collection>/<source_path>` 必须存在且 size/SHA256 完全一致。
- `vault_presence=external-reference-only` 只允许文件不在本地 vault 时使用，必须在清单或相邻 Markdown 写明原因；若同路径文件实际存在则视为边界漂移。
- vault 不允许清单外额外文件；raw log、core、SDK、release binary、源码包和 secret 不得进入。

## Safety invariants

- `active` and `reviewing` items must have `owner` and `review_after`.
- item `owner` must be registered in `registry/owners.json`.
- item `domain=projects/<project>` must use a project id registered in `registry/projects.json`.
- topic `domain` must be a relative existing local path, and topic `allowed_kinds` must use item kind enums.
- `superseded` items must have `superseded_by`.
- `artifact-ref` items must have `uri`, `size`, and `sha256`.
- `project-specific` items must not live under `domains/embedded/standards`.
- `personal-local` items must not use `active` status and must not be referenced by active team indexes.
- Human-readable title, summary, conclusion, risk and review notes should be Chinese by default.
- AI generated or AI transformed content must not become `active` without human review evidence.
- AI generated `active` items must provide `human_reviewed_by`, `human_reviewed_at`, and `review_basis`.
- AI generated registry items created on or after 2026-06-21 must provide `ai_role`, `ai_model_or_tool`, and `ai_generated_at`, even when they remain `reviewing`.
- External-source derived items must record source metadata, read status and promotion decision before promotion.
