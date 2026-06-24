# Knowledge Hub 用户路径边界加固 2026-06-24

## 摘要

本次将用户专属绝对路径边界纳入 Knowledge Hub 的长期治理：长期文本、registry、index、manifest 和工具 JSON 输出统一使用 `~` 用户路径形式；工具内部仍可展开真实路径执行只读检查。

## 变更范围

- 清理已落盘资料、索引、registry、manifest 和迁移副本中的用户专属绝对路径前缀。
- 更新 `tools/knowledge-check.sh`，新增用户路径边界硬门禁。
- 更新核心只读工具的展示层，使 `root`、`path`、source check 路径和搜索结果使用 `~`。
- 更新 `tools/knowledge-regression.sh`，新增持久文本扫描和核心工具输出脱敏回归。
- 更新 regression helper manifest，覆盖新增回归 ID 和当前 122 个场景。

## 边界

- 本次只改 Knowledge Hub 本仓治理层，不修改源项目。
- 本次不写 `~/.codex/memories`。
- 本次不生成 owner decision。
- 本次不提升 active。
- 本次不启用非 report-only 自动化。
- 工具内部路径展开仅用于本机只读检查，不作为长期文本输出格式。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| 禁用前缀扫描 | 0 | 仓库持久文本无用户专属绝对路径前缀残留。 | runtime:path-boundary-scan | Governance | `knowledge-hub-user-path-boundary-20260624` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-24` | 0 | `status=pass`，errors=0，warnings=0；用户路径边界门禁通过。 | runtime:knowledge-check | Governance | `knowledge-hub-user-path-boundary-20260624` |
| `rtk bash tools/knowledge-source-check.sh --json --plan --as-of 2026-06-24` | 0 | `status=planned`；source check 计划输出使用 `~`，内部执行保持只读。 | runtime:knowledge-source-check | Governance | `knowledge-hub-user-path-boundary-20260624` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-24` | 0 | `status=pass`，result_count=122；新增路径边界回归通过。 | runtime:knowledge-regression | Governance | `knowledge-hub-user-path-boundary-20260624` |
