---
id: daemon-ota-uart-lease-validation-2026-08-04
title: daemon 与 prog_ota UART 独占租约验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-08-04-daemon-ota-uart-lease-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session
  from: xcrz_sigmastar_demo
  source_sha256: b323638d52eb93a313a829a8d972d35420d8692b1a739cdb282663fce08415ae
  temporary_source_retained: false
review_after: '2026-11-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- validation
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-08-04-daemon-ota-uart-lease-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-08-04-daemon-ota-uart-lease-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 验证 daemon 电源开关兜底接管与 prog_ota 的共享 UART 租约，保持 OTA 原有流程和状态契约。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- daemon 与 prog_ota UART 独占租约验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# daemon 与 prog_ota 的 UART 独占租约验证

- Source: xcrz_sigmastar_demo 工作区的 daemon、app_ota、pcr02 联调改动
- Captured at: 2026-08-04 Asia/Hong_Kong
- Status: reviewing
- Scope: `/dev/ttyS1` 在 daemon 电源开关兜底接管与 `prog_ota` 之间的互斥

## 背景

daemon 在 `prog_pcr02` 因 MCU 电源开关安全退出后，会短暂接管 `/dev/ttyS1`，用于继续响应 MCU 的 TARGET_STATE/APP_EXITED 协议。仅检查 `/tmp/prog_ota.lock` 再打开 UART 存在 check-to-open 竞态：OTA 可能在检查之后取得进程锁并打开同一个 UART。

## 决策

- daemon 与 `prog_ota` 共同使用 `/tmp/pcr02_uart.lock` 的 `flock(LOCK_EX)` 作为 UART 独占租约。
- daemon 非阻塞获取租约；租约忙或检测到 OTA、业务进程、产测进程、模式切换时立即让出，不在 supervisor 循环中等待。
- `prog_ota` 保持原顺序：包预检、`/tmp/prog_ota.lock`、重复包检查、停止父进程，然后最多等待 6 秒取得 UART 租约，再初始化 HDI/UART。
- 两端均使用 `O_CLOEXEC` 打开租约文件，避免租约泄漏给 OTA 脚本或子进程。
- 所有 UART 实例都在释放租约前关闭；OTA 原进程锁最后释放。重启失败后的 APP_READY 临时 UART 恢复也必须先取得租约。

## OTA 兼容边界

- 不新增或修改 OTA phase/status 值。
- 不改变升级包格式、预检、重复包判断、版本策略、电机/MCU/SoC 升级顺序和退出码语义。
- UART 租约失败复用既有 `APP_RUNTIME_INIT_FAILED` 和恢复重启路径。
- 新旧 daemon 与新旧 `prog_ota` 混装不能提供完整的跨进程互斥保证，因此正式部署应同步更新两个二进制。

## 验证

- daemon、app_ota、pcr02 三个目标均完成交叉构建。
- 契约测试验证 OTA 原顺序、双方 acquire-before-open、close-before-release、Linux `flock` 排他和释放后接管。
- OTA shell 脚本语法检查通过；app_ota skill 快速校验通过；相关仓库 `git diff --check` 通过。
- 产物字符串确认 daemon 与 `prog_ota` 均包含 `/tmp/pcr02_uart.lock`。

## 剩余风险与硬件验收

静态、行为契约和交叉构建不能替代真机 OTA。发布前需要在同一套新 daemon/new `prog_ota` 镜像上至少执行：正常 OTA、daemon 正在兜底接管时触发 OTA、OTA 失败恢复、SoC 升级脚本接管四类冒烟，并确认 UART 无双开、phase/status 与旧版一致、升级后版本正确。

## Provenance

本记录由本地源码 diff、构建产物和契约测试归纳生成；未包含原始日志、固件二进制、凭据或运行时敏感数据。
