---
id: pcr02-aispeech-aec-res-24-sample-split-20260915
title: AISpeech AEC RES 24样本分层验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-24-sample-split.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 7596961cc55a7af978153c3c3f819b9feba5b5270ba16bd66f722833b33a7297
  temporary_source_retained: false
review_after: '2026-10-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- aec
- res
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-24-sample-split.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-24-sample-split.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-15'
updated_at: '2026-09-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-15'
manual_validation_pending: true
summary_zh: 24个四轨样本验证默认AEC RES、显式仅近端保护和两级headroom候选，组合候选因双讲退化被否决。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AISpeech AEC/RES 24 样本分层验证结论

## 背景

AISpeech 固定点前端需要在不替换产品链路、不修改默认一抽头配置的前提下，分别评估仅远端、仅近端和双讲，并定位 IFFT、重叠相加和固定输出增益的削波来源。

## 数据与方法

- 数据源：Microsoft AEC Challenge synthetic test 数据。
- 固定开发集：24 个四轨样本，按 linear-clean、nonlinear-clean、linear-noisy、nonlinear-noisy 各 6 个分层，SER 覆盖 -10 至 9 dB。
- 四轨输入：far-end speech、echo、clean near-end speech、near-end microphone mixture。
- 仅近端补充：将缩放后的 clean near-end 同时输入两个 mic，reference 置零；该 counterfactual 与原始 mixture 指标分开统计。
- 原始 WAV 保持 Git 忽略，只跟踪来源 revision、split、许可说明和 96 文件 SHA-256 inventory。

## 结果

- 默认一抽头：远端 ERLE 范围 -0.613 至 19.258 dB，平均 5.136 dB；18/24 样本的 AEC residual/echo 大于 1。
- 原始 mixture 共覆盖 7841 个仅远端帧、240 个自然仅近端帧和 6469 个双讲帧。
- 显式仅近端共 6709 个有效帧：相关性 0.97483 至 0.99999，平均 0.99674；SI-SDR 最低 12.815 dB；DTD 未激活且无削波。
- 默认削波计数为 IFFT/overlap/output/final = 47/112/497/497。
- 默认关闭的输出 limiter 将 final 降为 0，但双讲 SI-SDR 最差变化 -0.483 dB。
- 默认关闭的 IFFT limiter 将 IFFT/overlap/final 降为 0/35/369，双讲最差变化 -0.173 dB。
- 两级 limiter 串联虽将 IFFT 和 final 均降为 0，但双讲最差变化扩大到 -1.003 dB，因此否决组合推广。

## 决策与边界

- 保持产品默认一抽头、AES cap 关闭、两个 headroom limiter 关闭。
- 两个单级 limiter 只保留为 shadow/诊断候选；不能称为 AEC/RES 质量修复。
- 不对 overlap 状态做逐帧缩放，因为这会改变跨帧合成状态，超出短期小改边界。
- Host/SIL 数据不能替代 QIVW 唤醒率、SSC305 实时负载和移动播放真机 HIL。

## 验证与复跑

- 仓内入口：`modules/aispeech/tests/Makefile` 的 `run-aec-challenge-split`。
- 数据契约：`modules/aispeech/tests/validation/datasets/aec-challenge-synthetic/aec-challenge-synthetic.manifest.json`。
- 指标契约：`modules/aispeech/tests/validation/STAGE_POWER_CONTRACT.md`。
- ARM 默认构建、Host 基础回归、公共头检查、manifest JSON、split checksum 和 diff check 均有本会话新鲜证据。
- SLR28 严格 quality gate 仍失败，产品结论保持 needs-fix。

## 来源与版权边界

- 上游：https://github.com/microsoft/AEC-Challenge
- 上游 revision：6c633d0a9d2a143a0e364899b91b06f127315b18
- 获取日期：2026-09-15
- 本候选不保存第三方音频、原始日志、设备端点、凭据或客户资料。
