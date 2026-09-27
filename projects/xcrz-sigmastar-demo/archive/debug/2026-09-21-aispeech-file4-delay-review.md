---
id: pcr02-aispeech-file4-delay-review-20260921
title: AISpeech fileid 4 对齐对照与四轨评估器加固
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-file4-delay-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 19710af6262ffce84d38acd80977ad9b75fee8b2038d2047afe2d484ab52c304
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-file4-delay-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-file4-delay-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 否决逐窗最高峰及零延迟直接替代；四轨评估器缓存搜索使Host耗时约降47%，24样本指标不变，并拒绝长度不一致及非法缩放输入。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech fileid 4 对齐对照与四轨评估器加固

- captured_at / last_verified: 2026-09-21
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- HEAD: 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1；保留既有工作树改动。
- Reviewer Independence: author-self-review。
- 本轮范围：fileid 4 有效原始激活定位、两种单变量对齐对照、评估器输入与搜索优化。
- 未修改产品算法、默认参数、参考通道部署或设备。

## fileid 4 证据

默认自动固定延迟为 405 samples，相关性 0.315049，次峰 621 samples/0.267459，峰差 0.04759。
四个分析窗的最高峰为 404、405、408、786 samples，窗口峰差 0.025612～0.055485，存在明显多峰歧义。
52 个有效原始激活帧分布在多个仅远端区间，近端参考能量为零，回声 RMS 约 240～3300，并非全部为低能量边界。
样本元数据为 nonlinear-clean，但这些证据不能把残差唯一归因于非线性；有限滤波尾长和对齐选择仍有混杂。

| fileid 4 对齐方式 | 远端 ERLE dB | 双讲 SI-SDR 改善 dB | 有效原始激活帧 |
| --- | --- | --- | --- |
| 原固定最高峰 405 | 7.912 | 4.899 | 52 |
| 逐窗最高峰 | 6.836 | 3.969 | 67 |
| 固定零延迟 | 2.718 | 2.182 | 139 |

fileid 7 的零延迟对照同样退化：远端 ERLE 16.397 -> 2.179，双讲改善 16.017 -> 2.810，最终削波 0 -> 3。
结论：否决这两种直接替代；不因窗口峰位改变就推断真实延迟漂移，不推广到产品参考路由。
fileid 4 原基线仍有 8 个最终削波采样；四轨 evaluator 返回 0 只说明成功评估，不是声学质量通过。

## 本轮实现

1. estimateReferenceDelay 缓存候选相关分数，主峰、次峰与局部比较复用。最大延迟附近的外侧邻域仍单独计算，保持原搜索行为。
2. 四轨样本数必须相同；此前按最短轨静默截短，可能掩盖输入不完整。现在输出 track_length_mismatch 并在评分前失败。
3. 长度一致但存在共同不完整尾帧时，保持旧完整帧评分规则，新增 input_samples/discarded_tail_samples 明确覆盖范围。
4. 缩放必须有限且 0 < scale <= INT32_MAX/32768，约束参考幅度与统计数值范围。显式近端对照先在浮点域饱和，再转为 S16，避免先窄化后限幅。
5. 增加 run-reference-delay 回归入口，覆盖已知延迟、搜索边界、静音、空输入、四轨长度与数值边界。

仅修改 tests/sevc_aec_challenge_evaluator.c、tests/sevc_reference_delay_regression.c、tests/Makefile、tests/README.md。
缓存约 64 KB，位于 Host 评估器临时栈，不进入产品内存或算法库。

## 新鲜验证

- ASan/UBSan 定向测试通过：已知 0/257/8000 samples 延迟、最大搜索边界外的邻域探测、静音和空输入。
- 当前 24 个冻结四轨样本长度均一致。旧/新评估器的全部原有 JSON 指标逐项一致，包括延迟、次峰、窗口信息、DTD、语音保真和削波；新增两个覆盖字段单独验证守恒。
- fileid 4 的数字延迟覆盖与 windowed 模式也保持旧指标一致。
- 端到端负例：将 fileid 4 近端 WAV 减少一个采样，旧评估器接受并输出指标，新版本以退出码 1 拒绝且不输出评分 JSON。
- inf、nan、1e999、65536、0、负缩放值均以 CLI 退出码 2 提前拒绝，不输出评分 JSON。
- 相同编译选项与算法库、逐样本旧新配对运行：24 样本总耗时 78.7618 -> 41.7819 秒，单样本中位数 3.2820 -> 1.7404 秒；本机约 1.885 倍速度、46.95% 耗时降低。
- 这是 Host 评估器墙钟测量，没有 CPU 绑核，不外推 SSC305 p95/p99 或算法性能。
- make -n 核验新增入口，测试本身以同等命令实际编译并运行；未为纯评估器修改重复构建算法库。
- 子仓 git diff --check 通过；算法库 hash 与进入本轮时一致。

## 身份与剩余工作

- Host baseline lib SHA256: ac5b48ae8186d6e7b233a0fd1caadc25f3d8471dac1844ff4ed070b738d3ecef
- evaluator source SHA256: e511f3c9486709ebc628d84ef874afea6d42818560c31314e6ee47309b5f3726
- regression source SHA256: b973382fa16a6db1dc519bb4bbc4bd0333af13442c908fed17d33a0b138c9c86
- new evaluator SHA256: b982eaf77c916b4dbeb0815ed5887adb432154cdef6e4ea38236137ed7145948

fileid 4 的残余回声来源仍未唯一定位；需要能隔离非线性与滤波尾长的对照，不能继续凭一个最高相关峰或单项 DTD 占比改产品。
既有条件释放候选仍默认关闭；产品门禁与板端/QIVW 未闭环。未提交、推送或部署。
只归档脱敏结论；负例音频在临时目录生成并清理，不归档原始音频或逐帧日志。
