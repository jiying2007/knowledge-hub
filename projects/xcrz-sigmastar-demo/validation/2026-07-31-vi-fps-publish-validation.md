---
id: pcr02-vi-fps-publish-validation-20260731
title: PCR02 1/30fps 优化提交推送与最终验收
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-31-vi-fps-publish-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-validation-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: 0fdfafafbffb932cd81fe63001938211cf68923a9bdacc881bf03c5831613d10
  temporary_source_retained: false
review_after: '2026-08-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- validation
- vi
- 1fps
- 30fps
- publish
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-vi-fps-publish-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-vi-fps-publish-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 1/30fps 优化已完成跨仓库提交推送、最新依赖重建与5轮板级验收；远端哈希一致，仍待owner与量产扩展验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 1/30fps 优化提交推送与最终验收
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 1/30fps 优化提交推送与最终验收

## 背景与范围

本记录收口 PCR02 真实 1fps 与 30fps 在线切换优化的提交、跨仓库依赖同步、最终产物重建、板级硬件在环验收和远端发布。范围覆盖父仓库、HDI、APP、SENSOR 与 `app_test`；不包含量产批准、功耗仪表实测或长稳结论。

## 发布决策

- 父仓库原工作区存在用户 dirty 且与远端双向分叉，因此发布集成在基于最新 `origin/dev/pcr02` 的隔离 worktree 完成，未覆盖或清理用户变更。
- HDI、APP 和 SENSOR 功能分支先合并各自最新 `origin/master`，解决线程有界等待、UART ACK、IMU、低功耗、Common/Proto 等同期依赖。
- 父仓库跳过两版中间 `libhdi` 产物，只提交最新依赖集合重建的 HDI、APP、SENSOR 动态库和静态库。
- 公共 HDI/APP 头与模块头执行只读一致性检查，未发现 drift 或 stale header。

## 远端发布证据

- 父仓库 `dev/pcr02`: `f7894b197679ad6db84acc4c9b4f9e960e65b9c4`
- HDI `dev/video_fps`: `481190feea057c3d15fa21336b4f57940bed0f03`
- APP `dev/video_fps`: `9a5c4d385cd7644983f768e250cd58302b3f6da3`
- SENSOR `dev/video_fps`: `6001d9ab4a88659087bdadad7162f964edcdbc8b`
- `app_test` `master`: `16fba6a13cba409256c5bae92ac42db5dc2f3182`

推送后逐仓执行远端回读，五个本地发布提交均与对应远端分支哈希完全一致。

## 验证证据

- ARM 对象构建：HDI、APP、SENSOR 通过。
- ARM 库构建：HDI、APP、SENSOR 动态库和静态库通过。
- `app_test` 强制复链通过。
- 主机回归：
  - `hdi_vi_pipeline_test: PASS`
  - `app_diag_json_test: PASS`
  - `sensor_ir_policy_test: PASS`
- 最终测试程序 MD5：`96d3e403a1d08e2095f7faf1b3f97c11`；主机与设备端一致。
- 板级 HOT 双码流 1fps↔30fps 共 5 轮全部 PASS：
  - 最大切换耗时：886715 us
  - 最大 RAW 首帧：1024179 us
  - 最大主码流首个 IDR：1024470 us
  - 最大子码流首个 IDR：1026377 us
  - 主/子码流 PTS rollback：0/0
- 验收后的增量内核日志未发现 CMDQ reset/timeout、VIF failure、Call trace、Oops 或 panic，仅出现正常资源释放记录。
- 变更范围执行 `git diff --check` 与新增行敏感信息扫描，均通过。

## 接口与风险边界

- `VSHDIVI_IspGetDebugState` 调整为显式 `(state, size)`，属于源码级 breaking change；当前工作区调用方已全部迁移并通过构建，外部旧调用方需要同步传入结构体大小。
- 当前结果证明短周期功能、首帧时延、双码流 IDR、PTS 单调性和基础内核稳定性，不等价于量产批准。
- 仍需 owner 复核，并补充长稳循环、功耗仪表、真实日夜/IR、异常消费者退出和故障注入后的板级恢复验证。
- 官方 diag layer/naming 检查脚本在仓库中缺失，本轮以模块构建、JSON 回归、依赖扫描和设备验收补充证据，但不能声明该缺失门禁已执行。

## Provenance

- Source: 本次跨仓库提交、构建、定向测试、设备硬件在环验收与远端回读
- Topic: `vi-fps-publish-validation`
- Captured at: 2026-07-31
- Sanitization: 未记录设备地址、私有远端 URL、账号、凭证、原始长日志或二进制
- Verification: Git 远端哈希回读、三组主机测试、ARM 重建和 5 轮板级切换
- Memory Candidate: no
- Gate Result: pass；量产门禁仍待 owner 与扩展验证
