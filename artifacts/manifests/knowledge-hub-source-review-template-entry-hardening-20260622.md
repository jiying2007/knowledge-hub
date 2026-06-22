# Knowledge Hub Source Review, Template and Entry Hardening 2026-06-22

## 摘要

本次收口面向终态目标中的长期维护瓶颈，压实三类可由 Codex 自动完成的治理切片：

- source `review_after` 过期不再只校验日期格式，而是作为 warning/status surface 暴露到 `knowledge-check` 与 `knowledge-status`。
- README 与 tools README 增加“日常路径 / owner gate / 终态检查 / 高级写入计划”低复杂度入口速查，降低中文维护者首次操作成本。
- 模板增加字段填写矩阵和短引用，明确“必须填 / 条件填 / 不得填 / 不能伪造”，避免人工新增时漏填中文摘要、证据、AI provenance 或误把 worksheet 当 owner decision。

## 改动范围

| 文件 | 改动 |
|---|---|
| `tools/knowledge-check.sh` | `source_check_health` 增加 `stale_review_after_ids`、`stale_review_after_source_ids` 和逐行 `review_after_stale`，过期 source 输出 warning 但不阻断。 |
| `tools/knowledge-status.sh` | `sources` 区块增加 `stale_review_after_count`、`stale_review_after_sample` 和 source 复核命令，并在 `next_actions_zh` 中提示过期 source 复核。 |
| `tools/knowledge-regression.sh` | 新增 `source-review-after-stale-surface` 回归场景，验证 source stale 是 warning/status surface。 |
| `registry/schema.md` | 记录 stale source `review_after` 的非阻断语义和 JSON 输出字段。 |
| `README.md`、`tools/README.md` | 增加四层低复杂度入口速查。 |
| `templates/README.md` | 增加字段填写矩阵。 |
| `templates/item.md`、`templates/owner-decision-worksheet.md` | 增加字段矩阵短引用和 owner worksheet 不代签提示。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 登记新增回归 ID，并把场景计数更新为 79。 |

## 边界

- 不生成 owner decision。
- 不关闭任何 owner gate。
- 不修改 PCR02 源项目文件。
- 不复制 owner-gated source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 验证计划

```bash
rtk bash -n tools/knowledge-check.sh
rtk bash -n tools/knowledge-status.sh
rtk bash -n tools/knowledge-regression.sh
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22
rtk bash tools/knowledge-status.sh --json --as-of 2026-06-22
rtk bash tools/knowledge-regression.sh --as-of 2026-06-22
rtk git diff --check
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22
```

## 当前阻塞

自动治理继续推进后，终态仍应停在 `needs-owner-review`，前提是 final gate 证明唯一 blocker 仍是 `owner-gates-open`。7 个 PCR02 owner gate 不能由 Codex 代签。
