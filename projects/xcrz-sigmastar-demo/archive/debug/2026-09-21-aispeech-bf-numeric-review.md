---
id: aispeech-bf-numeric-review-20260921
title: AISpeech BF 数值与资源契约验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-bf-numeric-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 3fc7f7dd637554d8fed02be35a4e429c0476df6da5bfff3187a842d37b1388f7
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-bf-numeric-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-bf-numeric-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: BF及SPP溢出修复，资源检查和Reset回归
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech BF 数值、资源契约和下游 SPP 审查

本轮完成 BF 及紧接 SPP 的数值安全修复。源码基线为 AISpeech
9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加既有 dirty；保留其他更改。

## 已复现问题与修复

- BF 极值输入 UBSan：1083123197 + 1115906817 在 S32 累加溢出。
  改为 S64 逐麦移位后累加，最终饱和输出，保持正常范围取整规则。
- 中心波束复数乘法宏内部提前转 S32，首次修复后 oracle 仍失败；
  改为显式 S64 乘加及移位，复测通过。没有修改通用复数宏。
- 构造未限制资源尺寸；固定三波束写入与可变分配不一致。
  内存估算和构造拒绝非三波束/双麦及非 8k129bin、16k257bin 配置。
- BF Reset 原为空，测试帧计数清零断言失败。现在清计数及输出，保留权重/回调。
- 下游 SPP 复数功率在两分量 INT_MIN 时有符号平方和为 2^63，UBSan 复现。
  改用 U64 平方和后缩放到 S64，后续十倍回声项安全。

资源权重与默认参数不变。当前 AES 分支仍消费最后一路 AEC residual；
BF 输出和 SPP 在本默认配置中不能直接代表尾链音质收益。
BF 实现去掉完整输出清零遍历、按频点生成输出，但增加宽位运算；
未测量设备 CPU，不能宣称更快。引擎持久内存无新增。

## 验证

`rtk make -C modules/aispeech/tests run-bf-numeric run-stage-contracts run-pipeline-fingerprint run-vad-status run-agc-window run-nr-numeric run-nr-state` 退出 0。
SPP 测试补强真/假覆盖后直接用相同 flags 重编并运行，退出 0。
`rtk make NC=1 modules/aispeech_lib_all -j4` 退出 0。
`rtk git -C modules/aispeech diff --check` 退出 0。

- BF normal/extreme/config/reset 在 8k 和 16k 单阶段通过 ASan/UBSan。
  正常幅度在修复前后均与同一独立 oracle 一致；极值修复前失败、修复后通过。
- SPP 125 种组合，与 128 位 oracle 一致，覆盖判定真/假。
- stage-contract 11 场景、VAD 状态及 AGC40150帧通过。
- NR default/legacy/asym/combo 数值边界和突变到静音状态、历史独立性通过。
- 默认整链1000帧混合模式/reset指纹16985685392395738340，内存315620，与前轮相同。
- NN 复位实现可见能量/特征/CMN/FSMN历史清理；现有states测试通过，未新增弱语音声学评分。

ARM静态库SHA256：2c734159428dc9de02deadd9a123ad7c59aaf8b1563f5b18aa3d13ae00cb518d。
ARM动态库SHA256：2ea20f3df0e6859aef89439826629c1c4b7dc4d81624e541584889af354be8a0。

首次测试错误地用公开API创建8k整链，返回空并断言失败；已改为16k API
取配置模板后单独构造8k BF。这不构成公开API支持8k的证据。
Sanitizer覆盖本轮BF和SPP源码，不是全库全链instrument。
当前极值来自合成频谱，没有真实设备已触发的证据。

## 交付边界与后续

本轮为 targeted 自审，不声称外部独立审查或所有算法已审完。
下一步：NR/NN 弱语音、噪声突变声学矩阵；设备BF及整链CPU；产品集成另行处理。
未提交、合并、部署或生成image/OTA，旧编译警告未全部清理。
Runtime Control idle/null goal，required-artifact-missing 按 planning skill 记not_applicable。
reusable_pattern: 定点复数在窄化前做宽位累加并检查后续消费者。
promotion_candidate: false；do_not_promote_reason: 项目固定资源契约；owner_review: pending。
rollback_path: 仅反向本轮BF/SPP/测试补丁再重编算法，保留先前dirty。
next_task_friction_reduced: BF边界回归入口；reduced_by: run-bf-numeric；reduction_evidence: 修复前失败后通过。
