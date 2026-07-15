---
id: knowledge-hub-readiness-validation-20260713
title: Knowledge Hub 当前产品状态与证据缺口
kind: validation
domain: governance
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- knowledge-hub
- project-readiness
- validation
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
decision_owner: unassigned
summary_zh: 作为 Knowledge Hub 当前产品状态入口，明确平台结构已就绪而真实 owner、source、设备、制品、发布和回滚证据仍待闭环；实时数值以 product gate 为准。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: governance/product/validation/project-readiness.md
project_id: knowledge-hub
readiness_slot: validation
aliases:
- knowledge-hub validation
- knowledge-hub-validation
related:
- README.md
- governance/product/current/project-profile.md
- governance/product/current/runbooks/maintenance-entry.md
- governance/product/decisions/project-boundary-decision-candidate.md
---

# Knowledge Hub 当前产品状态与证据缺口

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，真实 owner、工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready；所有计数和技术门禁状态以实时 `knowledge-final-gate.sh --final-profile product` 输出为准。

“平台控制面可交付”和“长期资产终态”是两条不同验收线：前者可以由自动化检查、回归、恢复演练和干净 Git HEAD 证明；后者还要求人工复核队列清零、项目证据契约全部 ready，以及真实检索采用度达标。不得通过代签 owner、填充占位引用、清除历史遥测或生成合成反馈来缩短第二条验收线。

## 终态判定口径

| 验收线 | 必要条件 | 当前判定 |
|---|---|---|
| 平台控制面可交付 | check/schema/link/orphan/retrieval/route/full regression 通过；candidate 与 HEAD restore 新鲜；工作树已形成可审计本地提交 | 自动收口中，以最新 final gate 为准 |
| 内容治理闭环 | product 普通复核队列为 0；受托复核身份和依据可审计；owner/lifecycle 决定继续走独立 hash-bound attestation；无越权 active promotion | 普通复核已完成，owner/lifecycle 未被代签 |
| 项目证据闭环 | 30 个 validation item 的 `evidence_contract.status=ready`，且各 profile 的必需引用可解析 | `0/30` ready |
| 长期采用闭环 | 当前交互契约下达到观察期/调用量、性能样本、真实反馈数量和命中率门槛 | 未达到，仍为 `pending` |

只有四项同时满足时，才可声明 `terminal_maturity=true`。技术门禁通过不能替代后面三项。

## 2026-07-15 当前快照

本节是带日期的证据快照，不是永久常量；实时结果由文末命令重算。

| 维度 | 当前证据 | 结论 |
|---|---|---|
| 项目工作台 | 30 个项目、30 条 route、120 个 readiness slot；check 模式 `changed_count=0`；本机 workspace path/state 不写入 tracked 文档 | 结构通过 |
| 项目证据 | 30 个 validation contract，ready `0/30` | 真实证据待补 |
| 人工复核 | 用户后续明确“授权推动”；131 条 `ai-human-review` 已按 `auth-20260715-knowledge-hub-terminal-maturity-push` 受托复核并以 `leiwenjun-via-codex-delegation` 落地；131 条均保持 `reviewing -> reviewing` | 普通 review queue 已清零；不等于 owner decision 或项目 evidence-ready |
| Owner worksheet | open row 为 0，但 owner-ready package coverage 为 `0/7` | 不得把“无 open row”解释为 ready package 已存在 |
| 当前交互遥测 | search 4 次、context 5 次，共 9 次；379 条历史或非当前契约记录保留但排除 | 新口径已生效，样本不足 |
| 当前性能 | search P95 3269.45 ms、context P95 2876.01 ms；样本分别为 4/5，最低各 10 个 | 小样本提示性能风险，但统计状态仍为 `pending`，不得据此宣称稳定通过或失败 |
| 真实反馈与采用 | feedback 0；采用判定 `ready=false` | 不可判定为长期采用 |

### Evidence profile 分布与缺口

| Profile | 项目数 | 必需证据 |
|---|---:|---|
| `aggregate-group` | 1 | owner 引用，以及所有成员项目均 ready |
| `control-plane` | 1 | owner、source、validation、release、rollback |
| `runtime-assets` | 1 | owner、source、validation、release、rollback |
| `software-tool` | 8 | owner、source、validation、artifact、release、rollback |
| `embedded-target` | 19 | owner、source、validation、artifact、device、release、rollback |

按 profile 规则统计，当前尚未满足的必需字段为：`owner_ref` 30 项、`source_refs` 1 项、`validation_refs` 29 项、`artifact_refs` 27 项、`device_refs` 19 项、`release_ref` 29 项、`rollback_ref` 29 项。28 个项目已绑定 registered remote 的精确 Git commit；`mm32spin-validator` 的发现结果没有可用 Git HEAD，不能伪造 source commit。aggregate group 的成员列表已经登记，但在成员项目全部 ready 前仍不满足聚合终态。

### 授权推动执行记录

- 执行授权：`auth-20260715-knowledge-hub-terminal-maturity-push`，只允许 Knowledge Hub 本仓内 `automation-apply-with-review`。
- 复核范围：120 个共享生成器产生的 readiness 记录，以及 11 个逐项回退完整原文审阅的非模板记录。
- 复核结果：131 条全部为 `accept-as-review-record`，状态均保持 `reviewing`；未关闭 owner gate、未提升 active、未写 memory、未修改源项目、未生成合成反馈。
- Source 推进：本机按 exact registered remote 找到 29/29 个 remote；其中 28 个具有可绑定 commit，已写入对应 validation contract 的 `source_refs`。16 个 duplicate remote 继续保留为 alternate 诊断，不静默选成第二权威源。
- 授权边界：受托普通复核不是 lifecycle attestation，也不证明真实 build、artifact、device、release 或 rollback 已完成。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] 30 项目 route matrix 能将 `knowledge-hub` 稳定解析为本项目。
- [x] profile、runbook、decision、validation 四个入口均存在且互相可达。
- [x] search known-answer 与 link audit 通过。
- [ ] 本机 source 定位：运行 `knowledge-workspace-discover.sh --plan --json`，由 project gate 动态读取；结果不得复制到 tracked Markdown。

## 已落地的测量完整性优化

- 当前交互统一使用 `knowledge-retrieval-interaction-v1`，遥测 schema 为 v3；旧记录保留作历史证据，但不参与当前性能或采用度判定。
- search/context 记录不可逆 query hash、`interaction_id` 和本次 `result_ids`，不保存原始 query。
- feedback schema v2 必须绑定一个已观察到的当前交互；`found` 的 `selected_id` 必须属于该交互结果，且同一交互只能提交一次反馈。
- search/context 各不足 10 个当前样本时，性能状态为 `pending`，不能因单次快速调用被判为通过。
- 长期采用要求：观察至少 30 天或当前交互至少 50 次、两类性能样本各至少 10 个、真实反馈至少 10 条、`found_rate >= 0.8`，并且性能通过。

这套口径用于防止旧实现样本污染、重复反馈和“跑脚本刷绿”；它不会把缺少真实用户行为的问题自动消除。

## 人工/真实环境门禁

- [ ] Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。
- [ ] 来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。
- [ ] 责任验证：由真实 decision owner 明确接受、修改或拒绝边界候选。
- [ ] 控制面验证：执行 check、unit、retrieval、route、link、export 和 restore drill。

## 精确收口包

### 1. 普通复核队列

2026-07-15 授权批次已经完成，当前 `ai-human-review` 队列为 0。以后出现新队列时，继续按 20 条一批导出：

按 20 条一批导出，`--queue-offset` 依次使用 `0,20,40,60,80,100,120`：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue \
  --queue-type ai-human-review --queue-owner leiwenjun \
  --queue-limit 20 --queue-offset <offset> --queue-forms-jsonl
```

默认情况下，每条表单仍必须由真人依据精确 item、正文和证据填写。本批是在用户引用 131 条阻塞后进一步明确“授权推动”，并由 Codex 对 120 个共享模板资产核验生成器/schema/regression、对 11 个非模板资产读取完整原文后，以显式 delegated reviewer 身份落地；该例外不得泛化到未来队列。填表后依次执行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue \
  --json --validate-queue-forms '<filled-review-queue-forms.jsonl>'
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh \
  --forms '<filled-review-queue-forms.jsonl>' --dry-run --json
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh \
  --forms '<filled-review-queue-forms.jsonl>' --apply --json
```

最后一条写操作只可在精确人工复核或明确、可审计的 delegated review 授权已具备后执行。delegated review 必须使用 `<human>-via-codex-delegation`，记录 authorization、原文读取层级、依据和 guardrail；不得伪装成真人直接签收，也不得用于 owner decision、active promotion 或 lifecycle attestation。

### 2. 项目证据契约

每个项目以其 validation item 为唯一 readiness 入口。每条引用至少包含：

```json
{"kind":"<owner-attestation|source-commit|validation-report|artifact-sha256|device-run|release-record|rollback-drill>","ref":"<可定位的 Hub 路径、源仓 commit、制品 URI 或报告 ID>"}
```

采集顺序为：

1. 确认真实 decision owner，写入可追溯的 `owner_ref`。
2. 绑定源仓 remote/repository identity 与精确 commit/version，写入 `source_refs`。
3. 写入实际执行的命令、环境、返回码和报告路径；软件/设备项目分别补 artifact hash 与 device run。
4. 绑定 release record 与 rollback drill；确实不适用的字段必须在 `not_applicable` 中同时记录 `owner_ref`、`authorization_id` 和理由。
5. 仅在必需引用均可解析、证据与适用边界经过复核后，将 contract 状态改为 `ready`，随后重跑 project/final gate。

本页不代替 30 个源项目产生事实，也不把“源码路径可定位”当作工程、设备或发布验证。

### 3. 真实采用反馈

正常使用 `knowledge-search.sh` 或 `knowledge-context.sh` 后，以完全相同的 query 记录真实结果：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-feedback.sh \
  --query '<实际 query>' --outcome found \
  --selected-id '<本次结果中的 item id>' \
  --interaction-id '<本次 interaction_id>' --json
```

未找到时使用 `--outcome not-found`，不得提供虚假 `selected_id`。达到观察门槛后运行 `knowledge-metrics.sh --json`；自动化冒烟调用和 Codex 合成反馈不计作长期采用证据。

## 证据记录模板

| 字段 | 待填写 |
|---|---|
| decision owner | `unassigned` |
| source repo / commit / version | pending |
| 执行环境与设备 | pending |
| 命令与返回码 | pending |
| 日志/截图/制品 hash | pending |
| 回滚验证 | pending |
| 结论和适用边界 | pending |

## Evidence Index

| 证据 | 命令 | 2026-07-15 结果 |
|---|---|---|
| readiness generator 无漂移 | `rtk bash ~/knowledge-hub/tools/knowledge-project-readiness.sh --check --json` | pass；30 projects / 120 slots / changed 0 |
| 当前遥测与采用口径 | `rtk bash ~/knowledge-hub/tools/knowledge-metrics.sh --json` | schema v2；performance/adoption pending |
| product 普通复核状态 | `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 0 --json` | queue 0；131 条受托 review record 已落地，状态无提升 |
| source commit 覆盖 | `rtk bash ~/knowledge-hub/tools/knowledge-workspace-discover.sh --plan --first-party-only --json` 与 validation contract | registered remote 29/29；精确 commit 28；`mm32spin-validator` 缺 Git HEAD |
| 控制面完整门禁 | `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-15` | 候选冻结和提交后重跑；以生成 snapshot 为准 |
| 长期终态门禁 | 在上一命令增加 `--require-terminal` | 只允许在 review/evidence/adoption 同时闭环后为真 |

## Goal Closure

- 自动化目标：修复可复现的控制面、恢复、性能口径和验证问题，并形成干净、可恢复、全回归通过的本地提交。
- 已完成的受托目标：131 条普通 AI review record 已完成透明 delegated closeout；28 个项目已绑定精确 source commit。
- 外部目标：30 个项目的 owner、validation、artifact/device、release、rollback 证据，以及长期采用反馈；这些证据不能由 Codex 自行生成。`mm32spin-validator` 还缺可用 source commit。
- 当前决策：普通复核阻塞已消除；长期终态继续保持 `evidence-pending`，直到真实责任人和实际环境补齐项目证据与采用门槛。
- 失效条件：Git HEAD、working-tree signature、evidence contract 或 telemetry contract 变化后，旧 final-gate/restore snapshot 立即失效，必须重跑。

## Related

- [项目画像候选](../current/project-profile.md)
- [维护 runbook](../current/runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [项目入口](../../../README.md)
