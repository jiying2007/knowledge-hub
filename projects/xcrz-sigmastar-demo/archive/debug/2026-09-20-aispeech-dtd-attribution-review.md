---
id: pcr02-aispeech-dtd-attribution-review-20260920
title: AISpeech DTD 原始判决、保持和无效历史状态归因
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-attribution-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: bfb447ca5efc921f35edb21e3f87b71e366d5f6fa362c87cb7be0c0581c51bea
  temporary_source_retained: false
review_after: '2026-10-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-attribution-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-attribution-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-20'
updated_at: '2026-09-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-20'
manual_validation_pending: true
summary_zh: 拆分DTD原始判决、保持和旁路历史状态；明确Room002评分来源，14组评估器对照保持原声学指标和退出码不变。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech DTD 原始判决、保持和无效历史状态归因

- captured_at / last_verified: 2026-09-20
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- Review Target: working-tree；HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1。
- Reviewer Independence: author-self-review。
- 本轮只修改评估器、共享归因 helper、测试入口和说明，未修改算法库源码或产品默认值。

## 目标与确认原因

上一轮条件释放候选仍不能使 Room002 的 6.849% 激活占比通过 5% 门限。本轮逐帧区分该统计量的来源。
Room002 原始比例判据在初始帧 0～2 为真，帧 3 起为假；评分从第 8 帧开始，仍包含第 8～9 帧的保持。
双讲结束后第 160 帧原始判据为真，但 512-sample 分析窗由上一跳和当前跳各 256 samples 组成，此时仍含近端语音。
帧 161～167 原始判据均为假，但 DTD 仍处于保持；第 168 帧才首次观测到未激活。

因此 10 个评分激活帧 = 2 个启动保持 + 1 个混合窗口判决 + 7 个双讲后保持。
“Room002 存在持续稳态原始误判”不符合本次证据；但保持时长是否满足产品需求仍需另外验收，不据此修改门限或宣称通过。

## 已落地的观测契约

SLR28 和四轨评估器共享 tests/sevc_dtd_attribution.h，输出 dtd_attribution_version=1 和 far_dtd_attribution：

- observed/unobserved：当前 AES 处理且参考活跃并可安全计算 / 其余无法归因。
- raw_positive：当前原始比例判据为真，包含 attack 尚未完成的帧。
- active_raw：已激活且当前原始判据为真。
- active_hold：已激活但原始判据为假。
- active_unobserved：无有效观测时仍报告历史激活；不视为新的判决或保持。
- active_mixed_window：有效激活且分析窗覆盖上一跳近端标签，是交叉标签，不可重复累加。

必须满足 observed+unobserved=原远端观测帧数，以及 active_raw+active_hold+active_unobserved=原激活帧数。
原误激活率、评分区间、门限及退出码不变。该 helper 不参与音频控制。
SLR28 同时报告双讲结束后首次有效未激活的 clear_found/clear_frames；没有有效观测时不把 0 当成立即释放。
四轨 mixed-window 基于既有活动阈值标签，不宣称精确语音边界。

## 结果

| 默认场景 | 远端观测帧 | active_raw | active_hold | active_unobserved | active_mixed_window |
| --- | --- | --- | --- | --- | --- |
| Room001 | 146 | 1 | 8 | 0 | 1 |
| Room002 | 146 | 1 | 9 | 0 | 1 |
| path-change | 138 | 1 | 10 | 0 | 1 |
| reset-stress | 138 | 1 | 10 | 0 | 1 |
| 四轨 fileid 7 | 199 | 9 | 21 | 0 | 0 |
| 四轨 fileid 4 | 297 | 52 | 102 | 31 | 1 |
| 四轨 fileid 25 | 391 | 44 | 115 | 0 | 1 |

Room002 默认与条件释放候选均在 8 帧后首次有效未激活。Room001 的候选为 4 帧，默认为 8 帧。
fileid 4 的 31 个旁路历史激活帧表明：旧综合指标混合了原始判决、保持和无效旧状态，不能全部解释为当前误判。
下一轮应优先分析 fileid 4 有效原始判决的来源，而非继续围绕 Room002 的综合占比盲目缩短保持。

## 验证与保持项

- `rtk make -C modules/aispeech/tests run-dtd-attribution` 通过；ASan/UBSan 覆盖严格比例边界、attack、保持、混合窗、旁路历史和乘法范围失效。
- 原有 quality-metrics 测试重新编译并通过 ASan/UBSan。
- 默认/候选各 4 个 SLR28 场景和各 3 个四轨样本，共 14 组旧/新评估器对照。全部旧声学字段与退出码保持相同；SLR28 仅排除计时字段比较。
- 所有 14 组的计数守恒成立。默认严格门禁依然失败；条件释放仍只有 Room001 通过。
- 算法库未重建且 hash 不变；不需要把评估器修改表述为新的 ARM 或设备验证。
- 子仓 diff --check 通过。未提交、推送、部署或修改原始音频。

## 身份与限制

- 默认 Host lib SHA256: ac5b48ae8186d6e7b233a0fd1caadc25f3d8471dac1844ff4ed070b738d3ecef
- 候选 Host lib SHA256: 0f36c60965d6dbf6e382950cb1fc6152427da29ca46753bf783c40fa19787027
- attribution helper SHA256: 4c124e931d88fa8bee0f7446b897b9b0708a0dc6275cb5e248d4d05c8b5f427a
- attribution test SHA256: 2b0627042577eac96c29fb9fcb957428b4164ed06bb52e9d9ec39f471f387d58
- quality evaluator source SHA256: 0568d0c30307503c536eaac6a1d600503e7e399f2ba7a0965d6943ca65f67ad1
- challenge evaluator source SHA256: bc0002499e2da4314a28df4548808802b34a116c535b7dbf99036b398a23b28c

这是有限样本的诊断归因，不是新的 DTD 准确率验收，也不是板端或 QIVW 结果。
记录为 reviewing；只保留脱敏结论，不归档原始音频或逐帧日志。
