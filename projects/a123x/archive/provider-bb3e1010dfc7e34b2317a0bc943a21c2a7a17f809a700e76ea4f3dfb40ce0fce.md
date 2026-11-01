---
id: provider-bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce
title: A123X独立接口：MBI_ISP_StopPreRoll
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce
  source_sha256: 1bd0131f58df8a99c689982d5474c8ebcf008eb1570d340b4ec71f5dea8b08e9
  temporary_source_retained: false
review_after: '2027-01-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- a123x-api-451
- isp
- declaration-only
- MBI_ISP_StopPreRoll
validation_refs:
- projects/a123x/archive/provider-bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: A123X RC1 MBI_ISP_StopPreRoll；图像处理、停止；当前声明：MBP_S32 MBI_ISP_StopPreRoll(VI_PIPE ViPipe);；文档用途：未定位唯一匹配新版接口章节，仅核声明。；来源：mbi_isp.h:253
  头SHA256 2a1ff1e69916846d48f35f17f16b624fa9d934b9acbbc3ba9b2c886939184bc8；reviewing；实际库/ABI/设备未验证。
primary_language: zh-CN
source_language: en
translation_status: partial
terminology_status: pending
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: bb3e1010dfc7e34b2317a0bc943a21c2a7a17f809a700e76ea4f3dfb40ce0fce
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立接口：MBI_ISP_StopPreRoll

证据等级：声明级，语义待补齐。
适用快照：IPC C5 RC1；2026-10-24来源核验。

## 当前接口声明

`MBP_S32 MBI_ISP_StopPreRoll(VI_PIPE ViPipe);`

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/include/mbi_isp.h:253；SHA256 2a1ff1e69916846d48f35f17f16b624fa9d934b9acbbc3ba9b2c886939184bc8。

## 尚未闭环

- 实际库导出、ABI和运行行为尚未验证；源码/文档说明不代表板级、设备或量产结论。
- 当前13份新版MBI手册中未定位唯一完整接口章节；本条仅证实头文件声明，功能、参数单位和调用约束仍待提炼核实。
- ISP相关语义仍待实现/供应商/库绑定验证。曝光时间存在头文件us与手册x/4096ms差异，增益存在Q22.10与log2/4096差异，AWB使能/旁路字段亦有差异；涉及这些字段时不得直接换算或下发。

证据更新条件：对应头、文档或实际库身份变化时重新核验；本条为reviewing候选。
