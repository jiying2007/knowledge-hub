# Knowledge Hub long-term operations plan 2026-07-11

## 摘要

本计划把 Knowledge Hub mature 终态后的运营节奏固定为可执行、可复查、可回滚的长期维护入口。当前 Hub 已通过 mature gate，后续重点不再是一次性补齐终态，而是防止 `reviewing` 堆积、`review_after` 形成日期债、正文新增后未登记、owner 边界漂移和 full regression 性能退化。

本计划是治理运营计划，不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目、不 push/merge/rebase/tag/release。

## 当前基线

| 指标 | 当前值 | 运营判断 |
| --- | ---: | --- |
| registry item | 312 | 已包含长期运营计划登记 |
| active item | 16 | summary gap 为 0 |
| archived item | 277 | 长期运营计划作为 archived governance audit 登记 |
| reviewing item | 19 | 比例约 6.09%，低于 mature 阈值 10% |
| summary gap | 0 | active/reviewing/archived 均已清零 |
| review queue pending | 0 | 普通 AI/external review queue 已清零 |
| stale review_after | 0 | item/source stale 均为 0 |
| changed orphan | 0 | changed-only orphan check 当前无缺口 |
| mature blocker | 0 | mature audit pass |

## 固定节奏

### Daily

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json
```

通过条件：`health_status=ok`、summary gap 为 0、changed orphan missing 为 0、review queue pending 为 0。

### Weekly

```bash
rtk bash ~/knowledge-hub/tools/knowledge-reviewing-triage.sh --json --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-11 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
```

通过条件：`reviewing` 比例低于 mature 阈值，stale item/source 为 0；near-due 项必须分类为 owner/content/source/tooling 后再处理。

### Monthly

抽样审计 20 条 archived/reviewing 高价值条目：

| 领域 | 数量 | 检查重点 |
| --- | ---: | --- |
| governance | 5 | 摘要是否可读，是否误导为 owner approval |
| PCR02 decision/source-audit | 5 | 是否仍保持 reviewing/archive-only 边界 |
| patents | 5 | 是否保留 disclosure/search 边界 |
| embedded | 5 | 是否把项目特定事实误提升为团队标准 |

月度审计只记录质量结论和 follow-up，不自动 archive、active promotion 或 owner gate closure。

### Release

```bash
rtk git status --short --branch
rtk git diff --check
rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --json --strict
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --strict --json --as-of 2026-07-11 --final-profile mature
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-regression-trend.sh --from-json <full-regression-json> --json
rtk bash ~/codex/scripts/final-ready.sh
```

通过条件：diff check 通过、knowledge-check 0 errors/0 warnings、mature blocker 为 0、full regression 失败 0、final-ready pass。

## Reviewing 处置规则

| recommended_action | 允许动作 | 禁止动作 |
| --- | --- | --- |
| keep-reviewing | 保留 reviewing，并确认 `review_after` | 不因低风险自动 archive |
| evidence-needed | 补 evidence，或明确 archive-only 边界 | 不把缺证据条目提升 active |
| owner-review-and-validation | 走 owner gate、source identity 和验证命令 | 不由 Codex 代签 owner decision |
| archive-ready-check | 补 archive reason 和 validation refs 后归档 | 不删除正文或丢失 provenance |

PCR02 decision candidate、ST77912 结论和 MCU/SoC contract 索引默认保持 `reviewing`，除非 owner 签收、source identity、验证命令和 rollback 边界齐全。

## 性能趋势记录

full regression 后只保留 compact trend：

- `selected_test_count`
- `result_count`
- `failed_ids`
- `slowest_results[0:10]`

不把大段 full regression JSON 写入长期正文。若 full regression 超过 3 分钟，或 top slowest 与上一轮相比明显恶化，单独开性能治理任务。

## 发布与授权边界

- 本地 commit 是 Hub 内可审计维护快照，不等于发布。
- push、merge、rebase、tag、release 必须单独授权。
- commit 不代表 owner approval、active promotion、source project write 或 memory write。
- archive-only 历史证据只能作 provenance，不得反向提升 active fact。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-health-summary.sh --json --as-of 2026-07-11 --skip-final-gate` | 0 | 运营首屏可输出 registry、review queue、review_after、changed orphan、reviewing triage 和 mature audit | `tools/knowledge-health-summary.sh` | Tool | `knowledge-hub-long-term-operations-plan-20260711` |
| `rtk bash tools/knowledge-reviewing-triage.sh --json --as-of 2026-07-11` | 0 | reviewing 队列可按 bucket/action 分组，保持 report-only | `tools/knowledge-reviewing-triage.sh` | Tool | `knowledge-hub-long-term-operations-plan-20260711` |
| `rtk bash tools/knowledge-orphan-files.sh --json` | 0 | changed-only orphan check 可发现新增正文 registry 缺口 | `tools/knowledge-orphan-files.sh` | Tool | `knowledge-hub-long-term-operations-plan-20260711` |

## 下一次复核

- `review_after`: 2026-10-11
- 复核重点：19 个 reviewing 是否仍需保留；PCR02 decision candidate 是否已有 owner evidence；full regression 趋势是否稳定；是否出现新的 changed orphan 或 summary gap。
