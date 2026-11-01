---
id: provider-0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3
title: A123X：SD、USB、存储启动的U-Boot镜像如何区分
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3
  source_sha256: bf54eee63b16ae1ee0822842f3313daf5dc85812aa3d0bd2a0810617fdfcba13
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
- 启动
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 手册区分u-boot.bin.sd.bin.signed（SD启动）、u-boot.bin.usb.signed（USB启动）与u-boot.bin.signed（存储启动）。小GPT方案可能另用spl.sto.bin.signed和tpl.bin.signed，并要求对应SPL/TPL分区；不能直接把拆分镜像塞进旧单bootloader分区。选镜像同时核对启动介质、分区布局和当前打包规则。文件名含signed不证明设备信任链已生产验证。
  适用：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。 来源：downloads/Kernel/Bootloader Development Guide (0.1)_CN.pdf；PDF物理页
  10；SHA256 2c9355ba1fc6952cd2965a43697254c63b2139e69e0146648e626c242bf6143b
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 0bec75e3b07616c613d1bbae92daf38d2dc8df7b0311f2de1ad59bcd34a0eda3
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# SD、USB、存储启动的U-Boot镜像如何区分

手册区分u-boot.bin.sd.bin.signed（SD启动）、u-boot.bin.usb.signed（USB启动）与u-boot.bin.signed（存储启动）。小GPT方案可能另用spl.sto.bin.signed和tpl.bin.signed，并要求对应SPL/TPL分区；不能直接把拆分镜像塞进旧单bootloader分区。选镜像同时核对启动介质、分区布局和当前打包规则。文件名含signed不证明设备信任链已生产验证。

适用边界：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。

证据：downloads/Kernel/Bootloader Development Guide (0.1)_CN.pdf；PDF物理页 10；SHA256 2c9355ba1fc6952cd2965a43697254c63b2139e69e0146648e626c242bf6143b

状态：2026-10-24整理的reviewing知识候选；原文阅读与内容核验不等于设备实测或生产放行。操作建议尚未在设备执行；具体写操作应在目标、恢复路径与权限明确后实施。
