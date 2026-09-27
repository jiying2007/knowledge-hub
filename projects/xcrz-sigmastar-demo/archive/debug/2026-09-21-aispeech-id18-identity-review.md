---
id: aispeech-id18-identity-review-20260921
title: AISpeech样本18身份与电平核查
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-id18-identity-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: b1379c35f5c30b37e10c5b00267d93dc0797f684d1de744c845ee38be826e755
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-id18-identity-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-id18-identity-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 重生成与试听包一致，局部电平分析完成并提供同文件AB，听感原因待核
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 样本18原始输出身份与听感差异核查

用户反馈：id18默认版声音和噪声显得更小，其他对比无明显差异，已确认试听baseline-output.wav。
与哪份候选文件比较仍待确认。本轮保留反馈，不将文件能量方向等同于用户主观体验。

## 文件与重生成

检查试听包manifest和ZIP，两个output的SHA256及ZIP内字节都与本地一致。
重新显式编译HOLD_SILENCE=0，CAP_LOW_INPUT=0/1的两个观测器，分别重生成样本18
weak-noisy输出。结果与原试听包逐字节一致，未发现生成标签或文件被替换的问题。
- baseline SHA256: 2f0df0b7530a1ae56775686bd81ade46c1a504211521811967e94715f29d79ce
- candidate SHA256: 69a5e89a9f2b74e24b39c6af2eeb9bdebcad434b5200391069328708054750a5

两文件均159744样点、16kHz单声道PCM16。默认整体RMS486.730、峰值9930；
候选RMS87.630、峰值1240。候选整体RMS电平低约14.89dB。
逐秒候选相对默认：3～4s -18.839dB，4～5s -1.661dB，5～6s -0.184dB，6～7s -0.025dB。
0～3s和7s后文件为全零；此前打印的约-132dB只是能量公式正则底值，不是真实噪声。
624个16ms块中，候选有99块低超过1dB，没有高超过1dB的块。
所以当前文件数据不支持“原始默认输出电平更低”，但实际播放对象、播放器增益/归一化
或其他主观因素尚未核实，不能直接归因于任何一项。

## 同文件原始A/B

新工件/tmp/aispeech-id18-raw-A-baseline-B-candidate-20260921.wav，8.4秒。
两段均截取原输出3.1～6.8秒，不做增益、RMS匹配或归一化。
- 0～3.7秒：A，baseline。
- 3.7～4.7秒：全零间隔。
- 4.7～8.4秒：B，candidate。
逐字节核验A/B分别等于原文件对应片段，格式和134400总样点通过。
SHA256: 3eac2f39776f099aac84cfc77695c2eab6ffa726996844d1b9bc185b26183062。
用同一文件减少逐文件播放设置差异；仍不能排除播放器动态处理，也不构成独立听感通过。

本轮未修改源码、算法或默认参数，候选保持关闭。直接重编和重生成退出0，
只读Python能量/身份/ZIP比对退出0，git diff --check通过。未部署或发布。
用户比较对象通过异步文本问题请求确认，没有据未答复推定原因。
Runtime Control idle/null goal缺会话制品按既有planning规则单列not_applicable。
reusable_pattern: 听感与能量方向不一致时先核对文件、重生成和局部时间线，再制作同文件AB。
promotion_candidate: false；do_not_promote_reason: 主观方向待核且设备声学门禁未完成；owner_review: pending。
rollback_path: 本轮仅新增/tmp可审查工件，无源码回滚需求。
next_task_friction_reduced: 不需在两个播放器间切换；reduced_by: 8.4秒原始AB；reduction_evidence: 片段逐字节一致。
