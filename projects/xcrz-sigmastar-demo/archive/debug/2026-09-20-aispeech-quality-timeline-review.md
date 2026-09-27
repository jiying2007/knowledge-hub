---
id: pcr02-aispeech-quality-timeline-review-20260920
title: AISpeech 声学评分对齐修复与 DTD 释放候选否决
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-quality-timeline-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 1aeaf6472b7c0000bb8ec313555551a5daf24642c5e04c6ac44359e8990d95b0
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-quality-timeline-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-quality-timeline-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-20'
updated_at: '2026-09-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-20'
manual_validation_pending: true
summary_zh: 修复SI-SDR基线与远端功率评分时间轴；四帧DTD释放候选在公开四轨样本上退化并被否决，默认保持不变。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 声学评分时间对齐修复与 DTD 释放候选否决

- captured_at / last_verified: 2026-09-20
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- Review Target: working-tree，HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1；保留此前未提交改动。
- Reviewer Independence: author-self-review；不是独立审查或板端验收。
- 本轮改动：tests/sevc_aec_quality_evaluator.c、tests/sevc_quality_metrics_regression.c、tests/Makefile、tests/README.md。
- 本轮未修改产品算法源码或默认配置。上一轮 NR 修复保持原样。

## 根因证据与修复

1. 原始 mic 与 clean-near 同属输入时钟；评估器寻找输出延迟后，却将 mic[index] 与 near[index+lag] 相比，导致基线错误。已改为 mic[index+lag] 对 near[index+lag]。已知延迟直通用例修复前凭空得到 131.458581 dB 改善，修复后正负 256、正负 13 和零延迟均为 0。
2. 仅远端输出功率原来按当前 Feed 帧归类。Room001 第 160 帧输出仍含第 159 帧近端语音，能量比约 -24.18 dB，污染远端汇总。现按测得的近端相关延迟将 PCM 输出映射回输入时钟，完整帧才评分，EOF 不补零。保留 unaligned_far_erle_db，新增 metrics_version=2 和 aligned_far_frames。
3. 恰好 8 帧的恢复窗口原先被拒绝；现在允许完整窗口，NaN 不能判为已恢复。Reset 恢复搜索止于 near-only 起点，避免跨入近端阶段。
4. 新增 --trace-frames，只输出 stderr 逐帧标量；DTD 按当前 Feed 时刻观测，PCM 延迟不能机械应用到频域状态。

Repair note：保留产品 PCM、既有 NR 修复和门限；最小复跑为已知信号评分测试及两场景对照。回退仅涉及本轮测试代码，不覆盖已有算法改动。

## 时间线与被证伪假设

- 原始 DTD 远端激活：Room001 为帧 8、160～167；Room002 为帧 8～9、160～167。
- 第 160 帧 STFT 残差仍含近端，随后 7 帧处于默认 8 帧释放过程；并非持续的稳态误激活。
- “Room001 负 ERLE 全部是滤波失效”不成立：校正时间轴后为正；但第 161 帧后仍有真实恢复过程，不能归结为纯评分错误。
- “缩短 DTD 保持即可安全解决质量门禁”被四轨样本反例否定。

## 同一算法的评分修正

| 场景 | 旧同帧 ERLE | 对齐 ERLE | DTD 误激活率 | 严格门禁 |
| --- | --- | --- | --- | --- |
| Room001 | -0.225 dB | 11.604 dB | 6.164% | fail |
| Room002 | 22.533 dB | 24.908 dB | 6.849% | fail |

两组估计延迟均为 -256 samples，PCM 远端完整评分帧 145，DTD 观测帧仍为 146。
Room001 双讲后 0～256 ms ERLE 从 -11.369 变为 0.882 dB；恢复到预双讲基线减 3 dB 仍需 24 帧。
这不是算法收益。近端 SI-SDR 改善字段也修正了原始 mic 基线，v1/v2 不能混用。
纯净 near-only 的输入基线接近完美，修正后改善量为大负值并不表示本轮损伤了 PCM；必须结合绝对保真和相关性解释。

## 单变量候选：DTD release 8 -> 4

独立临时目录同时重建全 Host 静态库和两个静态链接评估器，使用 GCCFLAGS='-Os -DSEVC_AES_DTD_RELEASE_FRAMES=4'。
候选不进入默认配置。可通过 tests/Makefile 覆盖 HOST_OUT、HOST_LIB_ROOT、QUALITY_TEST_BIN、AEC_CHALLENGE_TEST_BIN 复跑。
先验拒绝界限：双讲或显式近端 SI-SDR 降幅 >0.2 dB、FAR ERLE 降幅 >0.5 dB、onset 相关性降幅 >0.02、或增加最终削波。

| 场景 | baseline / candidate ERLE | baseline / candidate DTD 误激活率 | candidate gate |
| --- | --- | --- | --- |
| development | 11.604 / 12.037 dB | 6.164% / 2.740% | pass |
| validation | 24.908 / 25.454 dB | 6.849% / 0% | pass |
| path-change | 18.187 / 18.481 dB | 7.971% / 2.899% | pass |
| reset-stress | 11.319 / 11.769 dB | 7.971% / 2.899% | pass |

随后按冻结的 24 样本 CSV 顺序检查，fileid 0、4 未触发拒绝界限；fileid 7 的双讲 SI-SDR 改善量下降 0.363 dB。
候选在第 3 个样本被否决，停止矩阵，不宣称跑完 24 样本。保留默认 release=8，不以四个合成场景通过代替近端保护。

## 验证、身份和下一步

- `rtk make -C modules/aispeech/tests run-quality-metrics /tmp/pcr02-aispeech-aec-quality-evaluator /tmp/pcr02-aispeech-aec-challenge-evaluator` 返回 0。
- 评分测试启用 ASan/UBSan，覆盖延迟直通、逐帧能量、不完整边界、空输入和恰好一个恢复窗口；算法库未整体插桩。
- 当前子仓 diff --check 通过；本轮未重建 ARM 产品或访问设备。
- evaluator SHA256: 86ff30c7f89de3770cad9f09d186a7a5266402bf6ee48ab7b8dc710f43b0f080
- metrics test SHA256: 9bd14aa076649c2bce6dd66c47235fc26d3e408f9ccf4ccb5c51800d1367ce8b
- baseline Host lib SHA256: 526197cb3b3bffd20d38ea45cbddc914bc998e1940be413fef75c58d92191ad8
- release4 Host lib SHA256: 4f73caa92799ae744e44f438f451783e9e8f1101f6c695f1eade4041c41537fd

后续优先拆分 fileid 7 的双讲间歇与保持保护作用，设计有证据的释放条件；不要继续盲扫固定保持帧数。
产品默认仍未通过严格 DTD 门禁，SSC305 性能与 QIVW/HIL 待验证。记录为 reviewing，不晋升产品结论。
仅归档脱敏结果与复跑约定，不包含原始音频、日志或设备身份。
