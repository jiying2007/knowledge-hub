---
id: pcr02-aispeech-reference-delay-confidence-20260915
title: AISpeech 四轨 reference delay 置信度边界
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-reference-delay-confidence-boundary.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 433192102aaa12a140dad1184027664b6099f9d5ee418c6467ccc9e616e6b866
  temporary_source_retained: false
review_after: '2026-10-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- aec
- reference-delay
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-reference-delay-confidence-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-reference-delay-confidence-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-15'
updated_at: '2026-09-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-15'
manual_validation_pending: true
summary_zh: 补充四轨delay峰值置信度诊断，确认其可分层评估但不能直接设定产品参数。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AISpeech 四轨 Reference Delay 置信度边界

## 方法审查结论

四轨 Microsoft AEC Challenge 数据可以用于有 clean echo 与 clean near target 的远端 ERLE、双讲保护和显式仅近端回归。它可否决不安全的 AEC/RES 参数方向，但不能直接设置 PCR02 产品 reference delay、tap 或 AES 默认参数。

原始 evaluator 仅输出最佳 far-to-echo 相关系数，无法区分唯一峰与多个强替代峰。已增加 evaluator-only 字段：最佳峰、至少相隔 128 样本的次峰、二者 gap，以及最佳峰正负 64 样本的 local margin。

## 24 样本证据

- peak gap 小于 0.05 的 9 个样本，平均 far ERLE 为 1.986 dB，含全部 2 个负 ERLE 和全部 3 个负双讲 SI-SDR improvement。
- peak gap 0.05 到 0.10 的 5 个样本，没有负 ERLE/负双讲；平均 far ERLE 3.374 dB。
- peak gap 至少 0.10 的 10 个样本，没有负 ERLE/负双讲；平均 far ERLE 8.853 dB。
- 低 gap 仍含可接受的 fileid 25，因此 gap 是风险与置信度字段，不是删除样本或 runtime gate 的依据。

## 参数优化边界

- per-file delay sweep 的最佳方向相反：fileid 21/27 减小 delay 改善，fileid 59 减小 delay 退化。
- 固定 AES cap 与 AES DTD-only cap 虽改善部分失败双讲，但会伤害已冻结的弱近端起始反例。
- 因此在真实 AO/Codec/功放/机壳 reference 路径证据之前，不提升 SEVC_AEC_TAPS、reference delay、AES cap、DTD 状态或 headroom 候选。

## 可复跑与边界

- 24 样本 split、96 文件 SHA-256 inventory、manifest 与 evaluator 位于 modules/aispeech/tests/validation。
- 默认四轨 evaluator、manifest JSON、checksum inventory、公共头检查和 diff check 已通过。
- 严格 SLR28 quality gate、QIVW 唤醒率、SSC305 实时性和移动播放 HIL 仍是未闭环门禁。
- 本候选不包含原始音频、设备端点、客户数据、日志或凭据。
