---
id: provider-1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f
title: A123X：曝光和白平衡设置接口实际由哪个预编译库导出
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f
  source_sha256: a11bd6f0d21757c53be3779b5c2b2941c8f98e5a62650d4dad563333206e8606
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
- evidence-gap
- isp-exposure-library
validation_refs:
- projects/a123x/archive/provider-1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 当前RC1的ELF符号表显示，MBI_ISP_SetExposureAttr/GetExposureAttr及MBI_ISP_SetWBAttr/GetWBAttr由lib32和lib64的libalg.so导出，所查libmbi_isp.so未列这四个导出。手册接口章节却列libmbi_isp.so依赖。函数名字属于ISP不等于应只链接libmbi_isp；应以当前构建实际链接链和目标架构绑定库身份。这里只核符号存在，未证明曝光单位、增益编码、AWB布局或设备实际装载库，相关冲突继续OPEN。
  来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/lib/lib32/libalg.so SHA256 f588a9938aa210432dfa1f58e7f88b176199c467dca5b13be2ace26e13524554
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 1acb718684771d4ead5e7e44bc088beab76cedf262e05e01ea64a29ce69cb97f
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X：曝光和白平衡设置接口实际由哪个预编译库导出

当前RC1的ELF符号表显示，MBI_ISP_SetExposureAttr/GetExposureAttr及MBI_ISP_SetWBAttr/GetWBAttr由lib32和lib64的libalg.so导出，所查libmbi_isp.so未列这四个导出。手册接口章节却列libmbi_isp.so依赖。函数名字属于ISP不等于应只链接libmbi_isp；应以当前构建实际链接链和目标架构绑定库身份。这里只核符号存在，未证明曝光单位、增益编码、AWB布局或设备实际装载库，相关冲突继续OPEN。

来源：

- workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/lib/lib32/libalg.so SHA256 f588a9938aa210432dfa1f58e7f88b176199c467dca5b13be2ace26e13524554
- workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/isp/lib/lib64/libalg.so SHA256 574972300cdea2e92f1dab6826ccf76fbe6adac2ebefde8d752c05681a134e47
- downloads/IPC SDK Documents/IPC SDK ISP MBI (02).pdf 物理页118起曝光接口，文档依赖需结合当前库核对。

适用边界：2026-10-24本地RC1资料核验；reviewing候选；不代表板级、设备、量产或owner验收通过。
