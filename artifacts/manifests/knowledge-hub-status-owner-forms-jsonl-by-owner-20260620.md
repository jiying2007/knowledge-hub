# Knowledge Hub status owner forms JSONL by owner 2026-06-20

## 结论

本轮把按 owner 导出 owner decision JSONL 骨架的只读命令暴露到 `knowledge-status.sh`。这样人工分派 owner gate 时，可以直接从 status/final gate blocker 里看到“某个责任人只需要填写哪些 JSONL 行”，不必先导出全量 7 行再手工筛选。

该能力不生成 owner decision、不写文件、不关闭 gate、不提升 active，只输出空白骨架和只读上下文。

## Issue Map

| ID | Finding | Severity | Evidence | Action | Status |
|---|---|---|---|---|---|
| OSFBO-001 | `knowledge-status.sh` 已有 by-owner summary 命令，但缺少 by-owner forms-jsonl 命令 | P2 | `tools/knowledge-status.sh`、`tools/knowledge-owner-gates.sh --owner project-owner --forms-jsonl` | 增加 `owner_forms_jsonl_commands` | applied |
| OSFBO-002 | strict blocker 里 owner 可执行命令缺少按责任人导出 JSONL 骨架入口 | P2 | `tools/knowledge-status.sh --strict --json` | 将 by-owner forms-jsonl 命令加入 `strict_blockers[].commands` | applied |
| OSFBO-003 | 回归只覆盖全量 forms-jsonl 和 next-open forms-jsonl，未覆盖 by-owner forms-jsonl 可发现性 | P2 | `tools/knowledge-regression.sh` | 增强 `status-next-owner-gate` 回归断言 | applied |

## 人工使用方式

```bash
rtk bash tools/knowledge-status.sh --strict --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl
```

owner 填写完成后仍必须走只读校验和 no-write landing plan：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

## 边界

- 不生成 owner decision。
- 不关闭 owner gate。
- 不写 owner decision JSONL。
- 不修改 PCR02 源项目 docs。
- 不复制 owner-gated 正文。
- 不启用自动化写操作，不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --owner project-owner --forms-jsonl` | 0 | 输出 `project-owner` 对应 2 条 owner decision JSONL 空白骨架 | `tools/knowledge-owner-gates.sh` | Owner gate | `knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 | 预期停在 `needs-owner-review`；输出 6 条 `owner_forms_jsonl_commands`，strict blocker 包含 by-owner forms-jsonl 可执行命令 | `tools/knowledge-status.sh` | Status | `knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓知识库检查通过，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 33 个回归场景通过，包含 status owner forms-jsonl 可发现性断言 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` | 0 | 新审计工件 registry 与核心索引引用正常 | `tools/knowledge-check.sh` | Registry/index | `knowledge-hub-status-owner-forms-jsonl-by-owner-20260620` |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-owner-forms-jsonl-by-owner-applied`
- 下一步：等待真实 owner 填写 owner decision JSONL；Codex 只允许校验和生成 no-write landing plan。
