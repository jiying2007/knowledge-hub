# Knowledge Hub owner/status gate hardening 2026-06-19

## 结论

本轮修复两个终态门禁风险：

- owner gate 的 resolved 判定从“状态词 + 任意 owner 字段”收紧为“状态词 + worksheet required_owner_fields 与通用 review 字段全部非空”。
- `by-status` 覆盖检查从“整文件出现过 item id”收紧为“item 必须出现在与 registry `status` 一致的 canonical bucket”。

同时将 `indexes/by-status.md` 拆成短 canonical 行，并同步只读计划器和人工新增向导，避免继续制造超长 status 行。

## 问题地图

| ID | 发现 | 风险 | 修复 |
|---|---|---|---|
| OG-RESOLVED-WIDE | `is_resolved()` 只要任意 owner 字段存在且状态含 resolved/approved/closed 就可能关闭 gate | 后续部分填表可能提前解除 owner gate | 要求 `required_owner_fields` 与 `target_decision`、`reviewed_by`、`reviewed_at`、`review_after`、`source_status`、`evidence_refs`、`status_reason` 全部非空 |
| STATUS-COVERAGE-WIDE | `by-status` 覆盖检查使用整文件反引号引用 | item 只写在说明行也可能被误判为已覆盖 | `by-status` 覆盖只读取 canonical bucket |
| STATUS-WRONG-BUCKET | 未校验 registry `status` 与 canonical bucket 一致 | active/reviewing/archived 放错 bucket 可能漏检 | 对每个 item 检查其 id 必须出现在对应 status bucket |
| STATUS-LONG-LINE | `indexes/by-status.md` 存在历史超长 `reviewing` 单行 | 人工维护、合并冲突和复核成本高 | 拆为一 item 一短行 |
| GUIDE-DRIFT | `knowledge-index-plan.sh` 和 `knowledge-new.sh` 仍鼓励超长行 | 新增条目会继续扩大维护瓶颈 | 输出/提示短 canonical 行 |

## 变更范围

- `tools/knowledge-owner-gates.sh`
- `tools/knowledge-check.sh`
- `tools/knowledge-index-plan.sh`
- `tools/knowledge-new.sh`
- `indexes/by-status.md`
- registry、migration 和 topic/owner/review/status 索引登记

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认 status bucket 一致性和 owner gate hardening 未误伤当前数据 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-owner-status-gate-hardening-20260619` |
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --json` | 0 | 通过；PCR02 owner gate 仍为 7 open、0 resolved、0 active_exposure | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-owner-status-gate-hardening-20260619` |
| `rtk bash tools/knowledge-index-plan.sh --section status` | 0 | 通过；只读计划器输出短 canonical status 行，不再输出超长 bucket 行 | `tools/knowledge-index-plan.sh` | Tool | `knowledge-hub-owner-status-gate-hardening-20260619` |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 | 预期负结果；仍为 `needs-owner-review`，7 个 PCR02 owner gate 未闭环，终态门禁不得放行 | `tools/knowledge-status.sh` | Tool | `knowledge-hub-owner-status-gate-hardening-20260619` |

## 边界

- 不修改 PCR02 源项目 docs。
- 不关闭任何 PCR02 owner gate。
- 不生成 owner decision。
- 不提升 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化，不写 memory。
