# PCR02 Owner Resolution Playbook - 2026-06-18

## 摘要

本 playbook 定义 PCR02 docs governance 剩余 7 个 owner-gated 条目在 owner 决策返回之后的安全落地规则。它不是 owner 决策结果，不关闭 blocker，不把任何条目提升为 active/current。

核心原则：

- `source-identity-match` 只证明源文件字节身份一致，不证明语义有效。
- owner 决策必须唯一、可追溯、带证据、带 review cycle。
- `registry/items.jsonl` 的 canonical `status` 继续只使用粗粒度：`active`、`reviewing`、`archived`。
- owner gate 语义写入 `review_status`、migration row 和 status overlay，不新增伪 canonical status。
- 历史 migration 只追加，不回写覆盖。

## 受控状态词

### `review_status`

| 值 | 含义 |
| --- | --- |
| `pending-owner-review` | 需要 owner 复核。 |
| `needs-owner-resolution` | 需要 owner 决策才能继续。 |
| `owner-intake-ready` | 已具备中文签收包。 |
| `source-identity-match` | 当前源文件 hash/size 与 worksheet expected 一致。 |
| `owner-decision-recorded` | owner 决策已记录，但尚未完成全部落地验证。 |
| `owner-gate-satisfied` | owner gate 已满足，后续仍需按目标类型验证。 |
| `owner-approved-reference-only` | owner 确认仅保留引用。 |
| `owner-approved-archive-only` | owner 确认只归档。 |
| `owner-approved-project-local-rule-pending-verification` | owner 批准项目本地规则，但仍待验证和落点更新。 |
| `owner-approved-project-current-pending-verification` | owner 批准项目 current 候选，但仍待验证。 |
| `owner-approved-project-decision-pending-verification` | owner 批准项目 decision 候选，但仍待验证。 |
| `owner-approved-validation-candidate-pending-verification` | owner 批准 validation candidate，但仍待补证。 |
| `owner-approved-split-pending-rewrite` | owner 批准拆分，但仍待重写和复核。 |
| `owner-rejected` | owner 拒绝迁移或抽取。 |

### `status`

| 值 | 用法 |
| --- | --- |
| `reviewing` | registry canonical status；控制面、gate-tracking、待复核目标默认使用。 |
| `archived` | registry canonical status；仅明确 archive-only 的目标条目使用。 |
| `active` | registry canonical status；只有 owner、证据、review cycle、验证全部满足后使用。 |

下列值只能作为 row-level 或 overlay status，不写入 registry canonical `status`：

- `blocked-pending-owner-decision`
- `reference-only`
- `archive-only`
- `project-current-pending-verification`
- `project-decision-pending-verification`
- `project-local-rule-pending-verification`
- `team-candidate-only`
- `teamized-report-only-disabled`
- `personal-local`
- `validation-candidate-pending-verification`
- `completed`
- `superseded`
- `rejected`

### `promotion_decision`

允许值：

- `none`
- `reference-only`
- `archive-only`
- `project-local-rule`
- `project-current`
- `project-decision`
- `candidate-only`
- `validation-candidate`
- `no-migration`

## 状态迁移矩阵

| Source path | Owner decision | Allowed target action | Forbidden transition |
| --- | --- | --- | --- |
| `AGENTS.md` | `project-local-rule` | PCR02 project-local rule；`review_status=owner-approved-project-local-rule-pending-verification`；`promotion_decision=project-local-rule` | 根 `AGENTS.md`、全局 Codex 规则、team standard、`domains/embedded/standards` |
| `AGENTS.md` | `reference-only` | 仅保留引用；`review_status=owner-approved-reference-only`；`promotion_decision=reference-only` | active/current/team/global |
| `AGENTS.md` | `no-migration` | 关闭迁移路径；`review_status=owner-rejected`；`promotion_decision=no-migration` | 任何正文迁移 |
| `standards/diag-command-metadata-standard.md` | `pcr02-project-decision-after-owner-gate` | PCR02 decision 候选；`owner-approved-project-decision-pending-verification` | 无 gate evidence 或 owner exception 时直接 current；team standard |
| `standards/diag-command-metadata-standard.md` | `pcr02-project-current-after-owner-gate` | PCR02 current 候选；`owner-approved-project-current-pending-verification` | 进入 `domains/embedded/standards`；泛化 PCR02 命令名/路径/生命周期 |
| `standards/diag-command-metadata-standard.md` | `reference-only` / `no-migration` | 引用或不迁移 | active/current |
| `runbooks/asan-debug-guide.md` | `split-approved` | 仅批准拆分；team 部分 candidate-only，PCR02 细节 project-local；`owner-approved-split-pending-rewrite` | 整篇复制到 team active；PCR02 `DEBUG=256`、`prog_pcr02`、`/customer/*` 变跨项目默认 |
| `runbooks/asan-debug-guide.md` | `active-project-local` | PCR02 project-local runbook 候选 | team active；embedded standards |
| `runbooks/asan-debug-guide.md` | `team-candidate-only` | team candidate-only，不 active | 直接 active |
| `runbooks/asan-debug-guide.md` | `reference-only` | 仅保留引用；不复制正文 | project current；team active |
| `runbooks/asan-debug-guide.md` | `rejected` | 关闭迁移路径；记录 owner 拒绝原因 | 任何正文迁移 |
| `runbooks/memory-auto-curation-guide.md` | `personal-local` | 仅 personal/local；`promotion_decision=no-migration` | team active index；自动化启用 |
| `runbooks/memory-auto-curation-guide.md` | `teamized-report-only` | disabled report-only governance candidate；`teamized-report-only-disabled` | 写 memory；启用自动 send/commit/publish/delete/promote |
| `runbooks/memory-auto-curation-guide.md` | `rejected` | 关闭迁移路径；记录 owner 拒绝原因 | team active；自动化启用 |
| `runbooks/memory-auto-curation-guide.md` | `no-migration` | 不迁移正文；保留控制面记录 | 写 memory；写 team active index |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `completed` / `superseded` | owner closeout；可 archive-only 或 closeout artifact | 把计划命令当验证结果；保持 active |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `active-if-owner-confirms-current-baseline` | current-baseline pending verification；必须有 branch/commit/tag 和实际验证结果 | 未确认当前基线就 active/current |
| `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md` | `archive-only` | 明确只归档；不保留 active 计划语义 | current-baseline；project current |
| `reports/2026-05-29-motor-mcu-debug-record.md` | `archive-only` | archive-only | 推断变 verified root cause；生产策略 |
| `reports/2026-05-29-motor-mcu-debug-record.md` | `validation-report-candidate` | validation candidate pending verification | 直接 current；隐藏 open items |
| `reports/2026-06-16-dvr-record-replay-session-archive.md` | `archive-only` | 仅 archive-only；抽取 decision/validation evidence 需新 owner review | 整篇 current；写 memory candidates；dirty-state/handoff 当项目事实 |

## 不可自动 active 的状态

即使 `source-identity-match`，以下状态也不能自动进入 active/current：

检索提示：source identity match 不能自动 active，source identity match 不能自动 current，必须等待 owner decision、evidence refs、review cycle 和 knowledge-check。

- `reference-only`
- `no-migration`
- `rejected`
- `personal-local`
- `teamized-report-only`
- `split-approved`
- `team-candidate-only`
- `completed`
- `superseded`
- `archive-only`
- `validation-report-candidate`

以下状态可通向 current/decision，但仍必须再次验证：

- `project-local-rule`
- `pcr02-project-current-after-owner-gate`
- `pcr02-project-decision-after-owner-gate`
- `active-project-local`
- `active-if-owner-confirms-current-baseline`

## Registry 和 Index 更新规则

每次 owner 决策正式落地，至少同步更新：

- `registry/items.jsonl`
- `registry/migrations.jsonl`
- `indexes/by-status.md`
- `indexes/by-project.md`

可选更新：

- `indexes/by-topic.md`
- `indexes/by-source.md`
- `indexes/by-review-date.md`
- `indexes/by-owner.md`

规则：

1. `registry/items.jsonl` 更新 gate-tracking item 的 `review_status`、`updated_at`、`validation_refs`，必要时更新 `review_after`。
2. 新建目标条目时，目标 item 只能使用 canonical `status`。
3. owner gate 语义不要塞进目标正文条目的 `status`。
4. `registry/migrations.jsonl` 只追加，不覆盖历史行。
5. `indexes/by-status.md` 保留 canonical bucket，额外用 overlay bullet 说明 owner gate 结果。
6. `indexes/by-project.md` 必须保留 closeout / resolution artifact 引用，即使结果是 `no-migration`。

机器校验：

- 受控枚举、source_path 到 owner_decision 的映射、额外必填字段和禁止组合由 `artifacts/manifests/pcr02-owner-resolution-schema-20260618.md` 固化。
- 若本 playbook 的 prose 描述与 schema/worksheet 不一致，先以 worksheet 和 schema 为 owner 决策落地依据，再追加修正 playbook。
- schema 仍是 `reviewing` 控制面制品，不代表 owner gate 已满足，也不允许自动 active/current。

## 验证矩阵

每次 owner 决策落地后至少运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 owner"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<本次终态词>"
rtk jq -c 'select(.id|test("pcr02|memory-auto-curation")) | {id,status,review_status,path,updated_at,review_after}' registry/items.jsonl
rtk jq -c 'select((.from|tostring|test("pcr02|memory-auto-curation")) or (.to|tostring|test("pcr02|memory-auto-curation"))) | {from,to,mode,status,checked_at}' registry/migrations.jsonl
rtk git diff -- registry/items.jsonl registry/migrations.jsonl indexes/by-status.md indexes/by-project.md
```

按条目补充源侧 gate：

- `AGENTS.md`：SHA256 / size、project-only scope、owner sign-off，目标不得是根 `AGENTS.md` 或 team standard。
- `diag-command-metadata-standard.md`：SHA256 / size、5 类 diag gate 运行态证据或 documented owner exception。
- `asan-debug-guide.md`：split approval、branch / SDK、build artifact、deploy path 适用性。
- `memory-auto-curation-guide.md`：`enabled=false`、report-only、no-memory-write、no-team-active-index-write、secret scan、rollback。
- DVR plan：唯一终态、branch / commit / tag、proto / build / refcount / grep 实际结果。
- Motor MCU debug record：firmware version、保护参数、波形 / 协议日志、复测、unresolved acknowledgement。
- DVR session archive：archive metadata approval、`contains_memory_candidates=true`、`not_active_source=true`、`extracts_require_owner_review=true`。

## 回滚规则

- 未提交落地：只回退本次控制面文件和新建目标条目，不碰源项目 docs。
- 已提交落地：优先追加 corrective migration row，并把受影响 item 的 `status` / `review_status` 改回上一稳定值。
- 错误创建目标条目：先取消目标 item 和 indexes 引用，再追加 corrective migration row 说明撤销原因。
- 禁止用清理源 worktree、删除源文档、写 memory 或回写历史 migration 来“修复”owner gate 错误。

## 禁止事项

- 不写 `~/.codex/memories`。
- 不修改源项目 docs。
- 不启用 automation。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不把 `AGENTS.md`、diag metadata、session archive、memory candidates 提升成 team active fact。
- 不把计划命令当验证结果。
- 不把 source identity match 当语义确认。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`owner-resolution-playbook-ready`
- promotion：`none`
- review_after：`2026-09-17`
