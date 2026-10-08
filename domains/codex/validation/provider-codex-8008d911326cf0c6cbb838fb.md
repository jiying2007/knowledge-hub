---
id: provider-codex-8008d911326cf0c6cbb838fb
title: Codex 7.14.2 来源与运行采用验证
kind: validation
domain: codex
path: domains/codex/validation/provider-codex-8008d911326cf0c6cbb838fb.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:8008d911326cf0c6cbb838fb24344f60c2f97f7ac874f8798f35432da21d0641
  source_sha256: b57eaedcbb111dd4c8f900859e2e8ca80627f260d84bbf570c0109082da7c32a
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- domains/codex/validation/provider-codex-8008d911326cf0c6cbb838fb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/codex/validation/provider-codex-8008d911326cf0c6cbb838fb.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 从canonical ADK actual main e9fab289f98961922342fa32a4f629067a5a9e21/7.14.2导入，tree37b5e02a544cb6a650137b239b29a9322ba00f98、manifest
  blob b312a2d8341c0ac769f7ac4b4be4e29ffc7aab9c。真实main CI37395924472 attempt1的promotion evidence以固定官方issuer/workflow identity/trusted-root验签Verified
  OK；归档SHA2566179c9853e4
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Codex 7.14.2 来源与运行采用验证
related:
- indexes/obsidian-home.md
---

# Codex 7.14.2 来源与运行采用验证

从canonical ADK actual main e9fab289f98961922342fa32a4f629067a5a9e21/7.14.2导入，tree37b5e02a544cb6a650137b239b29a9322ba00f98、manifest blob b312a2d8341c0ac769f7ac4b4be4e29ffc7aab9c。真实main CI37395924472 attempt1的promotion evidence以固定官方issuer/workflow identity/trusted-root验签Verified OK；归档SHA2566179c9853e47059123f1ef15f40acf34a95f04b063b2a3f238599ea6f0f690e5匹配官方digest与release contract。

既有signed importer按plan/apply、fixture生成、consumer README刷新分别执行；42Skill、9Agent和四policy上游正文不变，版本/commit来源及consumer-owned基线同步。历史fixture、原许可证和全部profile/模型/权限/MCP配置保留。来源审计42/42一致；两个binding通过，本地3.8和3.11各342/342，通过build/doctor；作者自审明确非独立owner审查。

Codex PR46的9项托管检查全部通过后合并，actual main55ee271dc86926e0fe8192179f4c724ece54608e。明确命名stash保存后ff同步，再恢复五tracked用户修改，增删行与原备份相同，journal SHA256dd8fc6ec7088bf4bf606b98ccc9ef512aa7e64192b059c3970083c13c09cc373不变。用户改动未进入提交，stash/备份未清理。

actual source-to-live完整build/doctor/plan/dry-run/apply/check通过。team-collab767 managed，69项受管内容更新有原plan与备份，未改config/auth/session/memories。应用后344项测试与四profile smoke通过，74skills零错误零警告；diff0/missing0，drift changed0/stale0/unmanaged0。原plan输出和keep路径回读相符，配置hash保持。

actual build tree e7566d9525b52f5d06e63aa05ee901b480cb2bcb97ca359a35a23bca222fb7ac；plan hash69d9d9eb93d1760cea637c58ab11844abdc70e1d37aa63e31937ac7355682400；live managed state f382d336cbc36e5169861461ed0e4cecf50fa3ceb726cd6fabaf9b096e57e635。

本记录证明当前来源和受管运行资产采用，不推导owner/M5/产品或真实效果资格。无真实模型调用，评测仍只有工具及确定性fixture。根仓来源提升PR182独立等待托管终态，不能从本Codex结果推导根仓已合并或workspace总体release-ready。
