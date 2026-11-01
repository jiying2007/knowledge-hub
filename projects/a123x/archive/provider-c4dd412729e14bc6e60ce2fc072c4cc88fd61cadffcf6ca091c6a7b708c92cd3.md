---
id: provider-c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3
title: A123X：thermal_zone0是否一定是SoC温度，温度如何读
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3
  source_sha256: 2dd10ebd1c9f031fb2523b799696bdc16181ece2a37b2aeab7f261f06b3f1c79
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
- 温控
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 先读每个thermal_zone的type确认传感器身份，再看temp及trip_point_*_type/temp。手册示例42200对应42.2摄氏度，80000对应80摄氏度，不能按整数摄氏度直接解释。编号会随注册顺序变化，thermal_zone0不能固定当某一传感器；记录节点身份、时间与负载后再比较。示例温控阈值不是A123X当前产品限值。
  适用：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。 来源：downloads/Kernel/Thermal User Guide (0.2)_CN.pdf；PDF物理页
  6,7；SHA256 91ab46b1ad067657d3a92a50869a61e4e3e16bbd4cda52a00e518c42da70c1ae
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: c4dd412729e14bc6e60ce2fc072c4cc88fd61cadffcf6ca091c6a7b708c92cd3
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# thermal_zone0是否一定是SoC温度，温度如何读

先读每个thermal_zone的type确认传感器身份，再看temp及trip_point_*_type/temp。手册示例42200对应42.2摄氏度，80000对应80摄氏度，不能按整数摄氏度直接解释。编号会随注册顺序变化，thermal_zone0不能固定当某一传感器；记录节点身份、时间与负载后再比较。示例温控阈值不是A123X当前产品限值。

适用边界：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。

证据：downloads/Kernel/Thermal User Guide (0.2)_CN.pdf；PDF物理页 6,7；SHA256 91ab46b1ad067657d3a92a50869a61e4e3e16bbd4cda52a00e518c42da70c1ae

状态：2026-10-24整理的reviewing知识候选；原文阅读与内容核验不等于设备实测或生产放行。操作建议尚未在设备执行；具体写操作应在目标、恢复路径与权限明确后实施。
