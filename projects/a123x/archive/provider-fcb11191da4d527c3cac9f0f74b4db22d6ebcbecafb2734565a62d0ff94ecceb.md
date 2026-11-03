---
id: provider-fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb
title: A123X独立知识卡：signed文件与安全启动生产验签
kind: runbook
domain: projects/a123x
path: projects/a123x/archive/provider-fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb
  source_sha256: d08620a364e96e89691f138dfbbdd5b82705fa280a0038b9a7b8faaec20314e9
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
- question
validation_refs:
- projects/a123x/archive/provider-fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/archive/provider-fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-23'
updated_at: '2026-10-23'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-23'
manual_validation_pending: true
summary_zh: A123X知识卡v2；2026-10-23 RC1候选；文件名signed或使用SDK测试签名不证明产品安全启动。ROM信任根、bootloader/镜像验签、rootfs完整性、OTA签名及版本策略分别取证。C3 Secure
  Boot0.4不能直接作为A123X RC1不可逆efuse烧写规程。 来源：integration/SECURITY.md；C3 SDK Documents/IPC SDK Secure Boot Quick Start0.4
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: fcb11191da4d527c3cac9f0f74b4db22d6ebcbecafb2734565a62d0ff94ecceb
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# A123X独立知识卡：signed文件与安全启动生产验签

文件名signed或使用SDK测试签名不证明产品安全启动。ROM信任根、bootloader/镜像验签、rootfs完整性、OTA签名及版本策略分别取证。C3 Secure Boot0.4不能直接作为A123X RC1不可逆efuse烧写规程。

来源：integration/SECURITY.md；C3 SDK Documents/IPC SDK Secure Boot Quick Start0.4

适用边界：本地RC1源码/文档快照；reviewing候选，未执行新的设备验证。来源变化须刷新本条，不以目录或其他知识卡替代其证据。
