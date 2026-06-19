# Knowledge Hub Status Strict Gate 2026-06-19

## 目标

为 `knowledge-status.sh` 增加严格终态门禁，区分“日常看板可读”和“终态验收可放行”。默认状态总览在 `needs-owner-review` 时返回 0，方便人工和 AI 继续维护；`--strict` 在任何非 `ok` 状态下返回 1，避免把 owner gate 未闭环误声明为终版完成。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| KSS-001 | 日常看板 `needs-owner-review` 返回 0，适合继续维护，但不适合作为终态验收门禁。 | 自动化或人工可能只看退出码 0，误以为 Knowledge Hub 已达到终版状态。 | 新增 `tools/knowledge-status.sh --strict`。 |
| KSS-002 | 终态目标要求 owner-gated 残留不得被忽略。 | PCR02 7 个 owner-gated 源文件仍 open 时，不能声明全部迁移落地完成。 | strict 模式要求 `status=ok` 才返回 0。 |
| KSS-003 | 严格门禁不应改变日常维护行为。 | 若默认命令因为 expected owner review 返回 1，会让看板不适合人工巡检。 | 默认退出码保持原语义；只在显式 `--strict` 时收紧。 |

## 决策

- `rtk bash tools/knowledge-status.sh`：日常看板，`needs-owner-review` 返回 0。
- `rtk bash tools/knowledge-status.sh --strict`：终态验收门禁，只有 `status=ok` 返回 0。
- JSON 输出增加 `strict` 字段，便于自动化判断本次运行模式。
- 不改变 `knowledge-check`、`knowledge-owner-gates.sh` 和 `knowledge-doctor.sh` 既有行为。

## 非目标

- 不关闭 PCR02 owner gates。
- 不生成 owner decision。
- 不修改源项目 docs。
- 不提升 owner-gated 内容。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 默认模式保持日常看板语义；当前 `status=needs-owner-review`、`strict=false`、`open_count=7`。 | `tools/knowledge-status.sh` | Knowledge Hub | status-strict-gate |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 expected | strict 模式在当前 `needs-owner-review` 下返回 1；JSON 中 `strict=true`、`open_count=7`。 | `tools/knowledge-status.sh` | Final-state gate | status-strict-gate |
| `rtk bash tools/knowledge-status.sh --help` | 0 | help 展示 `--strict`，说明只有 final status 为 `ok` 时才返回 0。 | `tools/knowledge-status.sh` | Tool smoke | status-strict-gate |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增 strict gate 后全仓门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | status-strict-gate |
| `rtk bash tools/knowledge-search.sh status-strict-gate-applied --json` | 0 | 本制品应可检索，命中 registry、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md`、本 manifest | Knowledge Hub | status-strict-gate |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- review_status：`status-strict-gate-applied`
- 下一次复核内容：若终态定义新增更多阻塞类型，应同步 strict 模式退出码规则和 status dashboard 字段。
