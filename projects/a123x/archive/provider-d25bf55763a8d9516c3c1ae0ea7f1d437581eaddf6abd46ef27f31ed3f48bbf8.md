---
id: provider-d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8
title: A123X：CPU频率sysfs读数是kHz还是Hz，当前值为何不同
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8
  source_sha256: f511dccfe8aa8612c1e3a28f49710e50b260441a8b93293c5ead93831e90917c
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
- a123x
- 性能功耗
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: cpufreq的频率值按kHz解释；1000000表示1000MHz。scaling_cur_freq来自调频框架，cpuinfo_cur_freq在该手册中描述为从clock tree读取，二者采样来源可能不同。分析时记录policy、时间点、上下限与负载，并与实际clock节点核对；不能直接把框架当前值当同一瞬间硬件实测频率。
  适用：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。 来源：downloads/Kernel/CPU Frequency Scaling User Guide (0.2)_CN.pdf；PDF物理页
  10,14；SHA256 1cd3d7a048ce062107ce35f60aeb83b5ef767fdd97819cb09ee47fd4bbb47f52
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: d25bf55763a8d9516c3c1ae0ea7f1d437581eaddf6abd46ef27f31ed3f48bbf8
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# CPU频率sysfs读数是kHz还是Hz，当前值为何不同

cpufreq的频率值按kHz解释；1000000表示1000MHz。scaling_cur_freq来自调频框架，cpuinfo_cur_freq在该手册中描述为从clock tree读取，二者采样来源可能不同。分析时记录policy、时间点、上下限与负载，并与实际clock节点核对；不能直接把框架当前值当同一瞬间硬件实测频率。

适用边界：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。

证据：downloads/Kernel/CPU Frequency Scaling User Guide (0.2)_CN.pdf；PDF物理页 10,14；SHA256 1cd3d7a048ce062107ce35f60aeb83b5ef767fdd97819cb09ee47fd4bbb47f52

状态：2026-10-24整理的reviewing知识候选；原文阅读与内容核验不等于设备实测或生产放行。操作建议尚未在设备执行；具体写操作应在目标、恢复路径与权限明确后实施。
