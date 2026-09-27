---
id: aispeech-agc-window-review-20260921
title: AISpeech AGC 窗口优化验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-window-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: d24831e5fe84025933680a6572e936c3dc4f9ca29d1bd664cf012d85dc0f7e09
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-window-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-window-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: AGC滚动窗口与非法配置防护，Host数值等价及ARM构建验证
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech AGC 窗口优化与数值等价验证

本轮在现有音频分支上完成 AGC VAD 长短窗口滚动求和，以及非法窗口拒绝。
源码基线：modules/aispeech HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加既有 dirty。
保留此前改动，没有提交、合并、部署、生成 image/OTA。

## 实现与边界

- 默认窗口 20/3，每帧遍历 23 个历史值改成两个 int64 累计更新；保留取整规则。
- 输入差值先转 int64；最大 U16 窗口乘 int32 幅度小于 2^47，累计安全。
- 构造和内存估算拒绝 0、负数及超过 65535 的长短窗口，避免窄化和除零。
- 构造完成调用 Reset，使历史数组、累计值和判定同源清零。
- 配置长度在引擎存活期间不可变；当前源码没有 AGC 模块外的历史窗口写入者。
- 私有结构增加两个 int64，必须一致重编译算法及私有结构消费者；公开 API 未改。
- 未调整 AGC 曲线、时间常数、VAD 阈值或 AEC/AES/BF/NR/NN 参数。

## 新鲜验证

以下命令退出码均为 0：

- `rtk make -C modules/aispeech/tests run-agc-window run-stage-contracts run-vad-status run-pipeline-fingerprint run-reset-equivalence`
- `rtk make NC=1 modules/aispeech_lib_all -j4`
- `rtk git -C modules/aispeech diff --check`

AGC 源文件启用 ASan/UBSan，40150 帧逐帧比较独立逐窗求和 oracle；
窗口为 20/3、1/1、3/20、31/7、65535/65534。最大窗口仅 150 帧，
其余每组 10000 帧。覆盖 Reset、Q24 和 int32 极值，非法配置返回失败。
没有把无效概率输入继续送入增益策略，极值测试边界是 preprocess。
stage-contract 11 场景、VAD 状态和 CALL Reset 回归通过。

优化前后各自重建 Host 库并运行相同 1000 帧混合模式/reset 测试：
PCM hash 均为 16985685392395738340；Host 内存需求 315604 -> 315620 字节。
这是合成回归指纹一致，不能替代全部音频位精确证明或声学验收。

ARM 静态库 SHA256：9487e3c21ebf8af505dbd3f6bdba28c33a3af6e57e382dfd6887fbd09f3c7e61。
ARM 动态库 SHA256：3b64874f23ce4686159672f314b9ae0b2b7e1a4d7d6284dd949d0f346951fa45。
旧代码的宏重复和 unused 警告仍存在。未重建完整产品，未做设备 CPU 或声学 HIL。

## 审查与后续

本轮为主代理 targeted review，非外部独立复审；检查了累计写入者、
构造/Reset 配套、长度转换和差值溢出。既有 AEC/BF/NN 的 stage-contract
通过不代表这些环节已完成全面审查。
后续继续 BF 消费链和计算开销、NN/NR 弱语音与突变噪声、AGC 设备算力测试。
产品媒体/音频分支整合继续独立待定。

Runtime Control 错用 checkpoint event 返回 2，修正 apply 后为 idle/null goal、
required-artifact-missing；依 planning skill 单列 not_applicable，不覆盖算法验证。
reusable_pattern: 宽位滚动总和保留末端取整；promotion_candidate: false。
do_not_promote_reason: 本项目局部优化；owner_review: pending。
rollback_path: 仅反向本轮 AGC/types/测试补丁并重编算法，保留之前 dirty。
next_task_friction_reduced: 后续窗口实现可复用独立 oracle；reduced_by: run-agc-window。
reduction_evidence: 40150 帧检查通过；verification_evidence: 上述命令和制品哈希。
