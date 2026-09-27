---
id: aispeech-agc-attribution-review-20260921
title: AISpeech AGC全零增益归因与候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-attribution-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: f951949f5a8ca19969af166b3c128eaa08c732107aa46bece1b4383a8ebcb191
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-attribution-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-attribution-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 全零增益40dB复现，默认关闭候选通过数值及小样本观测
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech AGC全零帧增益归因与默认关闭候选

本轮在现有AISpeech dirty基线上完成逐帧观测和候选验证。未提交、部署或启用默认。

## 确认的现象

1. fileid4原幅度交互路径：IFFT=0、overlap=0、output_gain=106次限幅计数。
   最终对齐输出满幅样点82个，口径不同：计数覆盖处理与零尾，限幅阈值及负端值也不同。
2. 默认AGC遇全零PCM，预处理输入峰值设-100dB，低输入目标为-60dB，目标增益40dB。
   NN增益推导的VAD在全零处仍可偏高，平滑策略允许增益逐渐上升至40dB。
   定向测试100帧全零且VAD为1复现40dB，输出仍全零；不声称静音自己产生了噪声。
3. AGC位于IFFT之后、overlap之前。CALL最终额外增益为1；交互仍使用outGain。

## 实现

新增SEVC_AGC_HOLD_SILENCE_GAIN，默认0。候选1在fXDb为全零专用-100dB sentinel时，
把目标增益上限设为当前增益，允许保持/下降，禁止继续上升。S16的1LSB非零峰值高于-91dB，
不会触发此条件。没有更改阈值、结构、NN VAD或公开接口。
它只作用全零帧，非零底噪和词首响度需要另外验证；不将候选启用为产品默认。

观测器支持--trace-agc，打印弱输入加噪声默认CALL的逐帧gain/input peak/VAD/linear gain。
三段摘要按对齐帧起点分组；AGC重叠窗使边界不是独立声学片段，max_step仅统计段内。
观测trace分支跑过fileid4的624帧，未归档PCM或完整会话日志。

## 小样本结果

沿用上轮fileid4、7、18、21及对应SHA256，输入构造完全相同。
默认与候选各48项组合；16个CALL组合的整段SI-SDR全部高于默认。
四样本平均输出SI-SDR，单位dB：

| 条件 | 默认 | 候选 |
|---|---:|---:|
| 原幅度，无注入噪声 | 8.802 | 11.252 |
| 原幅度，噪声突变 | 7.291 | 11.120 |
| 八分之一幅度，无注入噪声 | 1.839 | 6.096 |
| 八分之一幅度，噪声突变 | -2.527 | 2.824 |

16项中最小改善0.319dB。候选同时降低部分输出电平，不能等同听感或响度全面改善。
没有中文KWS、真实双麦/双讲、背景底噪和板级验收，不晋升默认。

## 验证与制品边界

- `rtk make -C modules/aispeech/tests run-agc-silence run-agc-window run-pipeline-fingerprint run-vad-status`退出0。
- silence测试补充恢复静音后，再以相同flags对默认/候选重编并运行，均退出0。
- ASan/UBSan直接instrument AGC，覆盖全零、1LSB、再次静音及Reset。
  默认全零增益40dB，候选0dB；候选已有非零增益返回全零后不再上升。
- 默认40,150帧窗口oracle、VAD、1000帧指纹通过；指纹16985685392395738340，memory315620。
- 默认`rtk make NC=1 modules/aispeech_lib_all -j4`退出0。
- 候选AGC独立ARM对象编译退出0，不能据此宣称候选完整ARM库或产品已经集成。
- `rtk git -C modules/aispeech diff --check`退出0。

候选观测直接编译AGC源码覆盖普通Host静态库对应对象；此宏仅AGC使用，无布局变化，
其他库对象复用同一基线。入口run-agc-hold-observation可复跑。
默认ARM静态库SHA256 143a3dcdc9ae3082856a4827d91787b32d058f02c59067f385ff16fffbfc1714。
默认ARM动态库SHA256 a27dd524e16d3f50131cc0ab0b60ead81328242b2f43128497df97b95819ede8。
候选ARM对象SHA256 3a5f290e4eceac599d01dda235e1cb8198e8db059aef6cf39c8e1d84618f4349。

本轮是targeted自审，不是独立听感评审。下一步增加不同静音长度、词首电平恢复、
非零连续低底噪、峰值变化与听感门禁；交互outGain限幅另作受控候选。
Runtime Control idle/null goal、required-artifact-missing按planning skill记not_applicable。
reusable_pattern: 区分零输入增益状态与输出噪声，单阶段控制变量试验。
promotion_candidate: false；do_not_promote_reason: 声学证据不足；owner_review: pending。
rollback_path: 保持宏0即禁用候选；移除本轮增量须保留先前AGC与其他dirty修复。
next_task_friction_reduced: 增益归因与候选矩阵已可复跑；reduced_by: trace/silence/hold-observation。
reduction_evidence: 定向100帧和96项观测。
