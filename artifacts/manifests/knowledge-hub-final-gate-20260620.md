# Knowledge Hub Final Gate 2026-06-20

## 结论

新增 `tools/knowledge-final-gate.sh` 作为仓库只读的终态验收聚合入口。它同时运行：

- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`
- `rtk bash tools/knowledge-regression.sh --json`
- `rtk bash tools/knowledge-status.sh --strict --json`

只有三者都达到终态条件时才返回 0。当前仓库仍会返回 1，因为 PCR02 还有 7 条 owner decision worksheet 未签收；这是语义 owner review blocker，不是工具失败。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| KFG-001 | `knowledge-status --strict` 不运行 regression。 | 终态检查若只看 status，可能漏掉 regression manifest coverage 等漂移。 | 新增 `knowledge-final-gate.sh` 聚合 check、regression 和 strict status。 |
| KFG-002 | final gate 调用 regression，而 regression 又需要测试 final gate。 | 直接互调会递归并放大 `/tmp` 临时副本压力。 | final gate 默认完整运行 regression；仅 regression 自测 final gate 时使用内部环境标记跳过嵌套 regression。 |
| KFG-003 | owner gate 未签收不应被伪装成工具失败。 | 维护者可能误修工具而不是收 owner decision。 | final gate 复用 `strict_blockers`，当前状态为 `needs-owner-review`，blocker 为 `owner-gates-open`。 |

## 决策

- `knowledge-final-gate.sh` 对 Knowledge Hub 正文、registry、index 和源项目 docs 只读，不提交、不提升任何文件；内部 regression 子命令可能使用 `/tmp` 临时 fixture，并在结束时清理。
- `final_status=ok` 仅在 `knowledge-check`、`knowledge-regression` 和 `knowledge-status --strict` 全部通过时成立。
- 当前 `final_status=needs-owner-review` 是预期结果，说明控制面健康但 owner 语义门禁未闭环。
- `knowledge-status.sh` 保持轻量，不默认运行 regression；终态验收使用 final gate。

## 非目标

- 不关闭 PCR02 owner gates。
- 不生成 owner decision。
- 不修改源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 expected | 预期返回 `needs-owner-review`；`knowledge-check=pass`、`knowledge-regression=pass`、`knowledge-status --strict=needs-owner-review`，blocker 为 `owner-gates-open count=7`。 | `tools/knowledge-final-gate.sh` | Final-state gate | `knowledge-hub-final-gate-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；20 个回归场景全部 pass，包含 `final-gate-owner-review-blocker`。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-final-gate-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-final-gate-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-final-gate-20260620` | 0 | 通过；registry item 和核心索引可解释。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-final-gate-20260620` |

## Review

- owner: `leiwenjun`
- status: `reviewing`
- review_after: `2026-09-20`
- review_status: `final-gate-applied`
- 下一次复核内容：若终态验收新增门禁，必须同步 final gate、regression 场景、README 和本 manifest。
