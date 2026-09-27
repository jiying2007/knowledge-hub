---
id: pcr02-aispeech-aec-res-failure-discriminator-20260915
title: AISpeech AEC RES 失败样本鉴别器边界
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-failure-discriminator-boundary.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: c3393e378e3a16a7d23d8ad22d699a2f29f7310ed986db600ea9bb175e89fa67
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
- reference-alignment
- double-talk
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-failure-discriminator-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-15-aispeech-aec-res-failure-discriminator-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-15'
updated_at: '2026-09-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-15'
manual_validation_pending: true
summary_zh: 固定四轨失败样本否决全局delay、固定AES cap和state-only cap，收敛到真实reference路径证据需求。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AISpeech AEC/RES 失败样本鉴别器边界

## 结论

在固定 24 样本 Microsoft AEC Challenge 四轨开发集中，负远端 ERLE 和负双讲 SI-SDR 不能通过全局 reference delay、固定 AES gain cap、AES DTD-only cap 或 shadow Activity/DTD state-only cap 安全修复。上述方向均已用固定反例证伪，产品默认继续保持一抽头、默认 AES gain 和默认 reference 路由。

## 证据

- Fileid 21 和 27 的相关性估计 delay 分别为 861 和 905；向更小 delay 扫描可将远端 ERLE 从 -0.531/-0.613 提升到 3.438/2.317 dB。
- Fileid 59 向更小 delay 扫描反而使双讲 SI-SDR improvement 从 -0.096 下降到 -0.279 dB，因此不能推广统一 delay 偏移。
- 固定 1.5 AES cap 或仅 AES DTD 状态内的 1.5 cap 能改善若干失败双讲样本，但 Room002 clean-near 1272-128104-0002 的弱起始相关性从 0.82098 降至 0.77435。
- 失败样本 21/27/45/59 的 AES DTD 在仅远端帧中激活率为 0.84541 至 0.99713；shadow double-talk active 为 0.22941 至 0.80882。
- 健康双讲样本也可有高 shadow active，例如 fileid 29/63/99 为 0.53141/0.78713/0.63009，无法作为单一鉴别器。

## 决策

- 删除实验性 DTD-only AES cap 宏和实现，不保留运行时开关。
- 四轨 evaluator 保留 AES DTD 与 shadow Activity/DTD 分段统计，用于后续真实 reference 路径验证。
- 不继续增加仅依赖 residual/echo、similarity、AES DTD 或 shadow state 的 gain 阈值。
- 后续优先获取实际 AO/Codec/功放/机壳路径下的 reference 对齐和路径变化证据，再评估同步/对齐机制；Host 数据不能设置产品 reference delay。

## 验证边界

- 默认四轨 evaluator 已通过编译并输出新增状态字段。
- split manifest JSON、96 个 WAV 的 SHA-256 inventory 和 AISpeech 子仓 diff check 已通过。
- 严格 SLR28 AEC/RES quality gate 仍失败；没有 QIVW 唤醒率、SSC305 实时性或移动播放 HIL 证据。

## 来源

- Microsoft AEC Challenge synthetic，revision 6c633d0a9d2a143a0e364899b91b06f127315b18。
- 仓内固定 split、hash 和指标契约位于 modules/aispeech/tests/validation。
- 本候选不包含原始音频、设备端点、日志或凭据。
