# Knowledge Hub source registry final-state fields 2026-06-20

## 结论

本轮把 `registry/sources.json` 从薄登记推进到终态字段登记：每个 registered source 现在都有维护责任人、复核日期、迁移策略和控制面终态处置；没有可执行 `check` 的 source 必须写明 `no_check_reason`。

这不是 owner decision，也不表示 owner 已签收。`owner` 字段只表示 source registry 的维护责任人；PCR02 剩余 owner-gated 文档仍然必须通过 owner decision JSONL 人工签收。

## Issue Map

| ID | Finding | Severity | Evidence | Action | Status |
|---|---|---|---|---|---|
| SRFS-001 | `registry/sources.json` 缺少终态目标要求的 `owner`、`review_after`、`migration_strategy` 和 `final_disposition` | P1 | `docs/goals/knowledge-hub-final-state.md` Level 3 | 补齐 13 个 registered source 的维护字段 | applied |
| SRFS-002 | 空 `check` 与漏填 `no_check_reason` 不可区分 | P1 | `registry/sources.json`、`registry/schema.md` | `knowledge-check` 要求空 `check` 必须有 `no_check_reason` | applied |
| SRFS-003 | final gate Level 3 只证明 coverage 覆盖，不直接报告 registry 终态字段缺口 | P1 | `tools/knowledge-final-gate.sh` | 增加 `missing_final_state_fields` | applied |
| SRFS-004 | 新增 source 向导仍输出旧薄结构 | P2 | `tools/knowledge-new.sh --source` | 输出新字段草稿并补回归断言 | applied |

## 字段语义

- `migration_strategy`：描述 source 如何进入 Knowledge Hub 控制面，不等于复制正文或提升 active。
- `owner`：source registry 维护责任人，不等于 owner decision 签收人。
- `review_after`：维护复核日期，格式为 `YYYY-MM-DD`。
- `final_disposition`：控制面终态处置枚举，不等于语义批准。
- `no_check_reason`：当 `check` 为空时必填，解释为什么没有 source-level 可执行检查。

## 边界

- 不修改任何 PCR02 源项目文件。
- 不复制 source 正文、脚本、日志、二进制或附件。
- 不生成 owner decision，不关闭 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化写操作，不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `subagent: source-registry-final-state-gap` | 0 | 只读确认 source registry 终态字段缺口是非 owner schema 缺口 | 本会话子代理回执 | Subagent | `knowledge-hub-source-registry-final-state-fields-20260620` |
| `subagent: status-final-gate-contract-gap` | 0 | 只读确认不应把 `final_state_audit` 透传到 status，终态审计保留在 final gate | 本会话子代理回执 | Subagent | `knowledge-hub-source-registry-final-state-fields-20260620` |
| `rtk bash tools/knowledge-check.sh --sources-only --json` | 0 | source registry 字段门禁通过，0 errors / 0 warnings | `tools/knowledge-check.sh` | Source registry | `knowledge-hub-source-registry-final-state-fields-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓知识库检查通过，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-source-registry-final-state-fields-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 33 个回归场景通过，包含 source manual guide 和 final gate Level 3 字段断言 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-source-registry-final-state-fields-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 | 预期停在 `needs-owner-review`；Level 3 为 `complete`，`missing_final_state_fields=[]`，唯一 gap 为 `owner-gates-open` | `tools/knowledge-final-gate.sh` | Final gate | `knowledge-hub-source-registry-final-state-fields-20260620` |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`source-registry-final-state-fields-applied`
- 下一步：如果用户提供 owner decision JSONL，再按 `tools/knowledge-owner-gates.sh --validate-forms '<owner-decisions.jsonl>' --landing-plan --json` 生成 no-write landing plan。
