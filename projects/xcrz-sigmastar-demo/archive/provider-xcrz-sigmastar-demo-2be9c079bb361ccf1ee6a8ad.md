---
id: provider-xcrz-sigmastar-demo-2be9c079bb361ccf1ee6a8ad
title: v34：切换归因与固定保护条件的收益上限
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2be9c079bb361ccf1ee6a8ad.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:2be9c079bb361ccf1ee6a8adc2a2c84eb67cc262501ffdcebe7decbf25b9c4c3
  source_sha256: b94f23ebdd457112c8a6e5264af9683ee81e4ccea9d8ee71a96df11d62b3037b
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2be9c079bb361ccf1ee6a8ad.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-2be9c079bb361ccf1ee6a8ad.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 冻结 v33 实际整数 PCM 和原生 AGC 轨迹，逐项核验 evaluation、模型、binary、input、trace 哈希。 所有非 output 轨迹和窗口相同，最终 PCM 精确指标重算严格匹配既有 precision
  报告。 诊断选择的输出切换邻域为校正非零权重开关当前及下一 hop；原生 IFFT 512、hop256， sevcPostOverlapProcess 仅保留前一窗口尾部，AGC 使用固定原生 driver。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 2be9c079bb361ccf1ee6a8adc2a2c84eb67cc262501ffdcebe7decbf25b9c4c3
---

# v34：切换归因与固定保护条件的收益上限

冻结 v33 实际整数 PCM 和原生 AGC 轨迹，逐项核验 evaluation、模型、binary、input、trace 哈希。
所有非 output 轨迹和窗口相同，最终 PCM 精确指标重算严格匹配既有 precision 报告。
诊断选择的输出切换邻域为校正非零权重开关当前及下一 hop；原生 IFFT 512、hop256，
sevcPostOverlapProcess 仅保留前一窗口尾部，AGC 使用固定原生 driver。

18：实际 DT -0.1962035720115054 dB；仅离线把切换邻域校正换回 native 后 -0.01373132659855969。
206：实际 target -0.2055006689704042；同样拼接后 -0.21273269184129306，稳定区贡献更明显。
550/831 的切换拼接结果分别 DT +0.010148/+0.005923；这些是离线诊断反事实，不能宣称候选通过。
切换区与稳定区的 target 投影改变量可加和；清晰说明没有因果连续性完整证明。

容量检查覆盖三个完整 24 例组：校正当前和前一 IFFT 都无非零 design weight 时，
该输出样点不可由系数改变；冻结 candidate 在所有这些样点与 native 完全一致。
让全部可修改 far 样点理想化为零，不可修改 far 样点能量仍构成总残差下界。
逐例收益上界取 dB 后按实际组均值聚合，近端真值先按 split near_scale 缩放后分类。
development24 的平均收益上限 0.1916952533260817 dB；
exposed24 的平均收益上限 0.33764530955895017 dB；
exposed-v27-24 的平均收益上限 0.3410125739385157 dB。
即使不限制系数也不考虑语音保护，这三个组仍无法达到 0.5 dB 门槛。
因此停止该 v33 guard 的系数重拟合；结论只适用于固定 guard、固定 native AGC 和当前两 hop 合成支持，
不能外推其他消回声机制或音频链路。

新 Host 工具 tail_pcm_transition_probe.py；五个独立数组控制验证邻域、投影加和、零差、
越界校正拒绝、无 eligible 零容量及半残差 3.0103dB 上限。help/dry-run 从 /tmp 验证通过。
首次测试 fixture 未包含 far-only 区段而被拒绝；补全独立 far/double fixture 后通过，未放宽工具输入条件。
全量 discovery 在新增第五控制之前运行112项，111通过、1项缺可选 stage probe binary 跳过；
后续最终验证须记录新鲜计数，不把未运行的可选 C 验证冒充通过。
生产默认、库、profile 与上层生命周期未在本轮修改；无 commit/push/deploy。

下一轮固定上一整 Feed 的瞬时 residual/echo 3:2 保护，沿用现有 DTD 的物理判据比例，
不要求平滑比值先越界，检查能否尽早避免风险校正并保留远端收益；先冻结机制、表和身份再实际 C 评估。
主声学目标未完成，累计预算200M/36h继续有效。
