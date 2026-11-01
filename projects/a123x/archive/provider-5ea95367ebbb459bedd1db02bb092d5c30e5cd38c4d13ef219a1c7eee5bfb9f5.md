---
id: provider-5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5
title: A123X：cma_alloc和dma_alloc_coherent的size单位相同吗
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5
  source_sha256: 9f804af544aab43663a8f9189f937ae5ee62f087f2e8961981d8c374e65e9ff7
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
- 内存DMA
- engineering-answer
validation_refs:
- projects/a123x/archive/provider-5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: cma_alloc的count按页数计，align表示以页为基准的2次幂对齐阶；dma_alloc_coherent的size按字节计。两者资源类型和释放接口不同，必须记录原分配尺寸并匹配释放。DMA API返回的DMA
  handle不能未经核实当CPU物理地址使用。手册对默认池与地址的简化描述应以当前内核实现复核，不把NULL参数示例当通用可用契约。 适用：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。
  来源：downloads/Kernel/CMA User Guide (0.1).pdf；PDF物理页 7；SHA256 b77a917acaca039209a40228ecd36bd041e21d961c6c5c0e3eed5afd7ff2e84b
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 5ea95367ebbb459bedd1db02bb092d5c30e5cd38c4d13ef219a1c7eee5bfb9f5
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# cma_alloc和dma_alloc_coherent的size单位相同吗

cma_alloc的count按页数计，align表示以页为基准的2次幂对齐阶；dma_alloc_coherent的size按字节计。两者资源类型和释放接口不同，必须记录原分配尺寸并匹配释放。DMA API返回的DMA handle不能未经核实当CPU物理地址使用。手册对默认池与地址的简化描述应以当前内核实现复核，不把NULL参数示例当通用可用契约。

适用边界：供应商通用驱动手册方法；A123X实际内核版本、DTS、节点存在性须与当前制品核对，示例地址和芯片参数不作为当前板配置。

证据：downloads/Kernel/CMA User Guide (0.1).pdf；PDF物理页 7；SHA256 b77a917acaca039209a40228ecd36bd041e21d961c6c5c0e3eed5afd7ff2e84b

状态：2026-10-24整理的reviewing知识候选；原文阅读与内容核验不等于设备实测或生产放行。操作建议尚未在设备执行；具体写操作应在目标、恢复路径与权限明确后实施。
