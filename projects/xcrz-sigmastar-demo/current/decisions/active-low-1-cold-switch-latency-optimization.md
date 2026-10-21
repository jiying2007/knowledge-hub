---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
id: pcr02-active-low-1-cold-switch-latency-optimization-20260728
title: PCR02 ACTIVE_LOW_1 COLD 切换耗时优化决策
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: manual
  from: manual-entry:knowledge-new.sh
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi-vi
- performance
validation_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-cold-switch-latency-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: SSC305 物理 1/30fps 继续使用完整 COLD rebuild；1→30fps 通过 lifecycle gate 内 Sensor teardown boost 与未连接 LDC 并行预热，将 RAW-only
  从 4.812s 降至 3.298～3.354s、both 从 5.845s 降至 3.323～3.426s；ISP DestroyDevice 约 0.999s 为当前安全下界；在线 FRC rebind 与预先 StopChannel
  无有效总收益，retained ISP/Sensor 继续 capability-gated。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1 COLD 切换耗时优化决策
---

# PCR02 ACTIVE_LOW_1 COLD 切换耗时优化：证据导航与待决策事项

> **状态：reviewing / 候选，不是已签署决策。** 2026-10-19 的补录依据同仓现存的 ProfileSwitchMode 历史正文，未回放当时源项目代码、计时原始数据或目标板测试。本条原模板未包含原始性能表与 owner 签字，因此 Registry 摘要中 4.812s→3.298–3.354s 等优化数值**仍无本条独立证据链**，不得作为当前版本的验收数据。

## 背景与适用范围

- 项目：PCR02 / SSC305，物理 1fps 与 30fps 的 VI profile 切换。
- 决策问题：COLD 全量 teardown/rebuild 的安全兜底是否继续作为默认路径，WARM/HOT 优化能否在完成专项验收后扩大适用范围？
- 不适用：未提供当前 VI graph、ISP lifetime、真实构建版本和板端验证标识的量产性能断言。

## 可核对的关联来源（仅历史项目候选）

- 同仓 [ACTIVE_LOW_1 Profile Switch Mode 当前决策候选](active-low-1-profile-switch-mode.md)，ID `pcr02-active-low-1-profile-switch-mode-20260729`，自身状态为 `reviewing`，尚未形成独立 owner 签署。
- 该来源正文描述 `VSHDIVI_InitParam_t.enProfileSwitchMode` 与 `[VI] ProfileSwitchMode=cold|warm|hot`，COLD 默认、WARM 资格验证候选、HOT 受控实验，以及 capability 不满足时回退 COLD 的计划。
- 关联来源内记录一轮历史 HIL：COLD 1→30 API 3.407023s，WARM 2.257506s，HOT 2.240004s；30→1 API 分别为 2.154947s、1.101895s、0.504283s。这是**来源正文中的历史结果**，不是本条新跑的 A/B；和 Registry 摘要另一测量阶段/口径的数值不得拼接。

## 选项与风险

| 选项 | 历史材料中的用途 | 尚缺证据 |
| --- | --- | --- |
| COLD | 全量重建、安全默认及失败兜底 | 当前版本基线耗时、故障恢复与回归 |
| WARM | 保留部分 ISP/Sensor 生命周期的准生产候选 | 24h 长稳、温循、低照、图像一致性、功耗和故障注入 |
| HOT | 受控实验，不做默认 | 首次切换、异常回滚与完整产品资格；收益与风险复核 |

## 决策与当前结论

- **本条独立 owner 决策：未取得。** 不把历史 ProfileSwitchMode 正文中的“生产默认”描述自动升级为本条当前正式发布批准。
- 不从一轮 HIL 或未经原始报告关联的性能摘要推出量产稳定性；COLD 继续作为待源码核验的保守路径参考。
- 旧环境变量实验文档不得作为当前可复制配置说明；最终入口应由源代码精确版本、现行配置合同和 owner 决策共同证明。

## 生效与回滚条件

- 生效需要：明确的 owner 签署、源代码与二进制 SHA 绑定、带测试环境/负载/统计分布的性能报告、图像/功耗/故障恢复矩阵和可重复 rollback。
- 任一 retained capability 失效或状态漂移时应按经源代码验证的受控 COLD 恢复策略处理；本文不授权修改运行设备。

## Review 周期与待办

- 沿用 Registry 原 `owner=team-core` 与 `review_after=2026-10-26`；本次 AI 文本补录不代表 owner 批准或 review 日期刷新。
- 取得 2026-07-28 原测量脚本/原始报告/精确 source SHA，解释与 2026-07-29 一轮 HIL 的测试口径差异；之后提交独立验证与真实 owner decision。
