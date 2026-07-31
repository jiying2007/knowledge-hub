---
related: []
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-aging-health-report-timeout-contract-20260717
title: PCR02老化健康上报与超时契约归档
kind: architecture
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/design/2026-07-17-aging-health-report-timeout-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f6ff1-9fa8-71a1-8b2a-e8019fbf1a54
review_after: '2026-10-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- aging
- health-report
- timeout
- mcu-soc
validation_refs:
- projects/xcrz-sigmastar-demo/archive/design/2026-07-17-aging-health-report-timeout-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/design/2026-07-17-aging-health-report-timeout-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 归档MCU变化触发和低频保底上报与SoC五秒stale超时冲突的跨仓契约；普通健康项可使用二十秒超时，WiFi和IR特殊语义不得机械统一。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 老化健康上报与超时契约归档

## 摘要

本文归档 MCU 健康状态上报节流与 SoC 老化程序 stale timeout 的跨仓契约。2026-07-17 的分析确认：MCU 不保证每秒发送所有健康帧；当值变化不超过阈值时，可能经过多次完整采样才执行保底上报。SoC 若统一以 5 秒未收到帧判失败，会在充电尾段或稳定状态产生假失败。

本文记录的是历史实现和建议边界，不代表 20 秒方案已通过全部板级老化验收。

## 适用范围

- PCR02 `app_product_test` 普通健康项。
- GD32L235 MCU 电池、电机和传感器状态上报。
- 不直接覆盖 WiFi 一次成功锁存、IR 特殊窗口或其他具有独立终态语义的项目。

## 权威来源

- source_id：`codex-raw-sessions`
- source_path：`codex-raw-sessions:019f6ff1-9fa8-71a1-8b2a-e8019fbf1a54`
- owner：`leiwenjun`
- source_status：历史源码核对和构建摘要，板级回归待验证

## 当前结论

1. `report period`、MCU 采样周期和 SoC stale timeout 必须作为同一跨仓契约设计。
2. 普通健康遥测采用 20 秒 stale timeout，能够覆盖 MCU 低频保底上报和调度抖动。
3. “读取/上报暂时缺失”与“健康项明确失败”必须使用不同状态，不能共用同一个 fail bit 语义。
4. WiFi 和 IR 等特殊项目不得因为普通项统一到 20 秒而机械改写。
5. 恢复稳定时间、失败锁存、测试总超时和 stale timeout 是四类不同参数。

## 超时分类

| 参数 | 用途 | 是否适合统一为 20 秒 |
| --- | --- | --- |
| 普通健康帧 stale timeout | 判断长期未收到周期状态 | 是，需板测 |
| 明确失败上报 | MCU/模块主动报告失败 | 否，应立即保留 |
| WiFi 成功锁存/连接窗口 | 网络状态机终态 | 否 |
| IR 测试窗口 | 受硬件激励和测量周期约束 | 否 |
| 恢复去抖 | 防止健康位快速抖动 | 独立配置 |
| 整体老化测试超时 | 控制测试时长 | 独立配置 |

## 历史验证证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| MCU 与 SoC 源码交叉核对（历史会话） | 0 | 识别 MCU 变化触发/低频保底与 SoC 5 秒 stale 冲突。 | `codex-raw-sessions:019f6ff1-9fa8-71a1-8b2a-e8019fbf1a54` | Project | 本条目 |
| `app_product_test` 定向构建（历史会话） | 0 | 普通健康项超时调整能够编译。 | 同一 session provenance | Project | 本条目 |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` | pending | 验证 Hub 登记与正文一致性。 | 本条目 | Knowledge Hub | registry item |

历史命令结果没有在本轮源项目复跑，因此只作为 session-derived evidence。

```yaml
manual_validation_pending: true
manual_validation_reason: 需要核对源仓提交并完成普通项与WiFi、IR特殊项板级老化回归
required_followup: 在匹配构建下执行稳定上报、延迟、丢帧、明确失败和恢复矩阵
owner: leiwenjun
review_after: 2026-10-17
```

## 风险与限制

- 20 秒会增加真实通信中断的发现延迟，必须由量产测试节拍接受。
- 若 MCU 保底周期未来变长，20 秒仍可能不足；应优先显式上报协议而非继续放大 timeout。
- 不保存电池序列、设备标识、raw 日志或本机绝对路径。

## Review

- owner：`leiwenjun`
- review_after：`2026-10-17`
- 下一次复核：源仓 commit、超时常量唯一性、WiFi/IR 例外和板级老化矩阵。
- Memory Candidate：no。
