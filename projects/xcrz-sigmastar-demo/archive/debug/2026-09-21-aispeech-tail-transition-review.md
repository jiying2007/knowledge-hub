---
id: aispeech-tail-transition-review-20260921
title: AISpeech NR NN 过渡与弱语音观测
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-tail-transition-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 61198cb264d41c27721a788331e9a6f4d00a0337bae30388e98bcaa45aac2ff4
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-tail-transition-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-tail-transition-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 过渡回归通过，48项弱语音对照提示下一步审查AGC时变增益
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# NR/NN 过渡验证与弱语音观测

本轮只新增测试与观测入口，未改算法参数或默认路径。基线 AISpeech
9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加现有 dirty；未提交/部署。

## 过渡数值验证

sevc_tail_transition_regression.c 分别对真实 NR/NN 阶段执行弱频谱80帧、
强频谱80帧、弱频谱80帧、静音80帧。先污染一个实例97帧再Reset，与新实例
逐样点对照，同时检查相位符号、上下界、历史帧对应和尾部清零。
NR/NN源文件启用ASan/UBSan，模型实现和其他静态库代码没有整体instrument。
全部通过。NN当前有1帧频谱历史，静音输入后按这一延迟排空；NR无阶段帧延迟。
合成弱频谱衰减NR约2.5dB、NN约14dB，不能解释为弱语音效果。

## 公开近端真值观测

现有evaluation split中近端干净标记的fileid4、7、18、21，直接取nearend_speech，
不混入原数据的echo/mic。原幅度与除8幅度，各自无噪声/中间三分之一白噪声突变。
噪声为seed91的LCG，幅度[-512,511]。双麦复制同一信号，reference为零。
80帧预热，1024样点零尾，按NR256/CALL512样点延迟对齐。
每样本对照交互NR、默认CALL NN+AGC、仅测试实例旁路AGC，共48项。
未改公共API或库默认；不把诊断旁路当发布候选。

弱输入加噪声突变，四样本整段SI-SDR相对输入平均变化：

| 路径 | 平均变化dB |
|---|---:|
| INTERACTION_NR | -0.175 |
| CALL_NN_AGC | -2.004 |
| CALL NN旁路AGC诊断 | +5.341 |

fileid4原幅度交互输出满幅样点82个，除8后0；默认CALL这两种输入满幅计数均0。
满幅不等价于已定位削波来源，需后续分级clip counters。
弱噪声默认CALL输出/干净目标能量比10.721～21.860dB，旁路AGC对照为-1.617～0.979dB。
输入没有响度归一，噪声幅度固定，四样本输入SI-SDR差异很大；均值仅本小样本描述。

结果支持优先审查AGC时变增益、噪声放大和恢复速度；不证明AGC应关闭。
时变增益会降低整段SI-SDR，必须结合逐帧统计、响度和听感；这里没有独立听感评审。
无噪声输入SI-SDR极高只是参考与自身一致及误差正则项；不能视作实际声学质量分。
这不是中文唤醒、真实双麦空间声学、双讲或HIL验收。

输入SHA256：
- 4: f7fb3fef780512e8f22c9d95a6ab1b2266278fa02ef10c9fb9d030bfd01b56e4
- 7: d9bf284f471e60d1b852b0f7c93e886d4d877f4806a140291156c45e953a1756
- 18: 186626cb0a375e0c4acc93368286061c6dd42cdb273ad1e2b643845f336348aa
- 21: bd8eeea006f6270a4220cff8748da7bf51f2799df9577ec186889a9a94e2ab39

## 可复跑与边界

命令：`rtk make -C modules/aispeech/tests run-tail-transition run-tail-audio-matrix`。
直接编译观测器带-Wall -Wextra -Werror通过；4个样本48组合均退出0。
退出0表示运行成功，不是声学门禁通过。不存在输入文件退出2，避免空结果假通过。
`rtk git -C modules/aispeech diff --check`通过；本轮不需ARM重建，未生成产品制品。
48项会话指标保留在/tmp/aispeech-tail-observation-20260921.json，无原始音频归档。

主代理自审测试边界，非独立人员审查。后续应补AGC逐帧gain/VAD、前后噪声区间、
峰值/限幅归因，然后才比较保持音量恢复能力的最小候选；不要单凭整段SI-SDR取消AGC。
Runtime Control idle/null goal，缺会话制品按planning skill单列not_applicable。
reusable_pattern: 状态测试与带真值观测分离；promotion_candidate: false。
do_not_promote_reason: 小样本诊断；owner_review: pending。
rollback_path: 仅反向本轮两个测试文件和Makefile/README增量，保留其他dirty。
next_task_friction_reduced: 弱语音AGC归因矩阵已可复跑；reduced_by: run-tail-audio-matrix。
reduction_evidence: 48项观测及NR/NN过渡测试。
