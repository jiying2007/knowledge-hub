# Knowledge Hub review_after、主题恢复与 owner 表单加固 2026-06-22

## 结论

本轮在不关闭 owner gate、不生成 owner decision 的前提下，继续压实终态前的人工治理入口：

- `knowledge-review-after.sh` 增加人工复核分组视图，JSON 输出按 owner、status、domain、source_id 分组，并标记缺失 source_id 的条目。
- `indexes/by-topic.md` 增加“优先恢复主题速查”，把 PCR02 迁移、owner gate、ASAN、DVR、memory auto-curation、motor MCU、自动化和终态回归入口集中到第一屏。
- `knowledge-owner-gates.sh` 增加 `target_candidates` 防篡改校验，并把 repo-relative `rtk bash tools/...` 从 safe command candidate 中移除。
- `knowledge-regression.sh` 增加 3 个 owner 表单回归：`reference-only/reference-only` 正向、`no-migration/no-migration` 正向、`target_candidates` 篡改拒绝；同时锁定 review_after 分组契约。

## 边界

- 不修改 PCR02 源项目 docs、tools、knowledge、product-test、scratch 或其他 source 文件。
- 不复制 owner-gated source 正文。
- 不生成 owner decision，不代填 `reviewed_by`，不关闭 7 个 PCR02 owner gate。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。
- `review_after` 仍是人工治理提醒，不作为 blocking gate。

## 变更明细

| 区域 | 文件 | 变更 |
|---|---|---|
| report-only review_after | `tools/knowledge-review-after.sh` | 增加 `groups` JSON 契约、`source_id/source_status` 明细字段和文本分组输出 |
| owner gate | `tools/knowledge-owner-gates.sh` | 拒绝 owner form 改写 `target_candidates`；safe command candidate 只保留 cwd-stable 稳定命令 |
| 回归 | `tools/knowledge-regression.sh` | 新增 owner 合法终止组合正向门禁、`target_candidates` 篡改拒绝、review_after 分组断言 |
| 主题恢复 | `indexes/by-topic.md` | 增加第一屏优先恢复主题速查 |
| 人工维护提示 | `README.md`、`indexes/README.md` | 将弱 `required_followup` 改为稳定 `rtk bash ~/knowledge-hub/tools/...` 命令 |
| 回归 manifest | `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 补齐新增回归 ID 和覆盖描述 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -n tools/knowledge-review-after.sh` | 0 | shell 语法通过 | `tools/knowledge-review-after.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash -n tools/knowledge-owner-gates.sh` | 0 | shell 语法通过 | `tools/knowledge-owner-gates.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash -n tools/knowledge-regression.sh` | 0 | shell 语法通过 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash tools/knowledge-review-after.sh --json --as-of 2026-06-22 --window-days 30` | 0 | 32 个 near-due、0 个 stale、7 个 owner gate open；分组为 team-core=23、leiwenjun=9、reviewing=26、archived=6、projects/pcr02=31、governance=1、pcr02-project-docs=23、missing source_id=9 | `tools/knowledge-review-after.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22` | 0 | 101 个回归场景通过 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22` | 0 | 全仓知识门禁通过；0 errors、0 warnings | `tools/knowledge-check.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22` | 1 | 预期停在 `needs-owner-review`；唯一 blocker 为 `owner-gates-open`，7 个 owner gate 仍待人工签收 | `tools/knowledge-final-gate.sh` | Tool | `knowledge-hub-review-after-topic-owner-hardening-20260622` |

## 后续人工动作

- owner 继续从 `tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --next-open --checklist --forms` 聚焦下一条 open worksheet。
- 若 owner 填写 `reference-only` 或 `no-migration`，`target_decision` 必须与该终止决策一致。
- 若 owner form 中 `target_candidates`、`must_not` 或 `allowed_owner_decisions` 被改写，必须丢弃该表单并从工具重新生成。
- `knowledge-review-after.sh` 输出仅用于人工安排复核，不自动变更 `review_after`。
