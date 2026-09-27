---
id: aispeech-agc-onset-review-20260921
title: AISpeech AGC起始恢复与微幅输入边界
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-onset-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 4be0171a29e1d7c650ad6002ea267361e4794925033a09059ba0b969fb0cd0fb
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-onset-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-onset-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 96次控制矩阵通过，全零候选减少过冲但不解决非零微幅增益积累
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AGC 全零保持候选的起始恢复与微幅输入边界

本轮新增控制变量回归，未改算法源码、参数或默认宏。沿用上轮AGC默认关闭候选。
测试入口 `rtk make -C modules/aispeech/tests run-agc-onset` 退出0，直接对AGC源码
启用ASan/UBSan，默认/候选各48项，共96次运行。diff --check通过。

## 矩阵与含义

前段长度0/1/20/200帧；前段幅度0/1/16LSB；前段VAD为0或Q24的1；
后段幅度64或1024LSB、VAD为1、160帧。PCM为正负交替确定性样本，
用于隔离AGC曲线，不是语音，也不是实际随机背景噪声。每帧处理512样点，
沿用产品256样点hop折算16ms/帧；阶段测试未走overlap。

当前这两个后段幅度的稳态目标均为+6dB。稳定时间按最后一次偏离目标±1dB
之后的帧索引计算，不使用瞬时首次穿越。能量统计取前10帧；所有运行
检查输出相位符号、160帧内稳定，无Sanitizer错误。

## 结果与取舍

前段200帧全零、高VAD，随后幅度64LSB：

| 指标 | 默认 | 候选 |
|---|---:|---:|
| 前段结束增益dB | 40.000 | 0.000 |
| 起始第一帧增益dB | 38.802 | 1.778 |
| 前160ms能量增益dB | 35.004 | 4.792 |
| 稳态±1dB稳定时间 | 98帧/约1568ms | 5帧/约80ms |

后段1024LSB时，默认第一帧受峰值目标限制到27.103dB，稳定需86帧；
候选仍第一帧1.778dB、5帧稳定。没有出现±32767输出端点。
候选减少起始过冲，但首帧比稳态低4.222dB，前160ms平均比稳态低约1.208dB。
不能从这些合成阶段结果推导真实词首响度无损。

48对匹配场景中仅6对输出指纹不同，均为前段全零且高VAD、非零持续时间。
其他42对一致，其中32对是非零微幅前段。
1LSB前段200帧且高VAD时，两版本均积累30.309dB增益，随后64LSB首帧29.452dB，
稳定需88帧。16LSB前段增益约6.227dB，后续已经在稳态容差内。
这确认全零保持候选不解决连续非零微幅输入的增益积累。

## 决策与复跑

候选继续默认关闭，仅作为全零场景候选保留；不扩大为通用噪声门，不盲调低输入阈值。
下一步应在整链真实语音起始和连续微幅随机噪声上观测NN输出全零比例、候选触发率、
词首电平及听感。单阶段VAD由测试显式控制，不声称实际模型会在所有底噪条件输出高VAD。
未进行ARM重建（本轮只有测试/文档变更）、设备部署、提交或发布。
主代理targeted自审，不声称独立听感审核或产品就绪。
完整96行统计保留/tmp/aispeech-agc-onset-results-20260921.json，无原始录音/会话日志归档。
Runtime Control idle/null goal，缺会话制品按planning skill记not_applicable。
reusable_pattern: 以稳定带最后越界定义恢复时间，分开纯零和微幅非零。
promotion_candidate: false；do_not_promote_reason: 真实词首与底噪门禁缺失；owner_review: pending。
rollback_path: 仅移除本轮测试与Makefile/README增量，保留其他dirty；产品默认无变化。
next_task_friction_reduced: 96次控制矩阵可复跑；reduced_by: run-agc-onset；reduction_evidence: 6对不同/42对相同的指纹对照。
