---
id: gd32l235-pb12-wl-gpio4-contract-20260812
title: GD32L235 PB12 WL_GPIO4 WoWLAN 引脚契约候选
kind: project-current
domain: projects/gd32l235
path: projects/gd32l235/current/pb12-wl-gpio4-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: user-correction-and-schematic-verification
  from: 2026-08-12 user correction, PCR02_MAIN_V2.0 schematic page 19, and workspace://gd32l235 source validation
  source_sha256: e28a8bdf2a0c9a71446d5de74607a0c49c8606259a8bcc866474c6ffe1828caf
  temporary_source_retained: false
review_after: '2026-11-12'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pb12
- wifi
- wowlan
validation_refs:
- projects/gd32l235/current/pb12-wl-gpio4-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/current/pb12-wl-gpio4-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 确认 PB12 连接 WiFi 模组 WL_GPIO_4，属于 WoWLAN 相关控制路径而非 SDIO_ENB；当前固件保持输出低电平且不动态切换。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- GD32L235 PB12 WL_GPIO4 WoWLAN 引脚契约候选
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# GD32L235 PB12 / WL_GPIO4 / WoWLAN 引脚契约候选

## 结论

- GD32L235 的 PB12（LQFP48 第 24 脚）连接 WiFi 模组 AP6303BH 的 `WL_GPIO_4`（模组第 39 脚），板级网络名为 `WL-GPIO4`。
- PB12 属于 WoWLAN 相关控制路径，不是 `SDIO_ENB`，也不是 SDIO 接口使能或失能信号。
- WiFi 模组的实际 WoWLAN 唤醒输出使用独立的 `GPIO_1/WOWL_WAKEUP` 网络，经板级转换后进入 MCU 的 PC12；PB12 与 PC12 职责不得混淆。
- 当前 GD32L235 固件把 PB12 配置为推挽输出并初始化为低电平，STANDBY、SLEEP、DEEP_SLEEP 状态转换不动态切换该引脚。本候选不新增或推断 PB12 的 WoWLAN 电平时序。

## 证据

- 用户于 2026-08-12 明确纠正 PB12 为 WiFi 模组 `WL-GPIO4`、WoWLAN 相关引脚。
- `PCR02_MAIN_V2.0_20251211.pdf` 第 19 页显示 MCU `WL-GPIO4` 网络连接 AP6303BH `WL_GPIO_4`，而 `GPIO_1/WOWL_WAKEUP` 使用独立的 `WIFI-WAKE-MCU` 网络。
- `workspace://gd32l235/App/wifi.c` 已核对 PB12 GPIO 配置；`workspace://gd32l235/Docs/IO功能说明.md` 和 `workspace://gd32l235/Docs/串口通信协议规范.md` 已同步纠正语义。

## 验证

- `rtk python3 Tools/tests/check_wifi_wl_gpio4_contract.py`：PASS。
- `rtk bash scripts/codex-check.sh --quick`：PASS。
- `rtk bash scripts/codex-check.sh --full`：PASS，包含 fresh build、package、全量仓库测试及 `fwtool check --scope all`。
- `rtk git diff --check`：PASS。

## 风险与边界

- 本候选不复制原理图正文或二进制，只记录脱敏网络关系、页码和验证摘要。
- PB12 后续若需要动态控制，必须补充 WiFi 模组规格、电平极性、转换时序和板级波形验证，不能从 `WL_GPIO4` 名称直接推断。
- 本条目状态应保持 `reviewing`，不代表板级 WoWLAN 动态时序已经签收。
