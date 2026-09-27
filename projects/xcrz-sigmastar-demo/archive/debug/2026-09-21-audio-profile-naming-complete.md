---
id: audio-profile-naming-complete-20260921
title: 音频配置命名全面统一与验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-profile-naming-complete.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/api
  source_sha256: d95c34bc45630cf94236da7b797a2ed23238cc0607745d8401c15ee3ad1a6ba5
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-profile-naming-complete.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-profile-naming-complete.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 按模块规范统一类型函数宏诊断与测试命名，保留原构建配置，回归和产品链接通过
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频配置命名全面统一

2026-09-21，在当前开发路径完成，保留用户要求的原构建配置及无关dirty。

## 范围与命名
- API内部辅助函数统一为 _AUDIO_AiConfigTransitioning、_AUDIO_AiSetProfileLocked。
- API公开函数统一为 VSAPIAUDIO_AiSetProfile、AiGetProfileStatus、AiWaitProfileReady、AiSetRefDelaySamples。
- API公开类型为 VSAPIAUDIO_Profile_e、VSAPIAUDIO_ProfileStatus_t；tag为_AudioProfile_e和_AudioProfileStatus_t；枚举为AUDIO_PROFILE_VOICE/CALL，超时宏为AUDIO_PROFILE_READY_TIMEOUT_MAX_MS。
- HDI沿用本轮之前统一的VSHDIAI_Profile_e/ProfileStatus_t、SetProfile/GetProfileStatus/SetRefDelaySamples/NotifyEchoPathChange、AI_PROFILE_*及AI_ECHO_PATH_CHANGE_*。
- APP内部命令函数去除Speech；API诊断命令统一为diag.api.media.audio_profile.{set,get,wait}.run，注册项、返回项、元信息及帮助示例同步。
- 测试文件、Makefile目标、忽略项及PASS名称统一为audio_profile_test；旧生成测试程序移至临时目录保留。
- SDK状态字段stVad.speech表示语音状态，按原接口保留，不进行机械删除。

## 模块规范
- 阅读各模块AGENTS、development指南和api-development/hdi-development/app-development技能。
- 保留API公共函数VSAPIAUDIO_Ai前缀及内部_AUDIO_Ai前缀；局部变量使用u32Channel等项目类型前缀，测试参数使用enProfile/pstStatus等。
- 为新增API状态拷贝、AO回声路径通知分支补齐大括号；依据各模块.clang-format只格式化音频变更范围及新增测试，不格式化无关ToF工作。
- 类型数值、结构布局、超时和处理行为不变。源码符号和诊断命令改名，消费者应重编，不提供旧名称别名。

## 验证
- 当前源码及公共头、测试和相关应用扫描旧SpeechProfile/SpeechConfig/SpeechEchoPath/SpeechRefDelay/SPEECH_PROFILE/speech_profile/_AiSpeech：零匹配。
- 三模块doctor及check通过；hdi/api/app公共头检查通过。
- API全套Host回归通过（包含audio_profile_test）；为既有视频测试提供实际libyuv include路径。
- HDI/API/APP静态、动态库构建通过；nm检查三库没有含Speech的VSHDIAI/VSAPIAUDIO旧符号，HDI和API各4个新入口有定义。
- 当前开发路径 `rtk make NC=1 pcr02_app_all -j4` 成功；产品BuildID 21a7b80eee41e47f4dcaee27e6cd8202464c2f73，SHA256 3c9a9fc31d5716914ec70bfdf5a144ecf8e2a5028f776a3c9db4f3f162661251，大小288715988字节。
- 本轮未修改构建配置、ToF逻辑，未commit/push、未部署设备、未生成image/OTA；构建通过不等于新制品声学或设备验收通过。

本记录补充并取代先前分批命名记录中的旧API命名；作为project-specific reviewing candidate保存。
