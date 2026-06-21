# PCR02 ASAN Owner Ready Package - 2026-06-20

## 结论

本包把 `pcr02-owner-decision-worksheet-003` 单独收口成 owner 可签收材料。它只服务 PCR02 docs `runbooks/asan-debug-guide.md` 这一条 owner gate：

- 不复制源 runbook 正文。
- 不修改源项目 docs。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不创建 PCR02 current runbook。
- 不创建团队级 ASAN runbook。
- 不提升到 `domains/embedded/standards/`。
- 不把 PCR02 构建、部署、路径或 `libasan` 布局当作跨项目默认。
- 不启用自动化，不写 `~/.codex/memories`。

当前状态仍为 `owner-fill-required`，最终门禁仍预期是 `needs-owner-review`，直到 owner 明确填写并验证通过。

## Source Identity

| 字段 | 值 |
| --- | --- |
| source_id | `pcr02-project-docs` |
| source_path | `runbooks/asan-debug-guide.md` |
| worksheet_id | `pcr02-owner-decision-worksheet-003` |
| owner | `team-core` |
| observed_sha256 | `d65cf6796eac2c306b6bd0fa101450a1307d5c49ba7b7640e6a329d4263d8e88` |
| observed_size | `4736` |
| identity_status | `match` |

`observed_sha256` 和 `observed_size` 只是只读提示，不能自动替代 owner 在签收 JSONL 中显式填写的 `source_sha256` 和 `source_size`。

## Owner 只需回答的问题

请 owner 对以下问题给出唯一结论：

> 是否批准拆分边界，把 `DEBUG=256`、`prog_pcr02`、`/customer/*`、`libasan` 等 PCR02 细节仅保留项目内；团队层是否只保留 candidate-only 并另行重写审查？

允许的 `owner_decision` 只有：

| owner_decision | 含义 | 允许 target_decision |
| --- | --- | --- |
| `split-approved` | 只批准拆分边界；PCR02-local 和 team-candidate 后续仍需分别落地验证。 | `project-local-plus-team-candidate-boundary` |
| `active-project-local` | 只允许创建 PCR02 project-local runbook 候选。 | `domains/projects/pcr02/current/runbooks/asan-debug-guide.md` |
| `team-candidate-only` | 只允许未来另行重写团队候选，不创建 PCR02 current runbook。 | `domains/embedded/runbooks/asan-debug-guide.md candidate-only` |
| `reference-only` | 只保留引用和 source identity，不复制正文。 | `reference-only` |
| `rejected` | owner 拒绝迁移或抽取。 | `no-migration` |

## 必填字段

owner decision JSONL 必须填写：

- `owner_decision`
- `target_decision`
- `split_approval`
- `reviewed_by`
- `reviewed_at`
- `review_after`
- `source_status`
- `source_sha256`
- `source_size`
- `applicable_branch_or_sdk_version`
- `target_binary`
- `team_level_status`
- `evidence_refs`
- `open_items`
- `status_reason`

## 拆分边界

### PCR02-local only

以下内容只能保留在 PCR02 项目域，不能进入团队 active runbook：

- `DEBUG=256` / `DEBUG=1` 与项目构建逻辑。
- `TARGET_REL_FOLDER := debug`。
- `make -j8 DEBUG=256`、`make install` 等项目 make 命令。
- `prog_pcr02`、`release/bin/prog_pcr02`、`/customer/bin`、`/customer/lib`。
- `libs/3rdparty/libasan`、`libasan.so.6` 和手动部署 `libasan` 的项目布局。
- 固件容量、strip 行为、动态链接器路径和项目构建产物关系。

### Team candidate only

以下内容可作为未来团队级 ASAN runbook 的候选，但必须重写为通用方法并单独 review：

- `-fsanitize=address`、`-fno-omit-frame-pointer` 等 ASAN 编译标志。
- 使用 `readelf -d <target-binary>` 检查 `libasan` 依赖。
- 首发 ASAN 错误优先、BuildID 匹配、栈帧提取、最小调用链和最小修复复现闭环。
- 嵌入式 `ASAN_OPTIONS` 取舍、日志落盘、符号化策略。

## Hard Gate

以下任一条件不满足时，不能越过 owner gate：

- `split_approval` 未明确。
- `applicable_branch_or_sdk_version` 未明确。
- `target_binary` 未明确。
- `team_level_status` 未说明是否 candidate-only、rejected 或 not-needed。
- 整篇源 runbook 被复制到团队 active 路径。
- PCR02 `DEBUG=256`、`prog_pcr02`、`/customer/*` 或 `libs/3rdparty/libasan` 被写成跨项目默认。
- 目标指向 `domains/embedded/standards/`。

## Copyable Owner Decision Skeleton

以下 JSON 只能由 owner 填写空字段后作为单行 JSONL 使用。不要把它当作已签收结果。

```json
{"worksheet_id":"pcr02-owner-decision-worksheet-003","source_id":"pcr02-project-docs","source_path":"runbooks/asan-debug-guide.md","worksheet":"artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl","owner":"team-core","status":"open","worksheet_status":"owner-fill-required","owner_question_zh":"是否批准拆分边界，把 DEBUG=256、prog_pcr02、/customer/*、libasan 等 PCR02 细节仅保留项目内；团队层是否只保留 candidate-only 并另行重写审查？","default_state":"split-required / blocked-pending-owner-review","allowed_owner_decisions":["split-approved","active-project-local","reference-only","rejected","team-candidate-only"],"must_not":["do not promote to domains/embedded/standards","do not copy whole PCR02 runbook to team-level","do not modify source project runbook for migration convenience","do not declare active before owner confirmation"],"owner_decision":"","target_decision":"","split_approval":"","reviewed_by":"","reviewed_at":"","review_after":"2026-09-17","source_status":"","source_sha256":"","source_size":"","applicable_branch_or_sdk_version":"","target_binary":"","team_level_status":"","evidence_refs":[],"open_items":[],"status_reason":""}
```

## 验证和落地顺序

1. Owner 填写 JSONL 后，先只读校验：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
```

2. 校验通过后，生成只读落地计划：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

3. 只按 landing plan 手工更新 Knowledge Hub，不修改源项目 docs。

4. 手工落地后至少运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-003 --checklist --forms` | 0 | 单条 checklist 和 form 可生成；source identity 为 match；owner fields 保持空白。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-asan-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --worksheet-id pcr02-owner-decision-worksheet-003 --forms --json` | 0 | JSON form 聚焦 worksheet-003；`owner_decision` 为空，allowed decisions 与 worksheet 一致。 | `tools/knowledge-owner-gates.sh` | Owner gate | `pcr02-asan-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-asan-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --explain pcr02-asan-owner-ready-package-20260620` | 0 | registry 条目存在，核心索引引用均为 ok。 | `tools/knowledge-check.sh` | Knowledge Hub | `pcr02-asan-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json` | 0 | 20 个 governance regression 场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `pcr02-asan-owner-ready-package-20260620` |
| `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；`knowledge_check` 和 `knowledge_regression` 通过，唯一 blocker 是 7 个 owner gates open。 | `tools/knowledge-final-gate.sh` | Final gate | `pcr02-asan-owner-ready-package-20260620` |

## 非目标

- 不把源 runbook 迁移到 `domains/projects/pcr02/current/runbooks/`。
- 不创建 `domains/embedded/runbooks/asan-debug-guide.md`。
- 不把源 runbook 提升为团队标准。
- 不变更 worksheet 状态。
- 不修改 `registry/items.jsonl` 中既有 PCR02 owner gate 的状态。
