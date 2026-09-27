---
id: pcr02-aispeech-vad-contract-20260921
title: AISpeech CALL VAD 状态导出及 HDI 接入
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-vad-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: f6613b18a152e2e1a08107edc385b449e52b2c9573343720ae3ffad16710e639
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-vad-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-vad-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: CALL VAD 状态导出与 HDI 接入通过源码和对象验证，VOICE 检测器及产品整合未闭环
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech CALL VAD 状态导出及 HDI 接入

日期：2026-09-21。状态：source/object 已验证；产品链接和 HIL 未完成。

## 范围与结论

新增 SEVC_API_VadStatusGet，返回结构大小、模式代次、active、source、valid、warmup、Q24 平滑估计和二值 speech。由 Feed owner 串行调用，不与引擎变更并发。新增契约不改原有算法参数，也不扩大 NN/AGC 的启用范围。

CALL 模式 NN/AGC 已就绪时导出 AGC 的平滑 NN 增益估计，限幅至 0..16777216，并保留已有二值语音状态。该值不是校准的语音概率，speech 也不是独立调优的唤醒门控。VOICE/NR 没有近端 VAD，返回 source=NONE/valid=0；参考活动检测不能冒充近端 VAD。

HDI 在处理完实际 SEVC 帧后查询状态，仅在 valid 且 source=NN_AGC 时填充事件，包含代次、帧序号、CALL profile、来源与估计值。现有发送回调路径因此可接收有效 CALL 事件；没有设备运行证据。预热、模式不支持、未就绪或查询失败时不发送有效事件。

## 验证

- make -C modules/aispeech/tests run-vad-status run-public-abi：Host 重建和测试通过。
- 测试增强后再次独立编译和运行通过：空指针、短结构不写入、参考活动不成为近端 VAD、20 帧预热、NN/AGC 禁用、正负越界限幅、模式切换代次及复位。
- public ABI smoke 使用投影公开头，新增 VadStatusGet 调用；Host 运行通过，新 ARM 静态库链接通过，ARM 程序未执行。
- make NC=1 modules/aispeech_lib_all -j4：ARM 静态/动态库构建通过。
- 使用项目交叉配置定向编译 hdi_ai.user.arm.o：通过。
- AISpeech/HDI 公开头精确一致检查及 Git 空白检查通过。
- 测试注入内部检测器状态仅验证状态导出，不能证明声学准确率；HDI 回调行为未作运行时验证。

## 源码与制品

- AISpeech HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加既有脏改和本轮接口/测试改动。
- HDI HEAD b34d16ccd732d23be766b9c2b2b05016ac877008 加音频状态接入。
- API HEAD 93c280695f9867030e7d8dc705d8d4dc3f346ba6，APP HEAD 0447b7dd898de5a1d6b46c60d1a2118dbbba50b4；本轮未修改或切换。
- ARM 静态库 SHA256 ec3d98be4786c08c8d2e918b10102148432a8e80efbfc8e076ae90313f8b1695。
- ARM 动态库 SHA256 f5a904769e82bb394c159c7899e99e1298c9b8e988e993b7c4cdd96f0c739b96。
- HDI 音频对象 SHA256 a5dcc56a7d17711110465ccd6ccdba9608666818f1996f03cc6a358e9c709e3e。

## 尚未闭环

父仓公开媒体接口采用 FrameLease 所有权模型，当前音频分支的 API/APP 源码仍采用 FrameNode；视频回调还存在五/六参数差异。API master 与当前分支分别有 61/2 个独有提交，属于功能分支整合，不能靠批量头同步或类型别名修复。整合基线选择已向用户提出，未收到选择前不实施依赖该选择的迁移。

VOICE VAD 缺少近端检测器；保持不可用，不伪造静音。BF 候选、中文两词唤醒、NN/AGC 听感及设备耗时仍需后续验证。没有提交、自动 merge、部署、image/OTA 重生成。
