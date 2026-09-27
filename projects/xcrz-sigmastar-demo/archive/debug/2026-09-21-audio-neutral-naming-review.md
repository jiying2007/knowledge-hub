---
id: audio-neutral-naming-review-20260921
title: 音频接口中立命名修正
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/hdi
  source_sha256: 2abd04e1a34994cfd078f4614def8bf2bc2f1095c69b8ee7dc4be5feda6a4c64
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- audio
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 移除上层厂商名称和AI_SPEECH宏前缀，厂商构建路径归产品层，定向验证通过
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频接口中立命名修正

2026-09-21，按用户要求在当前开发路径执行。

- HDI类型标签 _AiSpeechProfile_e、_AiSpeechEchoPathChangeReason_e、_AiSpeechProfileStatus_t 改为 _AiProfile_e、_AiEchoPathChangeReason_e、_AiProfileStatus_t。
- AI_SPEECH_PROFILE_* 改为 AI_PROFILE_*；AI_SPEECH_ECHO_PATH_CHANGE_* 改为 AI_ECHO_PATH_CHANGE_*。枚举值、结构布局和运行行为不变；调用源码须使用新标识。
- API、HDI、APP调用方和父仓公共头同步更新；模块中厂商头文件路径从HDI lib.mk移到父仓build/build.mk的HDI后端构建配置。现有SEVC后端实现仍保留，本次不声称已完成整个算法插件化或后端解耦。
- 忽略大小写扫描三模块非生成源码、构建文件和公共头，无aispeech及AI_SPEECH_残留。相关应用消费者也无旧宏或类型标签引用。
- HDI音频2个ARM对象、API/APP静态及动态库构建通过；audio_consumer_control_test与speech_profile_test通过；三模块边界检查、公共头一致性及父仓diff --check通过。
- 未修改独立ToF工作，未提交、未部署；本轮仅声明命名与定向构建验证。
