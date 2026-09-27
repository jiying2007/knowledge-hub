---
id: aispeech-agc-audibility-review-20260921
title: AISpeech AGC清晰度反馈与补偿边界
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-audibility-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 7e2312b1668bb1a2da9403610ed71594ebf007d1179d79e62346fd491c7f9d94
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-audibility-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-audibility-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 记录局部清晰度正反馈，固定补偿在12项超限，不启用全局补偿
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AGC 候选清晰度反馈与固定补偿边界

用户已明确在同文件原始AB中，样本18的B候选声音更小且更清晰。
将其保存为本片段正向主观反馈；其他场景此前无明显差异，不能扩为全场景听感通过。
本轮仅增加观测器电平审计和试听工件，没有修改算法或默认。CAP_LOW_INPUT和HOLD_SILENCE均为0。

## 声音边缘能量观察

沿用8样本整段默认/候选192项。根据原始干净参考256样点帧RMS>=64形成连续段，
仅取>=3帧的段，汇总其前/后48ms输出相对缩放目标能量。3～5帧短段的两窗口重叠，
不视为独立样本；这不是人工逐词标注。加噪声条件输出能量包含噪声，不据此判断语音完整。
弱输入无注入噪声时，8样本候选头48ms相对参考约+1.0654～+5.9114dB，
尾48ms约-0.8075～+5.7811dB。聚合结果没有普遍起始欠电平，但不能证明所有词首/尾音无损。

## 固定补偿风险

将原输出乘10^(dB/20)并舍入，审计是否超出S16[-32768,32767]。
只计算，不实际修改算法输出；这是预测越界样点，不是某个已有限幅器的计数。
32个候选CALL组合：
- +3dB在12项超限，合计733样点。
- +6dB在12项超限，合计13570样点。
- 超限均在原幅度场景；小音量片段无超限不足以推广全局补偿。
样本21正常干净输出由独立Python读取既有WAV复算，+3/+6分别15/458样点，与C观测器一致。
结论：不引入无保护全局增益来补偿候选音量；设备最终音量和峰值余量需要独立验证。

## 局部试听对照

工件/tmp/aispeech-id18-candidate-0-3-6dB-20260921.wav，13.1秒，单声道16k PCM16。
各段均来自候选原输出3.1～6.8秒：
- 0～3.7秒：候选原音0dB。
- 3.7～4.7秒：静音。
- 4.7～8.4秒：候选+3dB。
- 8.4～9.4秒：静音。
- 9.4～13.1秒：候选+6dB。
仅此低电平片段的三段均无削波，逐样点核验原段和增益转换；总209600样点。
SHA256 5652d95d2b29bbea93c7fe043d989749ae0bd518ebcf959f0972bf424a197eec。
这三段都不是默认baseline，不重新做RMS归一，只用于音量偏好评估。

## 验证和边界

默认/候选观测器直接-O2 -Wall/-Wextra/-Werror构建通过（仅屏蔽既有unused parameter），192项退出0。
新逻辑与AGC直接ASan/UBSan构建通过；候选样本4完整12组合运行退出0，验证越界审计分支，
其他静态库未整体instrument。独立导出WAV计算、补偿文件格式/样点/无削波检查通过。
git diff --check通过，未重建ARM（本轮测试/文档改动）、提交、部署或发布。
结果/tmp/aispeech-agc-audibility-results-20260921.json，无原始会话/音频进入Hub正文。
主代理自审与独立计算实现，不冒充全场景独立听评；用户反馈仅绑定样本18同文件AB。
Runtime Control idle/null goal缺会话制品按planning skill单列not_applicable。
reusable_pattern: 清晰度正反馈与音量补偿需分开判断，单样本有余量不等于全局可加增益。
promotion_candidate: false；do_not_promote_reason: 设备响度/峰值和中文验收缺失；owner_review: 样本18用户反馈已记录。
rollback_path: 移除本轮观测器/文档增量即可，算法未改。
next_task_friction_reduced: 可复跑头尾能量和固定补偿越界审计；reduced_by: edge_level/fixed_gain_audit。
reduction_evidence: 733/13570越界计数及独立15/458复算；下一步保留清晰度收益并验证设备实际音量。
