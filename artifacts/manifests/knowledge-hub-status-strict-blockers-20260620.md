# Knowledge Hub status strict blockers 2026-06-20

## 结论

`tools/knowledge-status.sh` 现在在 JSON 和文本看板中显式输出 `strict_blockers`。该字段把终态验收失败原因结构化为可机器读取、可人工扫描的阻塞项，避免 `--strict --json` 返回非零但 `errors=[]` 时被误解为工具异常或无阻塞。

当前唯一 strict blocker 是 `owner-gates-open`：PCR02 仍有 7 条 owner decision worksheet 未签收。它是语义 owner review 门禁，不是 `knowledge-check` 失败。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| SSB-001 | `knowledge-status.sh --strict --json` 能返回非零，但 strict 阻塞原因需要从多个字段推断。 | AI 或人工可能只看到 `errors=[]`，误判终态失败原因不明确。 | 新增 `strict_blockers`，用 `id`、`severity`、`count`、`summary_zh` 和 `commands` 描述阻塞项。 |
| SSB-002 | PCR02 owner gate 是语义门禁，不应混入工具错误。 | 把 owner 未签收当作脚本失败会导致错误修复方向。 | `owner-gates-open` severity 使用 `owner-review`，并提供 summary 和 next-open 命令。 |
| SSB-003 | 终态推进需要可复制的下一步命令。 | 维护者需要在 status、owner board、manifest 之间切换。 | blocker commands 同时包含 `--summary` 和 `--next-open --checklist --forms`。 |

## 变更范围

| 文件 | 变更 |
| --- | --- |
| `tools/knowledge-status.sh` | 新增 `strict_blockers` JSON 字段；文本看板新增 `Strict Blockers` 区块。 |
| `tools/knowledge-regression.sh` | 扩展 `status-next-owner-gate` 回归，验证 strict 返回 1、`owner-gates-open` count=7，并包含 summary 与 next-open 命令。 |
| `tools/README.md` | 说明 `knowledge-status.sh --strict` 会输出 structured strict blockers。 |

## 当前 blocker

| blocker | severity | count | commands |
| --- | --- | ---: | --- |
| `owner-gates-open` | `owner-review` | 7 | `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary`; `rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms` |

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
| `rtk bash tools/knowledge-status.sh --json` | 0 | 通过；默认看板返回 `needs-owner-review`，包含 `strict_blockers[0].id=owner-gates-open`、`count=7` 和 owner summary/next-open 命令。 | `tools/knowledge-status.sh` | Knowledge Hub | `knowledge-hub-status-strict-blockers-20260620` |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 expected | 负结果；strict 终态门禁仍因 7 条 owner gate open 返回 1，`strict_blockers` 明确阻塞原因。 | `tools/knowledge-status.sh` | Final-state gate | `knowledge-hub-status-strict-blockers-20260620` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；18 个回归场景全部 pass，`status-next-owner-gate` 覆盖 strict blocker。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-status-strict-blockers-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认本制品登记后全仓门禁无漂移。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-status-strict-blockers-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --explain knowledge-hub-status-strict-blockers-20260620` | 0 | 通过；新增 item 的 registry、正文和核心索引引用均可解释。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-status-strict-blockers-20260620` |

## Review

- owner：`leiwenjun`
- review_after：`2026-09-20`
- review_status：`status-strict-blockers-applied`
- 复核重点：新增终态阻塞类型时，同步 `strict_blockers` 枚举、回归断言和 README/tool README。
