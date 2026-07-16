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
decision_owner: leiwenjun
summary_zh: 作为 Knowledge Hub 当前产品状态入口，确认 30 个 owner_ref 已通过 hash-bound attestation 绑定；平台结构已就绪，但 source、设备、制品、发布、回滚与真实采用证据仍待闭环，实时数值以
  product gate 为准。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
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

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，decision owner 与 owner_ref 已通过 hash-bound attestation 绑定；工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready；所有计数和技术门禁状态以实时 `knowledge-final-gate.sh --final-profile product` 输出为准。

“平台控制面可交付”和“长期资产终态”是两条不同验收线：前者可以由自动化检查、回归、恢复演练和干净 Git HEAD 证明；后者还要求人工复核队列清零、项目证据契约全部 ready，以及真实检索采用度达标。不得通过代签 owner、填充占位引用、清除历史遥测或生成合成反馈来缩短第二条验收线。

## 终态判定口径

| 验收线 | 必要条件 | 当前判定 |
|---|---|---|
| 平台控制面可交付 | check/schema/link/orphan/retrieval/route/full regression 通过；candidate 与 HEAD restore 新鲜；工作树已形成可审计本地提交 | 2026-07-16 full regression 达 137 个测试函数、140/140 结果通过，candidate restore 通过；`platform_productization_complete=true`。当前工作树仍未提交、HEAD restore 不新鲜，因此 `platform_release_complete=false` |
| 内容治理闭环 | product 普通复核队列为 0；受托复核身份和依据可审计；owner/lifecycle 决定继续走独立 hash-bound attestation；无越权 active promotion | 普通复核队列为 0；30 项 authority-boundary 与 3 项 PCR02 专项 owner attestation 均已落地，候选继续 `reviewing`；真实项目证据仍独立待办 |
| 项目证据闭环 | 30 个 validation item 的 `evidence_contract.status=ready`，且各 profile 的必需引用可解析 | `0/30` ready |
| 长期采用闭环 | 当前交互契约下达到观察期/调用量、性能样本、真实反馈数量和命中率门槛 | 未达到，仍为 `pending` |

只有四项同时满足时，才可声明 `terminal_maturity=true`。技术门禁通过不能替代后面三项。

## 2026-07-16 当前快照

本节是带日期的证据快照，不是永久常量；实时结果由文末命令重算。

| 维度 | 当前证据 | 结论 |
|---|---|---|
| 项目工作台 | 30 个项目、30 条 route、120 个 readiness slot；check 模式 `changed_count=0`；本机 workspace path/state 不写入 tracked 文档 | 结构通过 |
| 项目证据 | 30 个 validation contract，ready `0/30` | 真实证据待补 |
| 人工复核 | 初始 131 条按 `auth-20260715-knowledge-hub-terminal-maturity-push` 受托复核；随后 6 份真实证据报告按 `auth-20260715-knowledge-hub-terminal-maturity-full-closeout` 复核，合计 137 条本轮 review record，均保持 `reviewing -> reviewing` | 普通 review queue 为 0；不等于 owner decision 或项目 evidence-ready |
| Owner worksheet | open row 为 0，但 owner-ready package coverage 为 `0/7` | 不得把“无 open row”解释为 ready package 已存在 |
| 当前交互遥测 | search 10 次、context 43 次，共 53 次；历史或非当前契约记录保留但排除；观察 2 天 | 已通过“30 天或 50 次”中的调用量门槛；不替代反馈与性能门槛 |
| 当前性能 | search P95 3269.45 ms、context P95 1903.01 ms；样本分别为 10/43 | 已可评估且 `fail`，分别高于 500 ms / 1000 ms 目标 |
| 真实反馈与采用 | feedback 0，found/not-found 均为 0；采用判定 `evaluable=false`、`ready=false` | 不得生成合成反馈或为达门槛刷调用 |

### Evidence profile 分布与缺口

| Profile | 项目数 | 必需证据 |
|---|---:|---|
| `aggregate-group` | 1 | owner 引用，以及所有成员项目均 ready |
| `control-plane` | 1 | owner、source、validation、release、rollback |
| `runtime-assets` | 1 | owner、source、validation、release、rollback |
| `software-tool` | 8 | owner、source、validation、artifact、release、rollback |
| `embedded-target` | 19 | owner、source、validation、artifact、device、release、rollback |

按 profile 规则统计，`owner_ref` 与 `validation_refs` 均已实现结构覆盖 30/30；当前尚未满足的其他必需字段为：`artifact_refs` 18 项、`device_refs` 19 项、`release_ref` 21 项、`rollback_ref` 29 项、aggregate `member_project_ids` 1 项。28 个项目已绑定 registered remote 的精确 Git commit；`mm32spin-validator` 没有可用 Git HEAD，改为绑定受治理 source snapshot SHA256，没有伪造 commit；`mcu` 是 aggregate group，不要求独立 source ref。aggregate 成员列表虽已登记，但 evaluator 在成员未全部 ready 时仍将该字段判作未闭环。

2026-07-16 owner checkpoint：`knowledge-hub-terminal-owner-attestation-20260716` 已绑定 30 项通用 authority-boundary；`knowledge-hub-pcr02-specialized-owner-attestation-20260716` 又按独立 Packet 绑定 3 项专项技术边界。120/120 readiness 镜像为 `decision_owner=leiwenjun`，30/30 validation contract 的 `owner_ref` 已绑定；三项专项候选也均为 `decision_owner=leiwenjun / decision_status=accepted-boundary-evidence-pending`。所有项目 contract 仍为 `pending`，0/30 ready；owner 绑定不替代工程、设备、发布、回滚或采用证据。

2026-07-16 adoption checkpoint：当前契约累计 53 次真实交互（search 10、context 43），观察 2 天；显式 feedback 仍为 0。调用量已使采用进入 `evaluable=true`，但 search/context P95 分别为 3269.45ms / 1903.01ms，性能状态仍为 `fail`，长期采用为 `ready=false`。本轮没有用合成调用、合成反馈、删除慢样本或改口径刷绿。

`validation_refs` 存在只证明执行结果可定位，不证明结果通过。PCR02 HDI、sensor、cli、cmd-server、proto-c、product-test 等已绑定真实失败或局部通过报告，contract 仍保持 `pending`。Knowledge Hub 自身已绑定本页作为 validation report，并记录 full regression 140/140 的技术结果；owner、工程/设备、发布、回滚、clean committed HEAD 和采用门槛不会因此改变。

### 授权推动执行记录

- 执行授权：初始批次使用 `auth-20260715-knowledge-hub-terminal-maturity-push`；全面落地批次使用 `auth-20260715-knowledge-hub-terminal-maturity-full-closeout`。二者都只允许 Knowledge Hub 本仓内 `automation-apply-with-review`。
- 复核范围：120 个共享生成器产生的 readiness 记录、11 个初始非模板记录，以及本轮新增的 MCU/SOC/software-tool/PCR02 core/PCR02 robot/LLM Agent 6 份证据报告。
- 复核结果：本轮相关 137 条均为 `accept-as-review-record`，状态保持 `reviewing`；未关闭 owner gate、未提升 active、未写 memory、未修改源项目、未生成合成反馈。
- Source 推进：28 个项目绑定 registered remote 的精确 Git commit；`mm32spin-validator` 绑定 hash-bound source snapshot；aggregate `mcu` 绑定成员列表。16 个 duplicate remote 继续保留为 alternate 诊断，不静默选成第二权威源。
- Validation 推进：30/30 validation item 均已绑定至少一个真实 validation 引用；失败、部分通过、warning 阻塞和通过结果均按实际 outcome 记录。Knowledge Hub 自身绑定本页，full regression 已为 140/140；final gate snapshot 仍需在最终 candidate refresh 后生成。
- Owner attestation：`knowledge-hub-terminal-owner-boundary-20260715` 共 30 行，manifest SHA256 `39c1f84c084d4e37527732ff35216e26f83e1fc5b6527c09cb2c1974a0598975`，确认码 `KH-OWNER-39C1F84C084D`；2026-07-16 已收到并落地完整 hash-bound owner attestation，机械绑定 `decision_owner` 与 `owner_ref`，未提升 active 或 evidence-ready。
- PCR02 专项 owner attestation：真实 owner 已接受 `knowledge-hub-pcr02-specialized-owner-boundary-20260716` 全部 3 行 proposed decision；Packet manifest SHA256 为 `ed72da24c54207f6a52189cc2b11f88a7ac15a10dfce0166460023c9d0ca5e88`，确认码 `KH-PCR02-ED72DA24C542`。三项已绑定同一 attestation 和精确 owner decision，继续保持 `reviewing / promotion=none / manual_validation_pending=true`。
- 授权边界：受托普通复核不是 lifecycle attestation，也不证明真实 build、artifact、device、release 或 rollback 已完成。

### 2026-07-15 全面落地执行检查点

- `goal_statement`：在不降低终态口径、不伪造证据的前提下，推进 30 个项目的内容证据契约、精确 owner 决策和真实采用观察闭环。
- `authorization`：`auth-20260715-knowledge-hub-terminal-maturity-full-closeout`；仅允许 Knowledge Hub 本仓内 `automation-apply-with-review`。
- `claimant`：Codex 执行代理；`verifier`：`knowledge-check`、项目 readiness evaluator、full product final gate 与真实 owner/环境证据。
- `required_evidence`：每个 profile 的必需引用可解析，owner 决策绑定精确正文与身份，采用指标只统计真实交互和显式非合成反馈。
- `retry_budget`：同一自动验证最多重试 2 次；连续两次失败必须更新假设和风险，不继续重复执行。
- `staleness_threshold`：Git HEAD、evidence contract、owner attestation hash 或 telemetry contract 任一变化，已有 checkpoint 立即失效并重跑。
- `heartbeat`：每完成 evidence 盘点、owner packet、adoption 观察、terminal gate 中任一阶段即更新本节或 Evidence Index。
- `stop_condition`：`pass`、`replan`、`split`、`blocked` 或 `abort`；不得用“文档已生成”替代真实证据完成。

| 阶段 | 状态 | 完成标准 | 验证 |
|---|---|---|---|
| S1 授权与基线 | `completed` | 授权账本有效；30 项 evidence matrix 与真实采用基线可复算 | `knowledge-check`、`knowledge-final-gate` |
| S2 真实证据绑定 | `completed-local / external-pending` | 本机可独立核验的 source、30/30 validation 引用、NAS artifact/release 与工具测试已如实绑定；外部 artifact/device/release/rollback 缺口继续显式保留 | readiness evaluator、逐项证据审计、full regression 140/140 |
| S3 Owner 决策 | `completed-owner-boundaries / evidence-pending` | 30 项 authority-boundary 与 3 项 PCR02 专项边界均由真实 owner 以精确 item/hash/decision/确认码接受，且与执行授权分离；不推导 active、release 或 evidence-ready | 两组 Packet、manifest SHA、确认码、attestation 与 landing audit |
| S4 真实采用 | `evaluable / performance-fail / feedback-pending` | 达到调用/观察、性能样本、真实反馈和命中率门槛 | `knowledge-metrics.sh --json` |
| S5 终态收口 | `pending` | full terminal gate 返回 0 且 `terminal_maturity=true` | `knowledge-final-gate.sh --require-terminal --regression-suite full` |

当前 `completion_claim`：尚未完成；30 项 authority-boundary 与 3 项 PCR02 专项 owner 绑定均已完成。最终 tracked 写入后的 candidate/full gate 由实时命令和本地 final-gate snapshot 验证，不再把瞬时 snapshot 回写本页以避免自我失效。clean committed HEAD、真实内容证据和真实采用仍未同时闭环，`terminal_maturity` 不得判真。

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

## 2026-07-15 检索性能诊断

本节按 `adk-systematic-debugging` 记录当前性能失败的证据链；诊断命令均使用 `--no-telemetry` 或直接调用内部只读函数，不计入真实采用样本。

| 假设 | 单变量实验 | 结果 |
|---|---|---|
| H1：每次全量 index rebuild 主导 search 慢样本 | 在当前 1042 个文本文件上分段计时；全量 signature 约 281–295ms，首次 rebuild 约 2787ms，完整 search 约 3466ms | 对 search 最大历史样本成立；10 个当前 search 样本中仅 1 个 `index_rebuilt=true`，其 latency 为 3269.45ms |
| H2：SQLite FTS candidate 查询本身过慢 | 同一 warm index 连续计时 candidate 查询 | 已证伪；3 次约 16–19ms |
| H3：跨进程 warm 路径无法满足 SLA | 3 个 search 与 3 个 context 使用真实查询、`--no-telemetry` 并行复测 | 已证伪；search 411–469ms，context 410–438ms，均低于 500ms / 1000ms 目标 |

5-Why 当前可证实链路为：search P95 失败 → 10 个样本时当前 percentile 实现取最大值 → 最大值来自 tracked 内容变化后的真实全量 rebuild → rebuild 对 1042 文档重新读取和建 FTS/token 索引 → 单次约 2.8s。context 历史 2876.01ms 与 1352.61ms 均标记 `warm`，本轮无法复现，因此其更深根因仍为 `unknown`，不能归因于实现缺陷或宣称已修复。

```text
[repair-note]
failed_scope: 当前契约 search/context P95；search 3269.45ms，context 2876.01ms
passing_scope_to_preserve: warm 检索排序、route/context 语义、隐私遥测契约和不记录 raw query
minimal_rerun: 只统计后续真实交互；若 warm latency 再超过阈值，增加 signature/index/ranking/route 分段时间与主机负载观测
rollback_anchor: 本轮未修改 retrieval 实现，无代码回滚项
root_cause_status: search rebuild known；historical warm context outlier unknown
repair_action: 不用合成调用稀释 P95；保持 needs-fix，等待真实调用复验并在复发时采集分段证据
semantic_verification: 3+3 个 no-telemetry warm 诊断调用均返回正确结果且满足单次 SLA
do_not_repeat: 不重复刷调用、不删除旧遥测、不排除真实慢样本来改变口径
```

## 2026-07-16 检索遍历优化

本节继续按 `adk-systematic-debugging` 收敛上一轮仍为 `unknown` 的 warm 固定成本。所有基线、profile 和复验命令均使用 `--no-telemetry`，不把诊断调用计入真实采用样本，也不删除或重分类既有慢样本。

| 假设 | 单变量实验 | 结果 |
|---|---|---|
| H1：`Path.rglob` 全树遍历是 warm signature 的主要固定成本 | 对同一 warm query 分别 profile search/context | 确认；search 中 signature 为 590ms/总 740ms，context 中 signature 为 497ms/总 641ms；遍历触发约 13171 次 path selection 和 14500 次左右 `stat` |
| H2：SQLite FTS candidate 或排序是主要固定成本 | 对同一 profile 比较 candidate、score 与 signature 累计时间 | 已证伪；candidate 约 33ms，score 约 35–74ms，显著低于 signature |
| H3：context route 装配是主要固定成本 | 对比 context 总时间与内部 search 时间 | 已证伪；route/context 额外开销约 50–65ms，不足以解释历史秒级慢样本 |

修复前，同一查询串行 5 次 warm 复测：search 为 420.56–471.34ms，context 为 396.02–473.81ms。等价性原型将遍历替换为剪枝 `os.walk` 后，文本文件集合保持 `1054/1054`，无 missing/extra，单次枚举从 324.46ms 降至 47.85ms。

最小修复仅把共享 `iter_text_files` 从 `Path.rglob` 改为不跟随目录 symlink、提前剪枝 `.git/.tmp/.cache/__pycache__/.pytest_cache` 的 `os.walk`；`include_control=false` 仍只排除顶层 `registry/tools/artifacts`。index signature 仍按同一文件相对路径、size 和 `mtime_ns` 排序计算，没有改变 freshness、ranking 或 telemetry 契约。

修复后，同一查询串行 5 次 warm 复测：search 为 168.69–178.32ms，context 为 162.00–178.17ms；context profile 总时间从 713ms 降至 331ms，signature 从 497ms 降至 100ms。294 个 case 的 retrieval benchmark 通过：20/20 search hit、MRR 1.0、274/274 route accuracy，search P95 142.90ms、max 152.48ms。

```text
[repair-note]
failed_scope: warm search 固定成本接近 500ms SLA；既有当前契约 P95 仍受历史真实慢样本影响
passing_scope_to_preserve: 1054 个文本文件集合、signature freshness、排序结果、route/context 语义、隐私遥测契约
minimal_rerun: test_common/test_search/test_context/test_retrieval/test_metrics、known-answer search、context smoke、retrieval benchmark、full regression
rollback_anchor: ef7722f 工作树上的 tools/codex_assets/knowledge_hub/common.py 与 tests/test_common.py 局部 diff
root_cause_status: known；通用文本枚举器使用 Path.rglob，对约 13171 个路径逐项构造 Path/is_file/stat
repair_action: 使用剪枝 os.walk，只对文本后缀候选执行 is_file，并补 excluded/control-root 等价性测试
semantic_verification: 定向 38 tests 通过；known-answer Top 3 不变；benchmark hit/MRR/route 均为 1.0，P95 142.90ms
do_not_repeat: 不删除历史 telemetry、不排除真实 rebuild、不用 synthetic interaction/feedback 稀释 P95
```

该修复改善后续真实交互，但不会追溯改写现有 telemetry；因此当前 `adoption.ready` 仍须以实时 `knowledge-metrics.sh --json` 为准，直到真实新样本、至少 10 条显式反馈和 found rate 门槛共同满足。

本轮首次 full regression 返回 1，唯一失败为 `final-gap-readability-positive-contracts`。根因是回归测试仍只允许旧的 `committed-release-evidence-pending`，未同步当前 product gate 已显式输出、且 `codex_auto_can_complete=false` 的 `owner-and-real-evidence-pending`。修复只更新测试契约：允许并校验这两个已知 gap 的 `gap_type` 与自动完成边界，仍拒绝任何未知 gap；没有修改 product gate，也没有把外部证据改为 ready。目标场景复跑通过，随后 full suite 恢复为 137 个测试函数、140/140 结果通过。

## 2026-07-16 首次 rebuild 增量优化

本节继续处理 tracked 文本变化后首个 search 的全量 rebuild 尖峰。所有 profile、性能对照和 benchmark 均使用 `--no-telemetry` 或内部只读调用，不计入真实采用样本。

| 假设 | 单变量实验 | 结果 |
|---|---|---|
| H1：只优化 CJK/ASCII token 即可满足 500ms | 对强制 rebuild 做 cProfile | 已证伪；token 为 1.086s，但扣除后仍有约 2.1s 的 SQLite、source、读取、YAML 与 replace 成本 |
| H2：copy-on-write 小批增量可以直接满足 SLA | 为 28.3MiB index 建副本，只更新一个正文 | 语义通过但性能失败；首次样本 1119.71ms，profile 显示双 signature 201ms、copy/replace 约 209ms |
| H3：SQLite 原地原子事务可保留强一致并消除文件复制 | 使用 rollback journal、`BEGIN IMMEDIATE`、失败 rollback | 确认；一个文件增量事务 35.66ms，完整 search 228.46ms，Top 3 不变 |
| H4：warm signature 仍被重复 stat/Path 转换主导 | 让共享遍历一次返回 path、relative、stat，并改用排序 `os.scandir` | 确认；1054 文件 signature 5 次为 33.28–37.16ms，warm search 5 次为 152.69–191.44ms |

实现将本地 cache schema 升到 v4，并在 SQLite 内增加 `indexed_files(path,size,mtime_ns)`。普通 Markdown/text 的小批增删改按 path 删除旧 documents/FTS 行并插入新行；以下情况仍强制完整 rebuild：

- 冷启动或 schema 升级。
- `registry/items.jsonl`、`registry/sources.json`、`registry/retired-sources.jsonl` 变化，因为它们可能改变全部 item metadata 或 physical source 归属。
- 一次变化超过 128 个文件。
- index/file-state 表缺失、损坏或无法解析。

增量刷新在同一 SQLite 事务内更新 FTS、file state、全局 signature 和 document count；任一步失败都会 rollback，再降级到完整 rebuild。读取端不会使用 stale index。writer 继续由本地 `fcntl` lock 串行化，warm/增量/rebuild 都只计算一次全树 signature。

复验结果：冷 cache 第一次 v4 build 为 2728.49ms，其中 build 2525.39ms；这是仍需显式保留的 cold/full-rebuild 风险。当前 validation 单文件更新触发 `state=updated`，完整 search 227.79ms、事务 38.11ms、增量阶段 67.86ms，changed/deleted 为 1/0。稳定路径 294-case benchmark 为 20/20 search hit、MRR 1.0、274/274 route accuracy，P50 94.41ms、P95 133.20ms、max 152.64ms。

```text
[repair-note]
failed_scope: tracked 正文小改后首次 search 被全量 rebuild 拉到约 2.7–3.5s
passing_scope_to_preserve: 同步 freshness、1054 文件集合、FTS/token 内容、排序、fallback、隐私 telemetry 与真实慢样本
minimal_rerun: test_common/test_search/test_context/test_retrieval/test_metrics、增删改/registry dependency fixture、known-answer、294-case benchmark、full regression、candidate restore、product gate
rollback_anchor: ef7722f 工作树上的 search.py/common.py/test_search.py/test_common.py 局部 diff；cache v3 保留且不作为 v4 权威状态
root_cause_status: known；每次任意正文变化都重建 1054 文件，且初版增量仍重复 signature 并承担 copy/replace 开销
repair_action: v4 file-state 增量计划 + SQLite 原子事务 + 单次 signature + scandir/stat 复用
semantic_verification: 定向 40 tests 通过；增量 Top 3 不变；benchmark hit/MRR/route 均为 1.0，P95 133.20ms
do_not_repeat: 不提供 stale-read 快路径、不删除慢 telemetry、不把诊断调用或 synthetic feedback 计入采用度
```

该优化显著降低普通正文维护后的首次查询成本，但没有把 cold cache、registry 变化或大批变更伪装成增量；这些 full rebuild 仍会作为真实性能样本进入 telemetry，并作为下一阶段优化边界。

## 2026-07-16 冷启动 full rebuild v5 优化

本节继续处理 cold cache、schema 升级和 registry dependency 变化触发的完整 rebuild。所有 profile、原型、强制 rebuild 和 benchmark 均禁用真实交互 telemetry；复现固定为 clean `222730b` 内容、1054 个文件、1059 个 document row 和临时空 cache。

| 假设 | 单变量实验 | 结果 |
|---|---|---|
| H1：临时 SQLite 文件写入主导 0.7s `execute` | 把 rebuild DB 放入内存并跳过持久化，仅测性能上限 | 已证伪；总时延仍为 2076.22–2125.49ms，说明主要成本是 FTS 建索引，不是临时文件 I/O |
| H2：2118 次 Python `execute` 调用主导 | 对同一 1059 行比较逐行写入和两次 `executemany` | 已证伪；逐行为 657.25–689.76ms，`executemany` 为 645.82–673.98ms，差异不足以解释热点 |
| H3：合并 ASCII/CJK 正则扫描可以等价加速 token | 对 1059 个真实 token 输入比较集合和耗时 | 已证伪；输出零差异，但两个实现分别从 839.06/852.17ms 变为 849.29/872.19ms |
| H4：线程或进程并发 token 值得进入默认路径 | 串行、4 线程、2/4/8 进程对照并校验输出 digest | 线程从 846.21ms 恶化到 1595.12ms；8 进程最好 454.75ms，但 full regression 自身为 4 并发，存在放大为 16–32 worker 的过度并行风险，本轮不采用 |
| H5：FTS 同时倒排原始 body 与完整 token 集合造成重复工作 | 只把 FTS `body` 标成 `UNINDEXED`，正文继续保存在 documents 表 | 部分确认；FTS `execute` 从 0.720s 降到 0.604s，294-case 普通查询门禁通过；首次 full regression 暴露结构化过滤仍在 256 candidate 后执行，active/owner 合法结果被截断，必须另补结构化窗口修复 |
| H6：YAML title、physical source 和 token 排序仍有可消除的串行成本 | 全量等价性后分别加入 scalar 快路径、规范路径边界比较和 index 专用顺序去重 | 确认；title 1059/1059、physical source 1054/1054、token 集合 1059/1059 均零差异；查询端 `search_tokens` 排序未改变 |

实现将 cache schema 升到 v5。原始正文仍完整保存在 `documents.body`，FTS 的 `body` 列仅不再建立重复倒排，candidate coverage 继续由 metadata 与正文生成的完整 token 集合承担。index 专用 token 使用确定的首次出现顺序去重，避免全量排序；查询 token 仍沿用既有排序和 `maximum=64` 契约。普通查询保持 256 candidate，结构化过滤扩大到 4096；当前 1059 row 可完整覆盖，过滤后仍由同一 `_filter_reason` 做最终校验。frontmatter 单行 scalar 只解析 title 值，quoted scalar 仍兼容，block/multiline scalar 回退完整 YAML；file symlink 继续 resolve 后再判 physical source。旧 v4 cache 保留但不再作为 v5 权威状态。

无 profile 的三次 v4 clean cold 基线总时延为 2137.17–2318.64ms；最终 v5 三次为 1557.00–1589.43ms，中位数从 2194.20ms 降至 1566.71ms，约下降 28.6%。最终强制 rebuild 为 1571.59ms；294-case benchmark 为 20/20 search hit、MRR 1.0、274/274 route accuracy，P50 85.52ms、P95 134.28ms、max 137.63ms。

```text
[repair-note]
failed_scope: cold cache/schema 升级/registry dependency 完整 rebuild 为 2.14–2.32s，明显高于 500ms 交互目标
passing_scope_to_preserve: 1054 文件与 1059 row、完整正文、candidate coverage、Top 3、增量事务、freshness、fallback、查询 token 契约和真实 telemetry
minimal_rerun: test_search/test_common、强制 cold rebuild 3 次、294-case benchmark、全量 pytest、full regression、clean HEAD restore、product gate
rollback_anchor: 222730b；v4 cache 文件继续保留但不作为 v5 权威状态
root_cause_status: known；Python CJK token 构造与 SQLite FTS 重复 body/token 倒排共同主导，YAML title 和逐 source Path.relative_to 是次级固定成本
repair_action: v5 body UNINDEXED + index 专用确定性 token 去重 + title scalar 快路径 + source path 边界比较 + 结构化过滤 4096 candidate；拒绝低收益 executemany/内存 DB/合并正则与有过度并行风险的 worker 方案
semantic_verification: 等价性样本全通过；benchmark hit/MRR/route 均为 1.0，P95 134.28ms；active/owner 结构化查询返回 5 条、113.2ms，对应最小 regression 通过
do_not_repeat: 不删除正文、不缩减 token 集合、不改查询 token 上限、不用 stale cache、不把普通 benchmark 当成结构化过滤充分证据、不在 full regression 内默认嵌套多进程
```

最终 cProfile 中 index token 仍为 0.922s、FTS 写入仍为 0.607s；因此 cold full rebuild 继续是显式性能债务，不声明达到 500ms。后续若继续优化，应优先评估可控的持久 token provenance 或 FTS 架构变更，并单独设计并发预算，不能直接打开嵌套 worker。

## 人工/真实环境门禁

- [x] Hub 结构验证：registry、route、正文镜像、链接和检索矩阵在当前阶段检查中通过；最终写入后仍需重跑。
- [ ] 来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。
- [x] 责任验证：真实 decision owner `leiwenjun` 已通过 `knowledge-hub-terminal-owner-attestation-20260716` 接受权威边界，并要求继续保持 `reviewing`。
- [x] 控制面验证：2026-07-16 的 full product gate 已覆盖 check、unit、retrieval、route、link、export、candidate restore 与 full regression；这不等于 release 或长期终态通过。

## 精确收口包

### 1. 普通复核队列

2026-07-15 初始与新增证据报告授权批次已经完成，当前 `ai-human-review` 队列为 0。以后出现新队列时，继续按 20 条一批导出：

按 20 条一批导出，`--queue-offset` 依次使用 `0,20,40,60,80,100,120`：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue \
  --queue-type ai-human-review --queue-owner leiwenjun \
  --queue-limit 20 --queue-offset <offset> --queue-forms-jsonl
```

默认情况下，每条表单仍必须由真人依据精确 item、正文和证据填写。本批是在用户引用 131 条阻塞后进一步明确“授权推动”，并由 Codex 对 120 个共享模板资产核验生成器/schema/regression、对 11 个初始非模板资产和 6 份新增证据报告读取完整原文后，以显式 delegated reviewer 身份落地；该例外不得泛化到未来队列。填表后依次执行：

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

1. 当前 30 项 authority-boundary 已由 `knowledge-hub-terminal-owner-attestation-20260716` 绑定真实 decision owner 与 `owner_ref`；若正文、owner 或边界方案变化，必须生成新的精确 Packet/attestation，不能复用本次确认。
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
| decision owner | `leiwenjun` |
| source repo / commit / version | pending |
| 执行环境与设备 | pending |
| 命令与返回码 | pending |
| 日志/截图/制品 hash | pending |
| 回滚验证 | pending |
| 结论和适用边界 | pending |

## Evidence Index

| 证据 | 命令 | 最新结果（截至 2026-07-16） |
|---|---|---|
| readiness generator 无漂移 | `rtk bash ~/knowledge-hub/tools/knowledge-project-readiness.sh --check --json` | pass；30 projects / 120 slots / changed 0 |
| Obsidian 幂等 apply | `rtk bash ~/knowledge-hub/tools/knowledge-obsidian-view-build.sh --apply --json` 与定向 pytest | 修复 `no-change` 与 schema/CLI 成功枚举不一致；8 个定向测试通过，幂等 apply 返回 0 且 schema pass |
| 当前遥测与采用口径 | `rtk bash ~/knowledge-hub/tools/knowledge-metrics.sh --json` | 53 次当前交互、2 天、feedback 0；search/context P95 为 3269.45ms / 1903.01ms，performance fail，adoption evaluable but not ready |
| product 普通复核状态 | `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-type ai-human-review --queue-owner leiwenjun --queue-limit 0 --json` | queue 0；本轮 137 条受托 review record 已落地，状态无提升 |
| 30 项 authority-boundary owner 绑定 | Packet SHA256、attestation、120 个 frontmatter/registry 镜像与 30 个 evidence contract `owner_ref` 交叉校验 | `decision_owner` 120/120、`owner_ref` 30/30；仍为 reviewing/pending，未提升 active/evidence-ready |
| 3 项 PCR02 专项 owner 绑定 | Packet SHA256、三份 before/after 正文 hash、attestation、registry/frontmatter 与 product gate 交叉校验 | `decision_owner / owner_attestation_ref / owner_decision / decision_status` 均为 3/3；仍为 reviewing/evidence-pending，未批准 active/release/evidence-ready |
| source 身份覆盖 | `rtk bash ~/knowledge-hub/tools/knowledge-workspace-discover.sh --plan --first-party-only --json` 与 validation contract | 28 个精确 commit；`mm32spin-validator` 为 hash-bound snapshot；`mcu` 为 aggregate |
| MCU NAS 发布制品 | `sha256sum -c` 与 `firmware-release.sh check-package` | 三包逐文件 checksum 通过；MM32SPIN023C 契约通过；GD32L235、HC32F072 因旧 schema 不兼容失败；实机与回滚未执行，见 `mcu-release-evidence-audit-20260715` |
| PCR02 SSC305 NAS 发布目录 | `sha256sum`、`metadata.env`/manifest 交叉核对 | `soc/v1.1.33` 受控文件已 hash-bound；缺构建来源闭环、目标设备、发布批准与 rollback，见 `2026-07-15-soc-v1.1.33-nas-release-audit.md` |
| PCR02 core 模块构建 | 精确组合源码、派生 SDK 配置、`make -B` 交叉 object build | API/App/MP4 返回 0；HDI 因缺 `cam_dev_wrapper.h` 返回 2，见 `2026-07-15-module-clean-source-build-audit.md` |
| PCR02 Robot 子模块 | 精确 commit + hash-bound harness 交叉构建 | sensor/schema、cli/cmd API、proto false-success、product-test 生成头失败；wifi 与四应用仅 object 层局部通过，见 `2026-07-15-robot-module-contract-audit.md` |
| 软件工具隔离验证 | 干净 Git archive/snapshot 中执行项目 test/release check | `firmware-release-tools` 18 tests、`agent-dev-kit` 52 tests、`ota-packager` 48 tests及 release check、`sigmastar-flasher` 45 tests及无串口 release check 通过；这些结果不替代发布、设备或回滚证据 |
| LLM Agent 精确源码门禁 | 根仓 + 7 个 gitlink 精确隔离 clone，执行 smoke/quick | smoke 12/12、quick 56/56 通过；full/harden、正式 artifact、release、rollback 未闭环 |
| Manifest 配对与 review-queue fixture | manifest profile 门禁；`test_final_gate_product_review_queue_owner_review_blocker` | 两份新 JSONL 已补中文配对说明；测试改为显式注入 2 条合法临时 queue row，不再依赖真实队列非空；定向回归通过 |
| 检索遍历性能 | `knowledge-search/context --no-telemetry`、cProfile、`knowledge-retrieval-benchmark.sh --json` | 文件集合保持 1054/1054；warm search 168.69–178.32ms、context 162.00–178.17ms；benchmark P95 142.90ms，hit/MRR/route 均为 1.0 |
| 增量索引性能 | v4 cold build、单文件 Markdown 更新、signature 5 次、`knowledge-retrieval-benchmark.sh --json` | cold build 2728.49ms；单文件增量 227.79ms、事务 38.11ms；signature 33.28–37.16ms；benchmark P95 133.20ms，语义指标保持 1.0 |
| 冷启动 v5 rebuild | clean `222730b` 临时空 cache、cProfile、等价性检查、`knowledge-retrieval-benchmark.sh --json` | v4 clean cold 2137.17–2318.64ms；v5 为 1557.00–1589.43ms，中位数下降约 28.6%；benchmark P95 134.28ms，hit/MRR/route 均为 1.0 |
| Full regression | `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --suite full --as-of 2026-07-16` | 首轮暴露 1 个 gap-contract drift；定向修复后 pass，137 个测试函数、140/140 结果通过、失败列表为空 |
| Candidate restore | `rtk bash ~/knowledge-hub/tools/knowledge-restore-drill.sh --source-mode candidate --as-of 2026-07-16 --json` | pass；1361 个 candidate path 全部复制，missing/hash mismatch 均为 0，unit/link/Obsidian/retrieval/project/export/search/context/product smoke 全部通过 |
| 控制面完整门禁 | `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-16` | `gate_status=pass`、`platform_productization_complete=true`；工作树未提交使 `platform_release_complete=false` |
| 长期终态门禁 | 在上一命令增加 `--require-terminal` | 退出 2；`terminal_maturity=false`，blocker 为 `owner-and-real-evidence-pending` 与 `committed-release-evidence-pending` |

## Goal Closure

- 自动化目标：修复可复现的控制面、恢复、性能口径和验证问题，并形成可审计、可恢复、全回归通过的工作树；本轮不自动创建 commit，clean committed HEAD 继续作为 delivery gate。
- 已完成的受托目标：本轮 137 条普通 AI review record 已完成透明 delegated closeout；30 项 authority-boundary 已由真实 owner 的 hash-bound attestation 绑定；28 个项目绑定精确 source commit，`mm32spin-validator` 绑定 source snapshot；所有可本机独立核验的 validation 与已有 NAS artifact/release 证据已如实绑定。
- 外部目标：3 个 PCR02 专项 owner 决定已经完成；仍有 18 个 artifact、19 个 device、21 个 release、29 个 rollback 缺口，以及长期采用反馈。这些证据不能由 Codex 自行生成。已绑定的失败 validation 还需要源项目修复和复测。
- 当前决策：普通复核、30 项 authority-boundary 和 3 项 PCR02 专项 owner 绑定均已完成；长期终态继续保持 `evidence-pending`，直到真实责任人和实际环境补齐项目证据与采用门槛。
- 失效条件：Git HEAD、working-tree signature、evidence contract 或 telemetry contract 变化后，旧 final-gate/restore snapshot 立即失效，必须重跑。

## Related

- [项目画像候选](../current/project-profile.md)
- [维护 runbook](../current/runbooks/maintenance-entry.md)
- [边界决策候选](../decisions/project-boundary-decision-candidate.md)
- [项目入口](../../../README.md)
