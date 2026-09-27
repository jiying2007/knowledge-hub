---
id: audio-neutral-naming-final-20260921
title: 音频中立命名最终修订：保留原构建配置
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-final.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/hdi
  source_sha256: c7dd38351e23bd48cd551a4653587b9020ac52fa98f9096828896e45e1c61b56
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-final.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-neutral-naming-final.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 保留命名修正，按用户要求撤回include路径迁移，恢复原构建配置
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频接口中立命名修正

2026-09-21，按用户要求在当前开发路径执行。

- HDI类型标签 _AiSpeechProfile_e、_AiSpeechEchoPathChangeReason_e、_AiSpeechProfileStatus_t 改为 _AiProfile_e、_AiEchoPathChangeReason_e、_AiProfileStatus_t。
- AI_SPEECH_PROFILE_* 改为 AI_PROFILE_*；AI_SPEECH_ECHO_PATH_CHANGE_* 改为 AI_ECHO_PATH_CHANGE_*。枚举值、结构布局和运行行为不变；调用源码须使用新标识。
- API、HDI、APP调用方和父仓公共头同步更新。按用户后续明确要求，保留HDI lib.mk原有厂商头文件路径，撤回父仓build/build.mk新增条件块；构建配置恢复原基线，lib.mk仅有末尾换行差异。现有SEVC后端实现仍保留。
- 本记录为最终修订，取代先前记录中关于迁移厂商头文件路径及构建文件零厂商名称的描述。
- 类型标签和宏不含旧AiSpeech及AI_SPEECH_命名；HDI lib.mk原有aispeech路径按用户要求保留。相关应用消费者无旧宏或类型标签引用。
- HDI音频2个ARM对象、API/APP静态及动态库构建通过；audio_consumer_control_test与speech_profile_test通过；三模块边界检查、公共头一致性及父仓diff --check通过。
- 未修改独立ToF工作，未提交、未部署；本轮仅声明命名与定向构建验证。
