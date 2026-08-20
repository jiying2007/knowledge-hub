---
related:
- projects/x5-rdk/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: x5-rdk-immutable-vendor-manifest-amendment-20260815
title: X5 供应商资料不可变清单与修订协议
kind: project-current
domain: projects/x5-rdk
path: projects/x5-rdk/current/candidates/2026-08-15-immutable-vendor-manifest-amendment.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 来自 X5 vendor-docs 不可变资料清单治理的脱敏工程总结
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
review_after: '2026-11-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- vendor-docs
- immutable-manifest
- governance
validation_refs:
- projects/x5-rdk/current/candidates/2026-08-15-immutable-vendor-manifest-amendment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/x5-rdk/current/candidates/2026-08-15-immutable-vendor-manifest-amendment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-15'
updated_at: '2026-08-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-15'
manual_validation_pending: true
summary_zh: 供应商资料清单默认不可覆盖；仅通过显式修订模式、身份锁定、原子替换、评审与 CI 门禁纠正元数据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 供应商资料不可变清单与修订协议
---

# X5 供应商资料不可变清单与修订协议

## 摘要

供应商资料清单一旦用于 SDK 交接，就应被视为来源身份记录，而不是可重复生成的缓存。默认行为必须拒绝覆盖；确有元数据错误时，只能通过显式修订协议生成可审查的新版本。

## 不可变身份

每份 release 清单至少绑定：

- SDK/release 标识；
- 归档日期与来源包身份；
- 文件相对路径、大小和摘要；
- 生成工具版本或提交点；
- 资料所有者和复核状态。

资料二进制、私有下载地址、认证信息和原始下载日志不进入源码仓或 Knowledge Hub；清单只保存必要的可验证元数据。

## 默认生成协议

1. 目标清单不存在时才允许首次创建。
2. 目标已存在时默认 fail-closed，打印冲突路径和显式修订入口，不做静默覆盖。
3. 使用同目录临时文件完成生成、结构校验和摘要复核，再原子替换目标；失败时保留旧清单。
4. CI 校验 schema、路径安全、重复项、排序稳定性和既有 release 未被非授权改写。

## 显式修订协议

仅当清单元数据有误且资料载荷身份未变化时启用 `amend-existing` 等显式模式：

1. 锁定 SDK 标识、归档日期和来源包身份，不允许借修订切换 release。
2. 生成旧版与候选版的字段级差异，说明修订原因、影响范围和验证人。
3. 由 CODEOWNERS 或等价审批规则复核；CI 必须证明未修改禁止字段且载荷摘要仍一致。
4. 以普通提交保留历史，不 force-push、不重写已发布 tag。

若资料载荷本身变化，应创建新的 release 清单或明确的新归档身份，而不是修订旧身份。

## 风险与回退

- “可重复生成”不代表“可安全覆盖”，工具升级、遍历顺序和环境差异都可能造成无意漂移。
- 原子替换只解决半写文件，不替代身份锁定、评审和版本历史。
- 修订失败或验证不完整时保持旧清单有效，候选文件不得作为构建输入。

## Review

- owner：leiwenjun
- review_after：2026-11-15
- 下一次复核：修订权限、锁定字段、CI 负向用例、CODEOWNERS 覆盖范围与历史 release 防篡改证据。
