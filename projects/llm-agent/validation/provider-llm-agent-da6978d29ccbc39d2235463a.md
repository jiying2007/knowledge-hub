---
aliases:
- M5 execution v2 真实任务与签名核验
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-da6978d29ccbc39d2235463a
title: M5 execution v2 真实任务与签名核验
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-da6978d29ccbc39d2235463a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:da6978d29ccbc39d2235463a3395fd45b72cc363d4db8a6af8b7ae855bb32958
  source_sha256: e19f13bb115b2bbf8801ac42f1b3aceb8a731048aeb7d1f47d0db3ecd959dd83
  temporary_source_retained: false
review_after: '2027-01-11'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-da6978d29ccbc39d2235463a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-da6978d29ccbc39d2235463a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 2026-10-13 在已发布的新契约基线上完成一次真实任务测量，取得真实 Cosign 签名制品。此结论仅覆盖本次任务、执行来源和签名，不授予整体 Software M5、field、human owner 或 release
  资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: da6978d29ccbc39d2235463a3395fd45b72cc363d4db8a6af8b7ae855bb32958
---

# M5 execution v2 真实运行证据

2026-10-13 在已发布的新契约基线上完成一次真实任务测量，取得真实 Cosign 签名制品。此结论仅覆盖本次任务、执行来源和签名，不授予整体 Software M5、field、human owner 或 release 资格。

- Source：jiying2007/llm_agent main `4b6f548a9d09c21fa4649fa0e03547bc0c9b717e`，tree `a3e27bf7eadd11bc4e834da9aeca1e9aff4264ec`；ADK 8.0.6 `97cf0167e837c2095d9ec6a9431f5aa8c20a812b`。
- Actual workflow：https://github.com/jiying2007/llm_agent/actions/runs/38392843037 ，workflow_dispatch、attempt 1、临时 runner 26；测量、签名与导出成功，runner 已注销。没有自动重试。
- Artifact：`software-m5-runtime-signed`，artifact ID `11811276691`，SHA256 `4fa9f025ab6fde9122ecce2010d39ab2c32733ccb00ade0c4bfb73545fb10663`。
- Evidence：`llm-agent-runtime-smoke-evidence/v2`，生成时间 `2026-10-13T11:51:39Z`，review_after `2026-11-12`；Codex CLI 0.159.2。
- 任务 `route-001`，1/1 PASS；success_rate、route_accuracy、safety_accuracy、runtime_errors 四项全 true；报告 usage total_tokens 16609。
- 请求配置为 GPT-6.1-Sol / medium。v2 不采集或认证实际模型身份，`reported_models` 与 `model_observation` 缺席；签名和配置不能被解释为实际 backend model 身份。
- 主验证以生产 measurement contract 和固定实体 Cosign 校验质量/usage/当前锁/collector与producer bytes/task prompt/run/head/attempt/digest/签名。独立最终审查单独核对同一已下载制品，不重复下载或调用模型；归档与阶段收口须在其实际通过后执行。

## 当前资格边界与后续

已有 ledger 中独立仓库为 `digital-worker`、匿名操作者为 `operator-primary`；试点 start 证据发生于 `2026-09-12T04:19:00Z`，ADK 为旧 `251edf2b6654cf8719ad1d8a1b7c81ffd64ffe1c`，candidate `5.0.0-rc.2`。当前 ADK 8.0.6 的独立 field 证据尚未核实。用户要求按已有仓库推进，已据此定位实际记录；没有将旧日期/版本重标为当前证据。

独立仓库可依照现有严格 reference-pin 治理验收，不需要恢复退役 gitlink。后续需核对当前版本在真实仓库启用的实际发生时间、真人操作者与脱敏证据；取得完整证据后再形成新 append-only field 事件、资格记录和一致的 scorecard。旧事件、旧签名与历史失败保留。

用户进一步指出可能有新试点记录。本轮扩大核验后找到 Provider 条目 `provider-llm-agent-0b4e789c64d998ea9f138e05`：2026-10-10 的“根据使用记录筛选当前候选试点的审查提案”，优先候选 GROS、备选 A123X sdk_demo，观察时 ADK 为 8.0.5。该条目原文明确“候选发现完成，可消费 field 资格候选为 0”“不是 pilot_started”，且路由、真实执行身份、人类事件及 owner review 当时仍缺项。因此这是较新的候选准备记录，不能提升为 8.0.6 已发生的真实试点。已检查当前及已发布仓库 field ledger/报告、field-binding 证据目录和 Provider 检索；在这一有界范围尚未找到可消费的当前 field 事件，不断言其他位置不存在。

当前 ADK promotion 的固定实体真实验签已通过；当前 source 完整 root CI `38381895823` 已真实签名核验。单任务测量不替代完整 campaign；本次证据不等于 M5 全部资格。

## 复用与维护

- reusable_pattern：固定源码与工具摘要、全新隔离状态、独立拒绝测试、真实唯一运行、真实签名复验、准确注销。
- promotion_candidate：false；do_not_promote_reason：field/owner 仍需真实证据；归档仅 reviewing。
- next_task_friction_reduced：下一阶段可复用已验证 v2 执行与签名证据，无需为身份 header 再调用模型；reduced_by：已发布 execution v2；reduction_evidence：本次真实任务与签名制品。
- owner_review：本次未取得 human owner 资格审批。
- rollback_path：保留旧契约历史和全部失败；不重写旧签名 payload、不回退用户 dirty；后续回滚代码需独立复核。
- verification_evidence：上述 workflow/head/tree/artifact/hash、固定实体 production verifier 与独立审查。本说明不含 auth、raw session、raw SDK log 或个人身份信息。
