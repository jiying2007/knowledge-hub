# Knowledge Hub final gate 需求章节映射加固 2026-06-23

## 摘要

本次加固将 `knowledge-final-gate.sh --json` 的终态证据从“命令和路径可追溯”推进到“命令、证据块和终态章节可直接映射”。

新增或强化的可读字段：

- 顶层 `summary`：只读派生扫读视图，汇总 `final_status`、Level 1/2/3、proof、maintenance 和 linking 状态。
- `evidence_index[].requirement_refs` / `evidence_index[].section_refs`：逐条命令证据映射到 `docs/goals/knowledge-hub-final-state.md` 的终态章节。
- `maintenance_entry_audit.requirement_refs` / `section_refs` 及每个 entry 的同名字段：证明 8 类长期维护入口和 1 个离线维护包分别对应哪些终态要求。
- `linking_audit.summary`、`linking_audit.requirement_refs` / `section_refs`：把跨会话和跨项目恢复链路的关键字段压缩成扫读摘要。
- `proof_artifacts.coverage_sections`、`requirement_refs` / `section_refs`：明确终态 proof 主制品登记、配对、migration 和核心索引恢复覆盖的章节范围。

这些字段只用于可读性、审计和回归锁定，不参与 `final_status` 判定，不生成或替代 owner decision。

## 变更范围

- `tools/knowledge-final-gate.sh`
- `tools/knowledge-regression.sh`
- `README.md`
- `tools/README.md`
- `artifacts/manifests/knowledge-hub-final-gate-requirement-map-hardening-20260623.md`
- `artifacts/manifests/knowledge-hub-final-gate-requirement-map-hardening-20260623.jsonl`
- `registry/items.jsonl`
- `registry/migrations.jsonl`
- `indexes/by-owner.md`
- `indexes/by-review-date.md`
- `indexes/by-status.md`
- `indexes/by-topic.md`
- `indexes/by-decision.md`

## 边界

- 不关闭 7 个 PCR02 owner gates。
- 不生成 owner decision。
- 不修改 PCR02 源项目 docs。
- 不复制 owner-gated source 正文。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化；所有新增证据仍为只读/report-only。
- 不写 `~/.codex/memories`。

## 验证计划

```bash
rtk bash -n tools/knowledge-final-gate.sh
rtk bash -n tools/knowledge-regression.sh
rtk git diff --check
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-23
rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-23
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-23
```

预期终态：

- `knowledge-check`: pass。
- `knowledge-regression`: pass。
- `knowledge-final-gate`: 仍返回 `needs-owner-review`，且唯一真实阻塞仍为 `owner-gates-open`。
- `final gate summary`、`evidence_index`、`maintenance_entry_audit`、`linking_audit` 和 `proof_artifacts` 均能直接映射到终态章节。

