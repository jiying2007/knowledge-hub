---
id: provider-xcrz-sigmastar-demo-9bb41d2281ce7dc4e87d376b
title: CALL 回声优化补充实验 v3
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9bb41d2281ce7dc4e87d376b.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:9bb41d2281ce7dc4e87d376b07972aac283df1903902be952a61cfdecd9659a7
  source_sha256: 6e42b3d77e2268b03a93f8edacac0d93a80ca42e6d0ba827edd60d82e09517c6
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9bb41d2281ce7dc4e87d376b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9bb41d2281ce7dc4e87d376b.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 状态：needs-fix。本报告补充 REPORT-v2.md，原报告及其归档不覆盖。持续明显的设备回声仍未解决，未部署、未重链 ARM 应用、未提交或推送。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 9bb41d2281ce7dc4e87d376b07972aac283df1903902be952a61cfdecd9659a7
---

# CALL 回声优化补充实验 v3

状态：needs-fix。本报告补充 REPORT-v2.md，原报告及其归档不覆盖。持续明显的设备回声仍未解决，未部署、未重链 ARM 应用、未提交或推送。

## 独立输出与共享 NN 对照

沿用全部 16 组设备原始输入和全部 24 组公共四轨真值，CALL 固定 512 点延迟、原定 nearend_scale 和评分窗口；没有新增设备采集作为前置条件。

| 候选 | rpm240 far / far-motion 输出总能量衰减变化 | rpm480 far / far-motion 变化 | 24 组远端 ERLE 均值变化 | 双讲 SI-SDR 最差变化 |
| --- | --- | --- | --- | --- |
| 独立输出状态，候选复用基线 NN 掩码与 VAD，使用持久化掩码快照 | +0.594 / +0.339 dB | +0.401 / +0.541 dB | +0.016458 dB | -0.187 dB，fileid 18 |
| 独立输出状态与独立 NN 掩码，候选只复用基线 NN VAD | +0.659 / +0.446 dB | +0.503 / +0.633 dB | +0.015375 dB | -0.023 dB，fileid 0 |

第二组 fileid 18 双讲变化为 +0.064 dB；fileid 16 为 +1.484 dB。所有 24 组纯近端 SI-SDR 变化为 0，第二组双讲目标投影电平最差变化为 0 dB。两组重放均有 16 个 VOICE 输出及 4 个 CALL 纯近端输出 SHA256 与默认基线一致、全部配对输入七文件哈希相同、输出削顶为 0。

结果将本例弱双讲退化缩小到复用基线 NN 掩码这一因素：只复用 VAD 而保持候选独立 NN 掩码时，fileid 18 不再退化。这不证明设备回声根因，也不证明所有输入上的严格无损。第二组仍运行两套 NN，尚未核验 SSC305 CPU、调度和资源预算；收益不足以宣布明显回声解决，不改产品默认。

设备远端总能量变化包含噪声、AES、NN、AGC，不能直接称为纯 AEC ERLE。设备采集实际 profile 为 VOICE；这里 CALL 为实际算法离线重放。

## 制品和无效原型

- 第一组有效制品：independent-output-shared-mask-v2/libsevc_replay.so，SHA256 `2385cf6ad13bffd5239cf19187ac60e8424507ff84d76022f431df02716262e6`。
- 第二组有效制品：independent-output-baseline-vad/libsevc_replay.so，SHA256 `3363f1f1a065d5bd0c6ddcb8a76435b2681e5b125058454b958869b040918845`。
- 对应公共结果为 supervised-independent-output-shared-mask-v2.json、supervised-independent-output-baseline-vad.json；对应设备结果位于同名 replay 目录 results.json。
- 最早的 independent-output-shared-mask 原型直接在基线 Feed 返回后读取共享 scratch pfGainNew，该内存已可被后续阶段复用。其质量结果无效，不用于结论。v2 在 callback 前复制到独立持久缓冲，消除此证据缺陷。
- 上述两个有效构建的 build.json 保存了完整产品实验源码身份，撤回实验后的工作区不能冒充与它们一致。

## 恢复和后续边界

产品 NN 源码和私有头中的所有 SEVC_TEST_SHARED_NN_MASK、VAD_ONLY 字段及分支已经撤除；产品 C/header 与 REPORT-v2 的恢复锚点相同。Host 双尾链 adapter 保留为诊断工具；默认没有双引擎或 Speex 依赖。撤回后另建 fresh-restored-v3 核对默认静态产品库，结果以其新 build.json 和实际 cmp 为准。

本轮不继续盲调相同掩码/共享尾链。下一步需要验证低成本候选能否保留候选自己的抑制掩码和输出历史；完整双 NN 对照可作为保护参照，不能直接当作产品资格。继续保留上层业务接口、reader、订阅和现有 profile 切换契约。

根分区空间修复见 REPORT-v2：按用户明确授权清理无占用的自有旧 pytest 临时目录，释放约 1GB；没有删除其他用户文件或原始音频证据。

## 撤回后的新鲜验证

- fresh-restored-v3 默认定义为空，69 个 Host 编译单元完成，shared library SHA256 `b397789f60060ebe7dc5ee172ffc76be19011a5adbbd46bef465e644d71423f7`，与 v2 恢复后的 shared 相同。
- 默认静态产品库逐字节与恢复锚点相同，SHA256 `70b002d6eb55236abf9f4183e8061dc43e36a2288b840803a307c48b27683c28`。
- 新 build.json SHA256 `f978e5a27f77042570614ee00b2f86fc14d79142b4976573d327951b7482435a`，当前全部 source_identity 均无漂移。
- fresh-restored-v3-replay/results.json 的 16 场景 × 两 profile 共 32 输出 SHA256 与 fresh-restored-final 基线完全相同，配对输入七文件哈希相同。
- 产品 sevc C/header 对原始恢复锚点没有 SHA256 差异；AISpeech git diff --check 通过。前序 1000 轮切换、Reset/ABI 与 20 Python 契约结果见 REPORT-v2，此段没有重新声称执行这些不受影响的测试。

本段新增保护/掩码归因是 Host 诊断结论，保持 reviewing/needs-fix，不代表产品默认已优化或设备听感已通过。
