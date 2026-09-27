---
id: pcr02-aispeech-dtd-conditional-release-review-20260920
title: AISpeech DTD 条件释放候选与 Host 构建隔离修复
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-conditional-release-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 640031b5a72ecea3c16cc2447c72b1288adfe714776b25ca4e0923a410c6c1d7
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-conditional-release-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-dtd-conditional-release-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-20'
updated_at: '2026-09-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-20'
manual_validation_pending: true
summary_zh: 定位强回声掩盖双讲导致提前释放；条件释放候选通过24样本退化筛查但未过全部门禁，保持默认关闭；修复Host共享对象宏混用并串行重验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech DTD 条件释放候选与 Host 构建隔离修复

- captured_at / last_verified: 2026-09-20
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- HEAD: 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1；审查 working-tree，保留此前未提交修改。
- Reviewer Independence: author-self-review；不等于独立审查或产品验收。
- 本轮范围：解释 fileid 7 反例；验证一个默认关闭的 DTD 条件释放候选；增加四轨逐帧诊断；修复 Host 构建资源隔离。

## 反例根因

固定 4 帧释放相对默认 8 帧在 fileid 7 上少保护 70 帧，其中 54 帧是带标签的双讲，16 帧是仅远端。
损伤集中在源帧 139、288、320 等区间：近端 RMS 仍约 1996～3018，回声 RMS 已达 4882～12507，残差/回声比因回声变大而下降。
例如帧 320 的 AES 平均增益从约 0.739 降为 0.629，双讲绝对 SI-SDR 从 10.658557 降为 10.295488 dB。
这否定了“比例下降代表近端静音”和“缩短保持只影响静音间隙”两个假设。

逐帧重放同时发现 AES 在 ref VAD 不活跃时走旁路，不更新判决；幅度/DTD 字段可能保留历史值。
用 aes_processed 筛选当前帧，再结合当前 ref_active 重放，fileid 7 的 624 帧 DTD 状态与实际完全一致。

## 最小候选契约

- 宏 `SEVC_AES_DTD_DROP_RELEASE` 默认 0，不修改默认 8 帧期限。
- 仅 Feed 线程维护私有残差锚点；当残差/回声占优判据成立且原始参考存在时刷新。
- 连续非占优至少 4 帧，且残差幅度低于或等于最近锚点的 1/4，才可提前释放。
- 回声升高但残差仍强时，继续使用 8 帧保护。
- Reset、旁路、路径事件或原始参考丢失使锚点失效；原始参考丢失的处理不依赖泄漏 telemetry 宏。
- 私有字段只在候选构建存在；库、评估器和内部类型消费者必须同宏重建。公共 API 未变。
- 候选是观测基础上的保守实验，不是近端存在的充分判据，不晋升默认。

## 构建问题与修复

发现 `build/compile.mk` 把 `.user.x86.o/.d` 放在源文件旁；不同 HOST_OUT/HOST_LIB_ROOT 仍共享这些对象。
并发重建使所谓默认库报告候选的 315620 字节，同时增益 telemetry 帧数变为 0，证明对象宏/内部布局混用。
该轮“全部零差异”矩阵和相关混合库结果明确作废。

tests/Makefile 的 host-lib 已加公共 flock，串行覆盖 clean/build，并重建当前对象组成的 archive。
直接使用底层 x86 构建的其他会话仍需遵守同一锁；同一输出目录的多次 make 仍不可并发。
修复后串行重建，默认内存恢复为 315604；fileid 7、4、25 与本轮修改前已冻结二进制的全部汇总字段一致。
候选评估结束后再次执行默认 host-lib 构建，将源目录共享 x86 对象恢复为默认宏配置，避免下一次增量构建沿用候选对象。

## 验证

- 默认与候选 DTD 单元测试启用 ASan/UBSan：回声增长保护、残差下降边界、两帧起动、旁路、Reset、路径事件、原始参考丢失。
- 关闭 SEVC_AES_LEAKAGE_TELEMETRY 的候选单元测试也通过。
- 默认 run-quality-metrics、run-aec-channel、run-reset-equivalence、run-long 通过。
- 最终候选 1000 轮尾链切换：315620 bytes、40013 回调、2000 次切换。Host 相对默认增加 16 bytes；不是 ARM 实测内存或性能结论。
- SigmaStar GCC 11.1.0 对 AES/API/func 三个受影响对象分别在宏 0/1 下交叉编译通过；未链接或部署产品。
- 四轨 --trace-frames 的 stderr 输出输入时刻状态与按源帧对齐的 PCM 能量/内积；不含 PCM 样本，stdout 汇总保持完全相同。
- 子仓 diff --check 通过；全库仍有既有编译告警。

## 串行重建后的声学矩阵

| 场景 | 默认 / 候选 ERLE dB | 默认 / 候选 DTD 误激活率 | 候选严格门禁 |
| --- | --- | --- | --- |
| Room001 | 11.604 / 12.036 | 6.164% / 3.425% | pass |
| Room002 | 24.908 / 24.908 | 6.849% / 6.849% | fail |
| path-change | 18.187 / 18.375 | 7.971% / 5.072% | fail |
| reset-stress | 11.319 / 11.754 | 7.971% / 5.072% | fail |

四场景近端绝对 SI-SDR、onset 相关性和削波计数保持不变。门限未放宽。
最终24样本矩阵已全部完成，0 个样本触发预设硬回归（双讲/显式近端 SI-SDR 降幅 >0.2 dB、FAR ERLE 降幅 >0.5 dB、新增最终削波）。
在报告精度下，FAR ERLE 变化为 0～+0.007 dB，双讲 SI-SDR 改善量变化为 0～+0.013 dB，显式近端 SI-SDR 与削波数均不变。
DTD 误激活率变化为 -0.03488～0（最大下降 3.488 个百分点）。fileid 7 双讲变化为 +0.012 dB。
双讲结束后首个 256 ms 窗口 ERLE 有 -0.008～+0.128 dB 的小幅变化，不宣称所有细分窗口单调改善。
以上均为最终串行重建制品的结果；先前混用对象的矩阵不纳入结论。

## 最终制品身份

- 默认 Host lib SHA256: ac5b48ae8186d6e7b233a0fd1caadc25f3d8471dac1844ff4ed070b738d3ecef
- 候选 Host lib SHA256: 0f36c60965d6dbf6e382950cb1fc6152427da29ca46753bf783c40fa19787027
- 默认四轨 evaluator SHA256: 349142c089c7be1a3dd4e651376cc1ba4302e377549602b0629ae7cccca6c434
- 候选四轨 evaluator SHA256: 88ef27e8075ccd793ef987fcbaa37ed03e2b2d1f52590743efbfd1dccdf5bc60
- AES source SHA256: 37792c538cccccbdf863a4168efc16e92837cd96e30c57c63422e217afb43f73
- 四轨 evaluator source SHA256: 6b3e3005c0001d478cf35290ff2259bee7826f8ee1bcb6fdd1b2c27739ea0aed

## 边界与后续

候选不能消除所有误激活，只保留 default-off 的离线可复验实现。下一步优先分析 Room002 剩余释放事件及判据可分性，不盲扫保持帧数或放宽门限。
真实双麦、QIVW、板端时延/负载与功耗未验证；Host/SIL 不代表产品完成。未提交、推送或部署。
归档仅含脱敏结论与身份，不包含原始音频、原始逐帧日志或设备端点。
