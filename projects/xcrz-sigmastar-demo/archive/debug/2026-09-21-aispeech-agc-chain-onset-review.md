---
id: aispeech-agc-chain-onset-review-20260921
title: AISpeech AGC整链起始验证与候选拒绝
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-chain-onset-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 5b229ea88416ef924b6efd93a930d0bb1e9d4841c1df5dbb32dd17479c50a0e5
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-chain-onset-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-chain-onset-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 64项整链验证发现起始回归及微幅背景收益消失，拒绝候选晋升默认
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AGC 全零保持候选整链起始验证：拒绝晋升默认

本轮仅扩展观测器和测试入口，未改算法或默认配置。沿用fileid4、7、18、21
干净标记近端文件及此前归档SHA256，双麦复制/reference零，非真实阵列或双讲。

## 方法

`--onset-probe`按原始样点abs>=256首次越阈的帧边界裁剪，取最多2秒，语音幅度除8。
不是人工标注词首。80帧全零CALL预热后，先注入20或200帧背景，再加入语音。
背景为种子193的LCG，均匀整数[-B,B]，B=0/1/4/16；持续覆盖前段、语音与1024样点尾部。
CALL按512样点对齐。默认/候选各32项，总64项。

记录NN输出复数频谱全零帧、AGC输入全零帧（-100dB专用标记）、
全零时gain实际上升帧、前160ms输出/目标能量比、片段SI-SDR。
这些全零计数不是候选分支触发计数。前段第一帧全零可能来自历史FIFO。

## 结果

| 背景B/LSB | 8对场景平均SI-SDR变化dB | 最差变化dB |
|---|---:|---:|
| 0 | +8.2294 | -1.0566 |
| 1 | +0.00004 | 0.0000 |
| 4 | +0.00001 | 0.0000 |
| 16 | +0.07439 | +0.0002 |

纯零平均收益掩盖负例：样本18前段20帧时默认3.1728dB、候选2.1163dB；
前段200帧时默认3.1729dB、候选2.1163dB。两项约-1.06dB。
样本4纯零前段则约+15.84dB，样本7约+16.69dB，样本21约+1.44dB，效果明显依赖输入。
候选纯零场景前160ms输出/目标能量比4.1875～5.5241dB，但不能据此认定词首听感通过。

所有非零背景场景前段NN和AGC仅1帧全零；语音区两者全零帧均0/125。
候选在1/4LSB背景下收益几乎消失；16LSB最多约0.2061dB，主要是初始状态差异，
不能视为持续噪声门。候选全零gain上升计数为0符合设计，但不代表声学效果合格。

## 决策

拒绝当前SEVC_AGC_HOLD_SILENCE_GAIN候选晋升默认，维持宏0；保留默认关闭实现与负例。
不针对fileid18调整参数。下一方向审查非零低输入增益目标与NN增益代理VAD的耦合，
并先确定响度恢复/噪声放大/词首保护的联合指标。当前候选的纯零局部收益不足以推广。

## 验证

`rtk make -C modules/aispeech/tests run-agc-chain-onset`退出0。
观测器和AGC直接启用ASan/UBSan，64项无错误；静态库其他算法未整体instrument。
直接-O2构建观测同样完成64项，统计保留/tmp/aispeech-agc-chain-onset-results-20260921.json。
`rtk git -C modules/aispeech diff --check`通过。最初-Werror遇厂商AGC两个unused parameter，
仅为测试编译加-Wno-unused-parameter，其余-Wall/-Wextra/-Werror保留，不修改厂商无关代码。
退出0是执行/数值检查通过，不是候选声学通过；声学晋升结论明确为拒绝。
无ARM重建需求（本轮测试/文档变更），未提交、部署或生成image/OTA。
主代理targeted自审，无独立听感或中文HIL。
Runtime Control idle/null goal、缺会话制品按planning skill单列not_applicable。
reusable_pattern: 候选平均收益必须同时检查逐样本负例与微幅非零输入。
promotion_candidate: false；do_not_promote_reason: 起始片段回归和非零噪声收益不足；owner_review: pending。
rollback_path: 默认宏保持0；仅反向本轮观测器/Makefile/README增量可移除测试，不回退其他dirty。
next_task_friction_reduced: 64项失败矩阵可复跑；reduced_by: run-agc-chain-onset；reduction_evidence: 样本18负例和背景1/4LSB收益失效。
