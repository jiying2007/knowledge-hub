---
id: gd32l235-power-diag-independent-build-switch-20260804
title: GD32L235 Power Diag 独立构建开关决策
kind: decision
domain: projects/gd32l235
path: projects/gd32l235/decisions/power-diag-independent-build-switch.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-session-summary
  from: workspace://gd32l235 implementation and verification
  source_sha256: 4f457a3c4bf687213e6aa341f24a2bd5852624f134e9054402d6a5d47989edf4
  temporary_source_retained: false
review_after: '2026-10-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- power-diag
- debug-uart
- build-profile
- ota-regression
validation_refs:
- projects/gd32l235/decisions/power-diag-independent-build-switch.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/decisions/power-diag-independent-build-switch.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 决定将 Bsp_PowerDiag_Log 改为默认关闭的独立构建能力：新增 --power-diag，固定数值事件格式，不再由 debug-uart 或 wakeup-diag 隐式启用，并保留生产 OTA 4 KiB
  headroom 门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- GD32L235 Power Diag 独立构建开关决策
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# GD32L235 Power Diag 独立构建开关决策

## 决策范围

- Captured at: 2026-08-04（Asia/Hong_Kong）。
- Source: `workspace://gd32l235` 当前实现、构建配置、契约测试与尺寸门禁。
- Scope: `Bsp_PowerDiag_Log` 的编译开关、输出格式和 fwtool 入口。
- Supersedes candidate: 取代 `projects/gd32l235/archive/debug/2026-08-04-debug-wakeup-flash-overflow-and-ota-regression.md` 中“Power Diag 格式由 wakeup diag 决定”的部分；不改变该记录的历史构建事实。
- Sanitization: 不含原始日志、二进制、凭据、临时路径或设备数据。

## 决策

1. 新增独立 CMake 开关 `GD32L235_POWER_DIAG_LOG_ENABLED`，默认关闭，并通过 target-wide 宏 `BSP_POWER_DIAG_LOG_ENABLED` 同时控制公共声明、调用方 no-op 和函数实现。
2. fwtool 新增 `--power-diag`；Power Diag 依赖 Debug UART 作为输出通道。开启 `--power-diag` 而未开启 `--debug-uart-printf` 时，CMake 必须拒绝配置。
3. `--debug-uart-printf` 和 `--wakeup-diag` 均不再隐式启用 Power Diag。
4. Power Diag 开启后固定输出紧凑数值事件 `PWR_EVT ... event=<0..17> ...`；删除 `Bsp_PowerDiag_EventName` 和事件名称字符串表，不保留旧文本格式兼容。
5. OTA 协议、Flash 分区、Stage0/Stage1、升级元数据和生产包格式保持不变。

## 迁移与兼容性

这是显式 breaking change：原先只使用 `--debug-uart-printf`，或使用 `--debug-uart-printf --wakeup-diag` 的镜像不再输出 `PWR_EVT`。需要电源状态日志时改为：

```text
rtk python3 Tools/Firmware/fwtool.py build --debug-uart-printf --power-diag ...
```

同时需要唤醒日志时追加 `--wakeup-diag`。Power Diag 的 `event` 只按 `App/bsp.h` 中的数值定义解码。

## 验证

- 契约测试：`check_application_debug_uart.py`、`check_boot_reset_diagnostics.py`、`check_wakeup_diagnostics.py`、`check_charge_cert_build_guard.py` 全部通过。
- 负路径：单独使用 `--power-diag --configure-only --fresh` 被 CMake 正确拒绝，错误原因是缺少 `GD32L235_DEBUG_UART_PRINTF=ON`。
- 原用户 wakeup profile：`--debug-uart-printf --wakeup-diag` 构建通过，App 50488/51200 B，余量 712 B；merge、package、check 全部通过。
- 最坏组合：`--debug-uart-printf --power-diag --wakeup-diag` 构建通过，App 50824/51200 B，余量 376 B。
- 生产全门禁：`rtk env BUILD_DIR=build/codex-full bash scripts/codex-check.sh --full` 通过，App 46984/51200 B，余量 4216 B；`otaEligible=true`、`flashHeadroomPass=true`。
- `rtk git diff --check` 通过；仅有厂商 GD 驱动的既有 allowlist warning。

## 风险与回退

- 调试工具若仍依赖事件名称字符串，需要切换到数值映射；旧文本解析器不会兼容。
- 最坏调试组合只剩 376 B，不宜继续增加诊断字符串。
- 尚未进行板级 UART 输出核验；软件构建与契约测试不能代替实机日志解析确认。
- 回退时应整体撤销独立开关和 CLI 入口；不得通过扩大 App 分区或占用生产 OTA 4 KiB headroom 恢复旧格式。

## 治理状态

- Decision candidate: reviewing。
- Memory candidate: no。
- Provenance: 只证明 2026-08-04 当前工作区和上述构建配置。
