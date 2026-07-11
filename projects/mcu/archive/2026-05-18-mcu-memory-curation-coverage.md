# MCU memory-curation 覆盖归档 2026-05-18

## 摘要

本文从旧 Codex archive `memory-curation` 选择性迁移而来，保留 2026-05-18 MCU 相关 memory 审计中的长期工程线索。本文是 archive-only 历史记录，不代表当前固件版本、当前硬件验证、当前发布状态或当前工具链状态。

## HC32F072 历史线索

- `charge_hc32f072` 当时按 `HC32F072FAUA` 单 App 镜像维护，不套用 GD32L235 Stage0/Stage1 分区。
- 历史记录保留芯片封装、Flash/SRAM、J-Link/OpenOCD 相关维护线索，但当前硬件连接、烧录脚本和构建结果必须重新验证。
- HC32 相关 Codex 配置和 workflow 的更早迁移记录在 `projects/mcu/archive/2026-05-17-gd32-hc32-codex-maintenance-session.md`。

## MM32SPIN023C 历史线索

旧 memory-curation 中记录的 `mm32spin023c` 历史 layout 线索：

| 区域 | 历史值 |
| --- | --- |
| Flash 起始 | `0x08000000` |
| Flash 结束 | `0x08007FFF` |
| App 起始 | `0x08001800` |
| BootJumpFlag 地址 | `0x08001400` |
| BootJumpFlag 值 | `55 AA AA 55` |
| SRAM 起始 | `0x20000000` |
| SRAM 结束 | `0x20000FFF` |

这些是历史线索，不是当前 linker script、bootloader 或量产烧录权威。涉及烧录、OTA、产测或现场维护时，必须回到当前 `mm32spin023c` 源仓、当前 linker/script 和当前硬件验证记录。

## firmware-release-tools 历史线索

旧 memory-curation 与后续 session-wrap 共同指向以下发布治理规则：

- NAS 发布根目录使用 `<mcu-release-nas>/robot/mcu`。
- 同版本同内容发布应幂等复用；同版本不同内容必须失败，禁止自动覆盖。
- 发布 tag 应在 package/check/dry-run/validation 通过并写入发布目录后再创建或推送。
- 凭据文件只属于运行环境，不进入仓库、Hub 正文、manifest、日志或 memory。
- `firmware-release-tools` 的更完整历史会话保存在 `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`。

## 迁移边界

| Source | SHA256 | 行数 | 字节 | 处置 |
| --- | --- | ---: | ---: | --- |
| `domains/codex/archive/codex-archive/memory-curation/20260518-224302-mcu-memory-curation.md` | `203a2795b26ebca20d3a5d013a4bee09be3e783a4e0883e153a168a121b91a8e` | 158 | 6809 | extract-first migrated |

## 关联覆盖

- `projects/mcu/archive/2026-05-17-gd32-hc32-codex-maintenance-session.md`
- `projects/firmware-release-tools/archive/release/2026-05-18-nas-release-sync-session.md`
- `projects/mcu/archive/2026-05-24-gd32l235-app-boot-refactor-session.md`
- `artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md`

## 风险

- 本记录不声明任何当前 MCU release 可发布。
- 本记录不替代当前 linker script、bootloader design、产测规范、release tag 或 NAS 发布账本。
- 任何 current fact、active runbook 或 release action 都必须基于源项目重新验证。
