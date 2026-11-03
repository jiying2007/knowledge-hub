---
id: provider-1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf
title: A123X接口知识卡：MBI_PPU_ReleaseChnFrame
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf
  source_sha256: 77fd4d6f8b68543e7f87c209d320ea04e550e49ee8364c76e13ab581b20d19a9
  temporary_source_retained: false
review_after: '2027-01-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- runbook
- a123x-answer-card-v2
- api
validation_refs:
- projects/a123x/archive/provider-1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；接口 MBI_PPU_ReleaseChnFrame 的头文件声明：MBP_S32 MBI_PPU_ReleaseChnFrame(MBP_S32 ppuDev,
  PPU_CHN ppuChn, MBP_VIDEO_FRAME_INFO_T *frame); 条件编译是否启用及实际运行库导出需分别核实。 来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/ppu/include/mbi_ppu.h:66，头hash
  32f52eeedc3136af775079aca437bcf5547b8459339c05197373e4fc557e1277
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 1e97e51e48acbe199dae56e6a1f847e3ba24aff9a22f4493be0fcab3b99175bf
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X接口知识卡：MBI_PPU_ReleaseChnFrame

接口 MBI_PPU_ReleaseChnFrame 的头文件声明：MBP_S32 MBI_PPU_ReleaseChnFrame(MBP_S32 ppuDev, PPU_CHN ppuChn, MBP_VIDEO_FRAME_INFO_T *frame); 条件编译是否启用及实际运行库导出需分别核实。

来源：workspaces/ipc-c5-rc.1.0/linux/mbp/mbi/ppu/include/mbi_ppu.h:66，头hash 32f52eeedc3136af775079aca437bcf5547b8459339c05197373e4fc557e1277

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
