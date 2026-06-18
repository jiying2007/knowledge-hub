# 中文开发人员长期资产规范落地 manifest

## 摘要

本 manifest 记录 2026-06-18 对 Knowledge Hub 中文长期资产规范的全面落地。范围覆盖文档可读性、术语表、证据写法、commit/changelog/PR、owner review、排障记录、命令入口、外部资料吸收、中英文命名边界和 AI 生成内容标注。

## 落地清单

| 序号 | 主题 | 权威正文 | 状态 |
| --- | --- | --- | --- |
| 1 | 中文术语表 | `governance/glossary.md` | reviewing |
| 2 | 中文可读性 | `governance/chinese-readability.md` | reviewing |
| 3 | 证据写法 | `governance/evidence-rules.md` | reviewing |
| 4 | commit/changelog/PR | `governance/commit-changelog-pr-rules.md` | reviewing |
| 5 | owner review | `governance/owner-review-rules.md` | reviewing |
| 6 | 排障记录 | `governance/debug-record-rules.md` | reviewing |
| 7 | 命令与工具入口 | `governance/command-tooling-rules.md` | reviewing |
| 8 | 外部资料吸收 | `governance/external-source-absorption.md` | reviewing |
| 9 | 中英文命名边界 | `governance/naming-boundaries.md` | reviewing |
| 10 | AI 生成内容标注 | `governance/ai-generated-content-labeling.md` | reviewing |

## 模板影响

已更新或新增以下模板：

- `templates/README.md`
- `templates/item.md`
- `templates/runbook.md`
- `templates/decision.md`
- `templates/validation-report.md`
- `templates/owner-decision-worksheet.md`
- `templates/debug-record.md`
- `templates/external-source-note.md`

## Registry 与索引

- 新增治理规范条目登记到 `registry/items.jsonl`。
- 新增模板集条目登记到 `registry/items.jsonl`。
- 新增本 manifest 条目登记到 `registry/items.jsonl`。
- 更新 `indexes/by-topic.md`、`indexes/by-status.md`、`indexes/by-owner.md`。

## 边界

- 未修改 PCR02 源项目 docs。
- 未写入 `~/.codex/memories`。
- 未启用自动化写入。
- 未把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 未复制外部资料正文。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`tools/knowledge-check.sh --dry-run`
