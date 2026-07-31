---
id: pcr02-vi-fps-full-optimization-closeout-20260728
title: PCR02 1/30fps Pipeline全量整改与板级验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-full-optimization-closeout.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-validation-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: eb7be545254ef9b23700983ffaafcb37e6cd57099946569c98380011c8a146d5
review_after: '2026-08-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- vi
- 1fps
- 30fps
- pipeline
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-full-optimization-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-full-optimization-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 完成1/30fps Pipeline架构、OSAL规范、严格诊断、资源编排和COLD/WARM/HOT板级验证；WARM/HOT切换内不再销毁ISP Device，最终deinit保留完整释放语义。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 1/30fps Pipeline全量整改与板级验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 1/30fps Pipeline 全量整改与板级验证摘要

## 范围

本记录总结 `ACTIVE_LOW_1`（真实 1fps）与 `NORMAL_30`（真实 30fps）在线切换的
架构、代码规范、诊断、测试和目标板验证结论。SOC 始终保持 Active，不使用平台
AOV/suspend 语义。

本文只保留可复用的工程结论和脱敏指标，不包含设备地址、共享目录、账号、凭证或
原始长日志。

## 最终运行契约

- 仅保留两个 profile：
  - `NORMAL_30`：30fps；LDC 按设计启用；H26x 无业务流时强制白天，存在业务流且
    充电时才允许根据硬光敏或软光敏执行日夜切换。
  - `ACTIVE_LOW_1`：1fps；LDC、软光敏、VIF sleep 全部关闭并默认白天；RAW 和
    VENC 严格按需。
- MAIN/SUB H26x 使用显式 stream gate 和 owner。诊断 owner 不能抢占业务 owner，
  无需求时不创建或维持编码链路。
- 业务入口显式选择 `COLD`、`WARM` 或 `HOT`，不通过环境变量或隐含状态决定路由。
- 运行时 graph 必须由 journal、资源句柄和真实 enable/bind 状态重建，并与 planner
  目标 graph 做 exact equality；切换完成和回滚完成都必须执行该门禁。
- 清理失败时保留首个错误码，同时记录完整 cleanup failure bitmap；COLD 回滚不得把
  混合拓扑伪装成成功状态。

## 关键整改

### 平台抽象与代码规范

- 1/30fps 相关 HDI、ISP、OSD、sensor 路径的 mutex、thread、join 和 atomic 操作统一
  收口到 `VSHDIOS_*`；业务实现不再直接调用 `pthread_mutex_*`、
  `pthread_create/join` 或 `__atomic_*`。
- OSD 字体锁也迁移到 OSAL，避免同一媒体链路存在两套同步抽象。
- `VSHDIVI_IspGetDebugState` 使用显式 ABI version、feature bitmap 和结构体 size，
  调用方必须传入并校验 size。
- 公共枚举、错误码和 switch mode 代替魔法数字；公共 HDI 头文件执行双副本一致性
  校验。

### Pipeline 与资源编排

- planner graph 纳入 stream fps、frame count、RAW/YUV/JPEG/BMP 等实际需求，精确
  描述 port、bind、LDC、VENC 和 owner。
- `NORMAL_30` 只启用实际使用的 ISP port1；`ACTIVE_LOW_1` 只启用实时低吞吐链路所需
  的 ISP port0，删除“planner 声明一个端口、executor 多开另一个端口”的漂移。
- SCL port 枚举是 bit index，运行时 mask 必须通过置位构造，不能直接对枚举值按位或。
- 11 个清理步骤可逐项注入失败并验证恢复，不依赖单一 happy path。

### 诊断与测试

- 诊断 JSON 改为严格 parser：拒绝重复顶层 key、嵌套替代、尾随字符、截断、非法
  Unicode 和整数越界；输出统一执行 JSON escaping。
- HIL 命令独立成测试组件，参数为：
  `vi_fps_hil [cycles] [dwell_ms] [none|main|sub|both] [timeout_ms] [cold|warm|hot]`。
- 每次 HIL 同时校验 route、debug ABI、runtime mask、VENC owner、LDC、光敏、
  VIF sleep、RAW 首帧、MAIN/SUB 首个 IDR 和 PTS 单调性。

## 目标板最终结果

当前源码重建并重新同步测试程序后，COLD、WARM、HOT 各完成一次双向切换，均返回
PASS；route 分别为 5、6、1，MAIN/SUB 首帧均为 IDR，PTS rollback 为 0，实际 topology
与目标 graph 一致。

| 路由 | 30→1 API | 1→30 API | RAW/IDR 最慢可用时间 | 切换内 ISP Device destroy |
| --- | ---: | ---: | ---: | --- |
| COLD | 2.154947s | 3.407023s | 3.780472s | 约 0.999s |
| WARM | 1.101895s | 2.257506s | 2.662667s | 0 |
| HOT | 0.504283s | 2.240004s | 2.288696s | 0 |

最终 `VSHDIVI_DeInit` 的完整 ISP Device 释放仍需约 1.44–1.53s。这是进程退出或完整
销毁阶段，不是 WARM/HOT profile 切换路径。常驻应用应通过 WARM/HOT 保留可安全复用
的 ISP Device 来避开切换内 deinit；不能通过跳过最终 deinit 或泄漏资源来缩短退出时间。

严格诊断 JSON smoke 返回成功。最终内核日志窗口未发现 CMDQ error/fail/timeout/reset、
recursive reset、`CheckOutputTaskStatus`、segfault、fatal 或 assert。

## 负例驱动的根因

1. 首次 exact graph 门禁暴露 executor 多启用了未声明的 ISP port。修正为每个 profile
   只启用一个实际端口后，模型和硬件状态一致。
2. 第二次门禁暴露 SCL mask 的 expected/actual 不一致。根因是把 bit index 当 bit mask
   使用，改为显式置位后 COLD/WARM/HOT 全部通过。

这两个负例证明 exact runtime gate 不能删除：若只观察 API 返回和图像，拓扑漂移会被
隐藏并在后续切换或清理阶段放大。

## 验证范围

- 主机单元测试：
  - HDI pipeline 与 11 步 cleanup failure matrix；
  - sensor 日夜/充电/H26x gate policy；
  - app 诊断严格 JSON parser。
- ARM 构建：
  - HDI、app、sensor；
  - `app_test`、`app_tool`、主应用。
- 静态门禁：
  - 目标路径禁止直接 pthread/compiler atomic；
  - profile 固定为 30/1；
  - 公共头文件一致；
  - 涉及仓库 `git diff --check`。
- HIL：
  - COLD/WARM/HOT 双向切换；
  - RAW、MAIN/SUB IDR、PTS、runtime graph；
  - 严格 JSON smoke 和内核错误扫描。

详细证据索引、构建哈希和历史验证过程保存在项目相对路径：

- `docs/changes/hdi-vi-active-low-1/VERIFICATION.md`
- `docs/changes/hdi-vi-active-low-1/ARTIFACT_MANIFEST.md`
- `docs/changes/hdi-vi-active-low-1/REVIEW.md`

## 剩余发布门禁

- 当前结果证明功能、拓扑一致性和单轮板级切换正确，不等价于量产发布批准。
- 发布前仍应补充长稳循环、功耗仪表实测、真实日夜/IR 场景、编码消费者异常退出和
  多次失败注入后的板级恢复验证。
- 项目工作区包含用户原有修改；提交前需按模块审查并只纳入本轮目标文件。
- 本记录由 AI 辅助整理，状态应保持 reviewing，等待模块 owner 复核。
