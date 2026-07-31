---
id: pcr02-active-low-1-profile-switch-mode-20260729
title: PCR02 ACTIVE_LOW_1 Profile Switch Mode当前决策
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/decisions/active-low-1-profile-switch-mode.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-decision
  from: xcrz-sigmastar-demo
  source_sha256: 3a8c254c230bf3710a8cfa73a850e0bf4fab4723a16dc2ac421b8bf7991085f2
review_after: '2026-08-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- hdi-vi
- profile-switch
validation_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-profile-switch-mode.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-profile-switch-mode.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 1/30fps切换入口统一为VSHDIVI_InitParam_t或VI.ProfileSwitchMode；COLD为生产默认、WARM为准生产候选、HOT仅用于受控实验，旧环境变量文档待supersede。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1 Profile Switch Mode当前决策
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 ACTIVE_LOW_1 Profile Switch Mode 当前决策

## 决策

1fps/30fps 的 profile 切换模式统一通过 `VSHDIVI_InitParam_t.enProfileSwitchMode` 选择：

- `VSHDIVI_PROFILE_SWITCH_COLD`：生产默认。
- `VSHDIVI_PROFILE_SWITCH_WARM`：优先进行准生产资格验证。
- `VSHDIVI_PROFILE_SWITCH_HOT`：仅用于受控性能实验。

产品配置统一使用：

```ini
[VI]
FpsHigh=30
FpsLow=1
ProfileSwitchMode=cold
```

`ProfileSwitchMode` 可取 `cold`、`warm` 或 `hot`，也兼容数字 `0`、`1`、`2`。未配置、
传入 `NULL`、结构体零初始化或配置值无效时保持 COLD。

旧环境变量 gate 已从 HDI、测试工具和现行文档入口删除，不提供兼容别名、回退解析或双轨
控制。历史记录只能说明旧二进制当时如何验证，不得提供可复制的旧命令。

## 使用契约

- 切换模式在 `VSHDIVI_Init` 时固定；当前没有运行时 mode setter。
- 修改模式需要重新初始化 VI。
- 同一 VI session 内的正常物理帧率切换只调用 `VSHDIVI_SetFps(1)` 或
  `VSHDIVI_SetFps(30)`。
- 业务层不传 route 数字；planner 根据 mode、runtime graph、ISP lifetime key 和 capability
  自动选择实际路由。
- 首次启动、完全关闭、runtime graph 无效、ISP lifetime key 改变或 retained capability
  不满足时，无论配置何种 mode 都走 COLD。
- 同 profile 的 RAW、MAIN、SUB demand change 使用局部 graph rebuild，不由 profile switch
  mode 决定。

## 三种模式

| Mode | 保留资源 | 重建资源 | 当前定位 |
| --- | --- | --- | --- |
| COLD | 不保留跨 profile 媒体资源 | Sensor/VIF/ISP Device/Channel/IQ/LDC/SCL/下游 graph | 生产默认与安全兜底 |
| WARM | Sensor、VIF、ISP Device | ISP Channel/IQ、LDC/SCL、RAW/VENC graph | 准生产候选 |
| HOT | Sensor、VIF、ISP Device、停止的 ISP Channel/IQ | LDC/SCL、RAW/VENC graph | 受控性能实验 |

WARM/HOT 执行前不满足 retained 条件时，本次目标请求直接改走 COLD。WARM/HOT 执行中失败
时先恢复旧 profile；快速恢复失败再用完整 COLD recovery 恢复旧 profile，并把原始错误返回
调用方。

## 当前性能证据

最终目标板一轮双向 HIL：

| Mode | 30→1 API | 1→30 API | RAW/IDR 最慢可用 | 切换内 ISP Device destroy |
| --- | ---: | ---: | ---: | --- |
| COLD | 2.154947s | 3.407023s | 3.780472s | 约 0.999s |
| WARM | 1.101895s | 2.257506s | 2.662667s | 0 |
| HOT | 0.504283s | 2.240004s | 2.288696s | 0 |

HOT 主要优化 30→1；更关键的 1→30 相比 WARM 只改善约 18ms。当前推荐保持 COLD
生产默认，优先推进 WARM 的 24h 长稳、温循、低照/长曝光、图像一致性、日夜/IR、功耗仪和
故障注入资格验证；HOT 暂不转为生产默认。

## Supersedes

本文是以下旧实验入口文档的替代候选：

- `pcr02-active-low-1-warm-switch-experiment-20260728`
- `pcr02-active-low-1-hot-switch-experiment-20260728`

旧文档应标记为 superseded，不再作为当前配置或 runbook 来源。

## Provenance

- last_verified：2026-07-29
- source：当前项目源码、配置解析、主机 contract test、ARM 构建和目标板 HIL
- owner：team-core
- status：reviewing，等待模块 owner 复核
- sanitization：不包含设备地址、共享目录、凭证或原始长日志
