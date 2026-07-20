---
last_verified: '2026-07-14'
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-st77912-black-screen-esd-root-cause-20260714
title: PCR02 ST77912 黑屏与 LCD ESD 根因记录
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-07-14-st77912-black-screen-esd-root-cause.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: field-debug
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-10-14'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- st77912
- lcd
- esd
- black-screen
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-14-st77912-black-screen-esd-root-cause.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- 0001-fix-display-ST77912.patch reverse apply check
- modules/sensor/display/display.patch reverse apply check
evidence_strength: strong-field-a-b-with-hardware-eco-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-14-st77912-black-screen-esd-root-cause.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- 同一最新固件下移除 LCD ESD 器件后显示恢复
- 当前显示优化工作区与两份 patch 的反向应用校验
created_at: '2026-07-14'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-14'
manual_validation_pending: true
manual_validation_reason: 硬件 ESD 设计修改后仍需补冷启动、重启、高温与 ESD/EMC 回归
summary_zh: 实机移除 LCD ESD 器件后双屏恢复显示，黑屏根因收敛到硬件 ESD 支路；ST77912 fbtft patch 与 sensor/display 改动属于残影和 CPU 优化，不能作为黑屏临时改动回退。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 ST77912 黑屏与 LCD ESD 根因记录

## 现象

- 安装最新固件后，两块 ST77912 LCD 无显示。
- 此前软件侧只读检查可见 framebuffer 有有效、动态变化的像素内容，LCD SPI 路径有活动，背光与 reset 状态正常。
- 在固件和显示软件不变的条件下，移除 LCD ESD 器件后屏幕恢复正常显示。

## 影响范围

- 项目：PCR02。
- 硬件路径：双 ST77912 LCD 及其 ESD 保护支路。
- 软件路径：LVGL -> DisplayProvider -> `/dev/fb0`、`/dev/fb1` -> fbtft/ST77912 -> MSPI。
- 本记录不包含设备 IP、完整 raw log、固件二进制或客户材料。

## 环境

- 固件：2026-07-13 构建的最新验证固件。
- LCD：双 240x240 RGB565 ST77912。
- 内核配置：两个 ST77912 节点使用 54MHz、25fps。
- 应用配置：`full_refresh=0`，启用局部刷新与应用层 staging。
- 排查边界：设备侧只读 ADB 取证；未通过软件写寄存器或强制刷屏改变现场条件。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-13 | 安装最新固件并检查显示链路 | LCD 无可见显示，但 framebuffer 内容、SPI 活动、背光与 reset 证据不支持“应用未渲染” |
| 2026-07-14 | 硬件侧移除 LCD ESD 器件，保持固件不变 | LCD 恢复正常显示 |
| 2026-07-14 | 重新审计显示相关工作区 diff 与 patch | 两组改动均属于残影/CPU 优化，不存在可独立识别的“黑屏专属临时源码改动” |

## 证据

1. 现场 A/B 证据
   - A：最新固件 + 原 LCD ESD 支路，LCD 无显示。
   - B：同一固件移除 LCD ESD 器件，LCD 恢复显示。
   - 该对照直接改变硬件 ESD 支路，软件版本未变，因果指向硬件侧。
2. 软件链路证据
   - framebuffer 含有效且变化的 RGB565 图像数据，说明 LVGL/DisplayProvider 已产生输出。
   - LCD SPI 路径有传输活动，背光开启，reset 为释放状态。
   - 这些证据不能单独证明面板电气链路正常，但可排除“应用完全未渲染”。
3. 工作区边界证据
   - 父仓 `0001-fix-display-ST77912.patch` 与 6 个目标文件的当前 diff 完整匹配，反向应用检查退出码为 0。
   - `modules/sensor/display/display.patch` 与 3 个 DisplayProvider 目标文件的当前 diff 完整匹配，反向应用检查退出码为 0。
   - 两组目标文件的 `git diff --check` 均通过；`git diff --quiet` 均返回 1，证明优化改动仍然存在、未被误回退。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 最新固件没有产生 LCD 图像 | 读取 framebuffer 内容并观察动态变化 | framebuffer 有有效动态像素 | 排除 |
| 背光或 reset 未正确工作 | 只读检查 PWM/GPIO 状态 | 背光开启、reset 已释放 | 排除为主因 |
| ST77912 残影/CPU 优化 patch 导致黑屏 | 保持同一固件，仅移除 LCD ESD 器件 | 显示恢复 | 反证，不成立 |
| LCD ESD 支路对信号或供电产生异常影响 | 移除 ESD 器件做硬件 A/B | 同一固件恢复显示 | 当前根因 |

## 根因

当前根因收敛为 LCD ESD 器件或其硬件支路异常。移除该器件后，在同一软件条件下显示恢复，因此黑屏不是 `0001-fix-display-ST77912.patch` 或 `modules/sensor/display` 优化的直接结果。

具体器件失效模式仍需硬件团队确认，例如器件选型、寄生电容、漏电、焊接或布局对 LCD 信号/电源的影响。本记录不替代示波器、电气参数与 ESD/EMC 复验。

## 修复或规避

- 临时验证：移除 LCD ESD 器件后显示恢复。
- 正式处理：由硬件团队修改 ESD 设计、器件或布局，并完成样机回归。
- 软件处理：
  - 保留 `0001-fix-display-ST77912.patch`；其归属是 ST77912 双屏残影与刷新/CPU 优化。
  - 保留 `modules/sensor/display` 的 staging、局部 dirty 合并与双屏交错 flush 优化。
  - 不以“消除黑屏风险”为由整体回退上述两组改动。
  - patch 内 SPI0/QSPI pad-drive 子改动不属于 LCD MSPI 数据路径，应作为独立子系统风险单独评审；该边界不构成黑屏回退依据。

## 验证

| 命令或动作 | 退出码/结果 | 结论 |
| --- | ---: | --- |
| 同一固件下移除 LCD ESD 器件 | 显示恢复 | 硬件 A/B 支持 ESD 根因 |
| `rtk git apply --reverse --check 0001-fix-display-ST77912.patch` | 0 | 父仓显示优化 patch 完整保留 |
| `rtk git diff --check -- <6 个 patch 目标文件>` | 0 | 父仓目标 diff 无空白错误 |
| `rtk git diff --quiet -- <6 个 patch 目标文件>` | 1（预期） | 目标优化改动仍存在 |
| `rtk git apply --reverse --check display.patch`（`modules/sensor`） | 0 | DisplayProvider 优化 patch 完整保留 |
| `rtk git diff --check -- display/com/display_com.h display/display_provider.cpp display/display_provider.h` | 0 | sensor/display 目标 diff 无空白错误 |
| `rtk git diff --quiet -- display/com/display_com.h display/display_provider.cpp display/display_provider.h` | 1（预期） | sensor/display 优化仍存在 |

### 离线待验证（可选）

```yaml
manual_validation_pending: true
manual_validation_reason: 硬件 ESD 设计修改后尚未完成整机回归
required_followup:
  - 双屏冷启动与连续重启
  - 静止画面、局部动画与双屏高负载动画
  - 高低温老化
  - ESD/EMC 与信号完整性复验
  - 确认内核无 ST77912/MSPI 传输异常
owner: leiwenjun
review_after: 2026-10-14
```

## 后续动作

1. 硬件团队完成 ESD 设计修改并记录器件、原理图与 PCB 变更。
2. 使用包含现有残影/CPU 优化的固件完成冷启动、重启、动画、高温与 ESD/EMC 回归。
3. 单独评审 patch 内 SPI0/QSPI pad-drive 变更，避免把 flash/QSPI 风险与 LCD MSPI 优化绑定。
4. 硬件回归闭环前保持本条目为 `reviewing` candidate，不提升为 active 决策。

## 边界

- 本条目是项目历史 debug-record，不是通用硬件规范。
- 不授权软件发布、固件刷写、owner decision 或 active promotion。
- 如果后续硬件复验推翻 ESD 根因，应以新证据更新或 supersede 本条目，而不是静默改写历史。
