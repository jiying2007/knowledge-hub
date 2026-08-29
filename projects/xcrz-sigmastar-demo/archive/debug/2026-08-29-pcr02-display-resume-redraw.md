---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-display-resume-redraw-20260829
title: PCR02 充电待机亮屏后的显示恢复与全量重绘候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-29-pcr02-display-resume-redraw.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 来源为 2026-08-28 至 2026-08-29 的本地源码审查、日志摘要和代码审查反馈；未归档原始日志或设备信息。
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-11-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- display
- standby
- charging
- redraw
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-29-pcr02-display-resume-redraw.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-29-pcr02-display-resume-redraw.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-29'
updated_at: '2026-08-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-29'
manual_validation_pending: true
summary_zh: 记录充电待机后 APP 唤醒时显示恢复的代码级证据、screenOff 与渲染挂起解耦方案及 HIL 验收边界；尚未获得实机闭环证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 充电待机亮屏后的显示恢复与全量重绘候选

## 现象

已报告的复现路径为：设备低电进入智能留电模式；APP 唤醒后放上充电桩；APP 退后台，设备约一分钟后进入待机/熄屏；再次打开 APP 时设备可唤醒，但双眼显示异常或停在旧帧。

本记录不包含原始设备日志、网络端点、序列号、二进制或现场视频。

## 影响范围

- 项目：PCR02 SigmaStar SSC305。
- 关注模块：显示管理、背光控制、待机/充电后 RTSA 唤醒路径。
- 影响：显示恢复可出现异常；尚无证据证明设备主状态机、相机恢复或 APP 建链失败。
- 结论等级：`needs_evidence`。修复代码已经存在，但尚未通过目标设备 HIL 证明问题闭环。

## 代码级时间线

| 阶段 | 观察 | 结论 |
| --- | --- | --- |
| 待机退出 | task 日志记录亮度恢复、相机恢复和原始流恢复 | 排除“待机退出完全未执行”的假设 |
| Idle 恢复 | task 日志记录已下发默认正常眼神 | 排除“业务层没有下发眼神恢复请求”的假设 |
| 显示挂起 | 亮度为 0 时，显示线程进入 `suspend_` | 熄屏期间不再推进 LVGL 场景更新 |
| 动画请求 | 原实现允许动画请求直接清除 `suspend_` | 渲染挂起状态不再等价于物理背光熄屏状态 |
| 真实亮屏 | 若只依赖 `suspend_` 的 true→false 边沿，前一阶段会吞掉亮屏恢复重绘 | 这是独立代码审查确认的正确性缺陷 |

## 证据

- 源码证据：`modules/sensor/main/sensor_entry.cpp` 在背光成功设置后通知显示管理器；`modules/sensor/display/display_manager.cpp` 由显示线程执行 LVGL 全量失效。
- 代码审查证据：审查发现动画请求提前解除 `suspend_` 会导致后续真实亮屏漏掉 `resumeRedrawPending_`，判定为 medium correctness；已按该发现修复。
- 本地机械验证：执行 `rtk git diff --check` 与 `rtk make pcr02`，命令返回成功。
- 证据边界：构建输出不等同于设备部署；未执行 ADB 写操作、重启、镜像/OTA 制作或 HIL。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| APP 打开后未触发待机退出 | 检查 task 日志中的 RTSA START、Standby exit 和设备控制应答 | 恢复链路有记录 | 已排除 |
| 业务层未下发正常眼神 | 检查 Idle 显示状态日志 | 已记录默认正常眼神下发 | 已排除 |
| 熄屏后 framebuffer/LCD 保留局部旧帧而未在亮屏时全刷 | 审计显示挂起、背光和 LVGL invalidate 路径 | 代码级风险成立；需要 HIL 确认触发实际现象 | 待验证 |
| 动画请求吞掉真实亮屏重绘边沿 | 审查 `suspend_` 状态转换 | 已确认并已修复 | 已修复，待 HIL |

## 根因

现场现象的最终根因尚未确认。

已确认的代码缺陷是：使用单一 `suspend_` 同时表达物理熄屏和渲染挂起；动画请求可提前将其清为 false，使后续真实亮屏无法检测到恢复边沿，从而漏掉预期的全量重绘。

## 修复或规避

修复采用两个独立状态：

- `screenOff_`：仅反映背光命令对应的物理熄屏状态；
- `suspend_`：仅控制显示线程是否暂停渲染。

真实亮屏时，`screenOff_` 的 true→false 转换登记 `resumeRedrawPending_`；显示线程在下一轮对两个显示 root object 执行 `lv_obj_invalidate()`。动画请求可解除渲染挂起，但不修改 `screenOff_`，故不会吞掉后续亮屏全刷。

背光设置失败时不更新显示内部状态，避免硬件状态与软件状态进一步偏离。修复不会强制切换为普通眼神，也不应覆盖 OTA、抱起、跌倒等前台显示状态。

## 验证

### 已完成

- 代码审查发现已修复，逻辑上覆盖“熄屏 → 动画请求 → 真正亮屏”的边界。
- `rtk git diff --check`：通过。
- `rtk make pcr02`：命令成功返回。

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: 尚未在目标设备上完成原复现链路、5至10次短循环与显示日志采集；本地构建不证明LCD、Framebuffer和动画恢复行为。
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: '2026-11-29'
```

HIL 需按单次 smoke、5～10 次短循环逐级执行；前一级若出现 core、致命 dmesg、状态泄漏或设备身份漂移，不得扩大测试。验收时应观察以下日志语义：

```text
DisplayManager suspend=1
DisplayManager suspend=0, screen_off=0, resume_redraw_pending=1
DisplayManager: full redraw requested after screen resume
```

并确认双眼持续动画或跟随正常、无局部残留、无左右眼不一致，且高优先级业务表情未被普通眼神覆盖。

## 后续动作

1. 将含修复的 app 制品按 source/build/target 身份逐级核对后部署到受控测试设备；后编译 app 不会自动进入既有 image 或 OTA。
2. 收集最小脱敏 HIL 结果，补充单次与短循环的通过/失败证据。
3. HIL 通过后创建 validation 记录；若仍复现，保留本记录为 debug 入口并追加显示驱动/Framebuffer 证据。
4. 本记录不提升为通用规则、memory 或 active 决策。
