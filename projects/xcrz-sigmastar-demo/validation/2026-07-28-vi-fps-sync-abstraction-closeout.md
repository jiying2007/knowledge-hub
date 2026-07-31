---
id: pcr02-vi-fps-sync-abstraction-closeout-20260728
title: PCR02 VI 1/30fps 同步抽象规范收敛验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-sync-abstraction-closeout.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-validation-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: 352e43738d39dcf7a12fe86340190fa120137c9ac85817e503296df392d31bdd
  temporary_source_retained: false
review_after: '2026-08-28'
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
- osal
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-sync-abstraction-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-sync-abstraction-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 1/30fps consumer 的 pthread/compiler atomic 已收敛到 VSHDIOS，并完成主机、ARM 与板级复验；遗留平台边界另列。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 VI 1/30fps 同步抽象规范收敛验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 VI 1/30fps 同步抽象规范收敛验证

## 范围

本轮复审近期 1/30fps 管线提交中新引入的同步、线程和原子操作，目标是把 HDI/app consumer
统一收敛到项目 `VSHDIOS` OSAL。未改写已推送历史，未改变生产默认 COLD、WARM/HOT opt-in
资格、公共 ABI 或 profile/demand 语义。

## 问题与修正

- VI consumer 直接使用 `pthread_mutex_lock/unlock/trylock` 和 `__atomic_*`，绕过 OSAL。
  相关 mutex/atomic 改为 `VSHDIOS_Mutex*`、`VSHDIOS_Atomic*`，同步资源绑定 VI
  Init/DeInit，并在局部创建失败时只回滚本次资源。
- LDC prewarm 直接使用 `pthread_create/join`。改为 `VSHDIOS_ThreadCreate` 和
  `VSHDIOS_ThreadDestroyJoin`，保留 join 失败即 topology invalid 的安全行为。
- app diag H26x stats 使用静态 pthread mutex 且无 provider 生命周期。改为 ModuleUp/Down
  创建销毁 OSAL mutex，provider 退出时只回收自己创建的 reader。
- host pipeline test 增加负向门禁，禁止目标 consumer 再引入直接 pthread
  mutex/thread 或 compiler atomic builtin。

## 验证

- 目标 consumer 的 `pthread_create/join`、`pthread_mutex_lock/unlock/trylock`、
  `__atomic_*`、`__sync_*` 静态扫描零命中。
- pipeline host test 以 `-Wall -Wextra -Werror` 通过，包含新增同步抽象门禁。
- HDI/app ARM object 构建通过；app_test、app_tool、主应用依次强制复链通过。
- 参考板 COLD/WARM/HOT 的 MAIN+SUB+RAW 双向单轮均通过，route 分别为 5/6/1，
  PTS rollback 为 0，1fps 的 LDC、soft-light、VIF sleep 保持关闭。
- 设备诊断 smoke 通过；内核日志未匹配 CMDQ error/fail/timeout、recursive reset 或
  output task status 告警。
- LDC prewarm OSAL thread join 返回成功，观测 join wait 为百微秒量级。

## 本地提交

- HDI `93b04e8`：统一 VI 同步与线程抽象。
- app `45d84a7`：统一 VI 诊断同步抽象。
- app_test `9dc49b7`：修正线程抽象日志命名。
- 根工程 `4c73d26d`：增加同步抽象调用门禁。

以上提交均未推送。

## 边界与剩余风险

- `hdi_os` backend 内部必须保留 pthread/compiler builtin，它是 OSAL 的平台实现，不属于
  consumer 禁止范围。
- VI 文件仍有旧检测区域/OSD pthread 存储或平台 font 接口要求的 pthread mutex；不是本轮
  1/30fps 提交引入，需独立迁移和 OSD 回归，不能宣称全文件 pthread 已清零。
- VENC 唤醒仍使用 Linux `eventfd`；当前 OSAL 无等价 fd/event 接口，属于 HDI 平台边界。
- 官方 diag layer/naming 检查脚本及其编码规范引用在工作树缺失，因此该项没有执行证据。
- 根构建系统同时请求 library/app 多目标时可能用旧 library 先链接；本轮最终证据采用先构建
  module library、再逐 app 强制复链的顺序，依赖图仍需仓库 owner 治理。
- 仍需模块 owner 人工复审；WARM/HOT 的量产资格仍依赖长稳、温循、故障注入、图像和功耗验证。

## Provenance

- 日期：2026-07-28
- 来源：项目代码复审、主机测试、ARM 构建和参考板硬件在环复验
- 生成方式：AI 辅助整理，状态保持 reviewing，未授权 active promotion
