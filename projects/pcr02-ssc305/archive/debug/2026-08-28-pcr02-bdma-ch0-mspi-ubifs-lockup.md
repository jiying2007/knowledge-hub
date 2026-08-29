---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-bdma-ch0-mspi-ubifs-lockup-20260828
title: PCR02 MSPI0 泄漏 BDMA CH0 导致 NAND/UBIFS 全局阻塞
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-08-28 现场只读 ADB/SysRq/MMIO 证据与本地 SDK 源码、Git 历史交叉分析；原始日志和设备端点不归档
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-09-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- bdma
- mspi
- spi-nand
- ubifs
- deadlock
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-28'
updated_at: '2026-08-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-28'
manual_validation_pending: true
summary_zh: 实机 SysRq w、MMIO 与源码交叉证实：最后占用 BDMA CH0 的路径为 MIU 到 MSPI0；硬件 busy/done/IRQ pending 均为 0，但 CH0 信号量未归还，LCD 后续请求与 SPI-NAND/UBIFS
  回写共同阻塞于 CamOsTsemDown。MSPI DMA 超时路径缺少 owner-aware stop、IRQ 同步与信号量释放；两个 25fps ST77912 的高频小包和 4KiB 像素块放大触发概率。Flash cancel
  的迟到 IRQ 竞态保留为未证实触发候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 排障记录标题

## 现象

说明用户可见症状、错误码、时间和频率。

## 影响范围

说明项目、设备、版本、模块，以及是否影响量产或现场。

## 环境

说明硬件、固件、配置、工具和输入数据。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
|  |  |  |

## 证据

记录日志摘要、命令摘要、artifact 引用和 hash；不写 raw 大文件正文。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
|  |  |  |  |

## 根因

确认根因；未确认时写“未确认”。

## 修复或规避

说明已执行动作、适用范围和副作用。

## 验证

说明复现前后对比、命令和通过/失败判据。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason:
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner:
review_after:
```

## 后续动作

说明是否提升为 runbook、validation、decision，或仅归档。
