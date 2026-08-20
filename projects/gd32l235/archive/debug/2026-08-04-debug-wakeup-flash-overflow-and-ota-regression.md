---
id: gd32l235-debug-wakeup-flash-overflow-ota-regression-20260804
title: GD32L235 调试唤醒诊断 Flash 溢出与 OTA 回归记录
kind: debug-record
domain: projects/gd32l235
path: projects/gd32l235/archive/debug/2026-08-04-debug-wakeup-flash-overflow-and-ota-regression.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-derived-debug-summary
  from: workspace://gd32l235 implementation and verification
  source_sha256: e82de95fb7672d5203f7d28700ca3e8b9cd14686fd567020a5d9cd3c4edc4f7c
  temporary_source_retained: false
review_after: '2026-10-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- debug-uart
- wakeup-diag
- flash-headroom
- ota-regression
validation_refs:
- projects/gd32l235/archive/debug/2026-08-04-debug-wakeup-flash-overflow-and-ota-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/debug/2026-08-04-debug-wakeup-flash-overflow-and-ota-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 记录 GD32L235 debug-uart 与 wakeup-diag 叠加导致 App 分区溢出的根因、紧凑诊断修复，以及生产 OTA 4 KiB headroom 和完整构建门禁未回归的证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 调试唤醒诊断 Flash 溢出与 OTA 回归记录

## 背景与边界

- Captured at: 2026-08-04（Asia/Hong_Kong）。
- Source: `workspace://gd32l235` 当前工作区源码、构建脚本与契约测试。
- Scope: 修复同时启用 `--debug-uart-printf --wakeup-diag` 时 App 链接区溢出，并证明生产 OTA 路径未受影响。
- Sanitization: 仅记录源码策略、构建配置、尺寸和验证命令；不保存原始日志、二进制、凭据、临时目录或私有端点。

## 现象与根因

用户命令在 App 链接阶段失败：App 区上限为 51200 B，当前工作区最初达到 51744 B，超出 544 B。干净 HEAD 在相同调试配置下也会超出 316 B，因此根因不是单个功能改动，而是两个诊断开关叠加后，带字段名和事件名的格式化字符串超过固定 App 分区预算；本次电源收敛改动增加了剩余 228 B 压力。

生产配置和只启用 `--debug-uart-printf` 的配置均未溢出。没有通过扩大 App 分区、削弱 Stage0/Stage1、改变 OTA 元数据或修改 linker layout 来规避问题。

## 修复策略

- `App/wakeup.c` 的诊断输出改为紧凑统一记录：`TAG tick value0 value1`，事件源、丢弃原因和组合状态使用数值编码。
- `App/bsp.c` 在 `WAKEUP_DIAG_LOG_ENABLED` 下输出数值型 `PWR_EVT event`，并让可读事件名表在该配置中不参与编译；普通 debug-only 配置仍保留可读名称。
- `WAKE_SHADOW` 保留具名字段，便于 shadow 验证；文档同步给出解码映射。
- 修复复审发现的重复 `APP_EXITED(FAST)` 问题：已进入 `BOOT_WAIT_READY` 后的重复同代确认不得刷新 30 秒超时；通过复用公共状态进入函数抵消新增代码尺寸，避免触发生产 OTA 4 KiB headroom 门禁。
- 生产构建所需的 wake drop reason 枚举保持在诊断条件编译之外，确保关闭诊断时仍可编译。

## 验证证据

精确复现用户链路并通过：

```text
rtk python3 Tools/Firmware/fwtool.py build --generator ninja --build-dir build/gcc-ninja --debug-uart-printf --wakeup-diag --fresh
rtk python3 Tools/Firmware/fwtool.py merge --build-dir build/gcc-ninja --output-dir build/gcc-ninja/merged
rtk python3 Tools/Firmware/fwtool.py package --build-dir build/gcc-ninja --output-dir build/gcc-ninja/package --package-name gd32l235_debug
rtk python3 Tools/Firmware/fwtool.py check --scope all --build-dir build/gcc-ninja --package-dir build/gcc-ninja/package --package-name gd32l235_debug
```

- debug + wakeup diag：Stage0 2280 B，Stage1 12936 B，App 50824/51200 B，物理余量 376 B；merge、package、check 均通过。该 profile 按策略为 `otaEligible=false`，只用于调试。
- 生产全门禁：`rtk env BUILD_DIR=build/codex-full bash scripts/codex-check.sh --full` 通过；App 46984/51200 B，余量 4216 B，高于生产 OTA 要求的 4096 B；`otaEligible=true`、`flashHeadroomPass=true`。
- shadow profile：`--debug-uart-printf --wakeup-diag --wifi-wake-shadow` 构建通过，App 51000/51200 B，余量 200 B。
- `rtk git diff --check` 通过；契约测试、生产构建、打包和完整 fwtool check 均通过。
- 仅有厂商 GD 驱动中的已知 allowlist warning，不是本次新增问题。

## 兼容性、风险与回退

- OTA 协议、分区、Stage0、Stage1、`firmware_common` 和生产包格式未修改；生产 OTA 尺寸门禁有 120 B 安全裕量。
- 兼容性变化仅限显式启用 `--wakeup-diag` 时的诊断文本格式，已同步文档和契约测试；生产 UART 协议不受影响。
- 尚未执行真实板级/HIL、daemon 与 MCU 的完整反复拨动验证。软件验证不能替代 PA8、PA15 和 UART 波形确认。
- 回退诊断紧凑格式会重新引入当前调试组合的链接溢出；若必须恢复旧文本，应先提供新的诊断容量方案，不能挤占生产 OTA 4 KiB headroom。

## 治理状态

- Archive candidate: reviewing。
- Memory candidate: no；不提升为常驻规则。
- Provenance: 只证明 2026-08-04 当前工作区与上述配置的验证结果，不作为未来分支的永久构建证明。
