---
id: provider-llm-agent-47752ebe98d16c6e9c2adfa0
title: ADK与llm_agent信任边界及来源迭代审查候选
kind: audit
domain: projects/llm-agent
path: projects/llm-agent/archive/provider-llm-agent-47752ebe98d16c6e9c2adfa0.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:47752ebe98d16c6e9c2adfa0b390f7794d61c172b3e4fe3bc06050627e505922
  source_sha256: e6501682db2b136776c0e652d0ae1c36107a9f772f6f4f60eccf7aab7fc45cd6
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- audit
validation_refs:
- projects/llm-agent/archive/provider-llm-agent-47752ebe98d16c6e9c2adfa0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/archive/provider-llm-agent-47752ebe98d16c6e9c2adfa0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 日期2026-10-06，reviewing候选，仅AI工程审查与实际源码/部署证据，不创建owner或产品资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# ADK与llm_agent信任边界及来源迭代审查候选

日期2026-10-06，reviewing候选，仅AI工程审查与实际源码/部署证据，不创建owner或产品资格。

可复用结论：严格JSON reader必须与producer预算闭环，防止合法安装成功后receipt超限而不可回滚；safe descriptor的regular/NOFOLLOW/NONBLOCK检查防止叶节点链接/FIFO替换，目录descriptor相对遍历限制元数据范围，平台能力缺失failclosed且声明非原子/父目录边界。扫描工具rc1与rc>1必须区别，无界维护--apply退役属于MAJOR，报告应明确planned/appliedfalse。URL信任基于精确HTTPS authority/port与路径段，诊断不泄漏credentials/query；推广claims验证与实际签名准入分层，不能把宽松claims缺口夸大为完整签名绕过。

部署经验：所有consumer精确pins，包括专用validators和runtime binding，要同步前移并保持既有blob与强约束；source tests不能代替专用binding gate。部署前保留本机配置漂移，使用既有non-overwrite策略、同计划source/build/target预条件、实际dryrun和独立readonly复审；config/auth/session/memory/history不能因资产升级被意外覆盖。

公开证据：llm_agent PR183信任边界、PR184签名source推广，main ebacd77f50312b8551cf56fa26fe6446d8e93915；agent-dev-kit PR176、main2c5bd3574c660c5d71bd7e71502977f8cadcf0ad、immutable v8.0.0，mainCI37411676809及release37412113614成功，actualarchive SHA9712f4e43898727264d528b0a7051ae1c4d6074d39f1f5d7cf0062e471dbf291与API/signedevidence/releasecontract一致；CodexPR47/main4084f918f949a8b7969ac2c286f273712c046b2f。

验证结果：ADK支持三Python各98回归/30routing/wheel/audit通过；Root74回归、独立source审查通过；Codex候选两Python各342、实际恢复user修改后344及四profile smoke通过。实际team-collab受管部署完成，postcheck diff/missing/changed/stale/unmanaged均0，config/auth保留；history在会话期间变化，不能宣称其字节不变。真实模型未调用，没有模型收益量化。

独立复审真实发现并关闭producer预算Major及三个消费pin遗漏Major；移放文档恢复report预算，不扩大阈值或删除历史记录。参考baseline过期、历史M5/source不匹配、当前产品/owner资格与长期pilot仍NEEDS_REVIEW/failclosed，未刷新owner/date/certification或重标旧证据。组件发布、runtime本地conformance不能推导产品资格。

外部一手设计输入：Anthropic effective-harnesses-for-long-running-agents与harness-design-long-running-apps的增量交接/独立评价；OpenAI agent-evals的trace与workflow分层；SLSA1.2 verifying-artifacts的身份/来源/制品期望；MCP2025-11-25 security/experimental Tasks仅设计参考，不引入默认runtime。

后续验收：真实owner复审参考基线、独立补当前M5/pilot证据；按用户授权再安排真实模型成本/成功率测量，本轮继续仅工具/fixture。本文无raw session/log/core/binary/credential、设备标识或个人主体推断。
