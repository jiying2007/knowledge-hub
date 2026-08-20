---
id: pcr02-unused-io-ble-kernel-policy-20260802
title: PCR02 无接口驱动裁剪与 BLE-only 内核策略
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-unused-io-ble-kernel-policy-20260802.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: schematic-and-implementation
  from: PCR02_MAIN_V2.0_20251211.pdf and pcr02_ssc305_compile
  source_sha256: dfaf9d47470314bb1ea65dd7a5805f714bd084bfc09e950a3f6c74f99e4f7f34
review_after: '2026-11-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; reviewing capture does not authorize deployment
tags:
- pcr02
- ssc305
- kernel-config
- low-power
- boot-time
- image-size
- ble
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-unused-io-ble-kernel-policy-20260802.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: schematic-plus-dual-build-hil-pending
created_at: '2026-08-02'
updated_at: '2026-08-02'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-02'
manual_validation_pending: true
summary_zh: PCR02 V2.0 无外部 USB、以太网和 SATA，production/debug 使用独立硬件约束内核；Bluetooth 仅保留 BLE+H4 且 BT_REG_ON 默认关闭，双镜像构建通过但板端回归待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 USB Ethernet SATA BLE kernel policy
related:
- projects/pcr02-ssc305/README.md
- projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_evt2_hardware_pdf_reference_index_20260711.md
- indexes/project-readiness.md
---

# PCR02 无接口驱动裁剪与 BLE-only 内核策略

## 结论

PCR02 V2.0 产品内核采用以下硬件约束：

- USB20 HOST1 D+/D- 仅到 TP9327/TP9328，无 USB 连接器和 VBUS 路径；关闭
  USB host、USB storage 和 SSTAR USB2 PHY。
- Ethernet 差分线仅到 TP5～TP8，未安装外部 PHY、磁性器件或 RJ45；关闭
  SSTAR EMAC、NETPHY、PHYLIB 和外部 PHY 驱动。
- 原理图未提供 SATA 连接器或存储器件；关闭 ATA 和 platform AHCI。
- AP6303BH 的 Bluetooth 产品能力限定为 BLE；内核仅保留 BT、BT_LE、
  HCI UART H4，关闭 BR/EDR、RFCOMM、BNEP、HIDP、HS 和无关 vendor protocol。
- BT_REG_ON(GPIO55)启动默认保持低电平，不在系统启动时给蓝牙上电脉冲；需要
  BLE 时由明确 owner 拉高并负责 HCI attach、业务生命周期和关闭回收。

## 配置隔离

PCR02 production/debug 不再共用通用 AP6303BH 内核 defconfig：

| Profile | 产品 defconfig | 内核 defconfig |
|---|---|---|
| `ap6303bh_512m_v20` | `xcrz_ipc_ap6303bh_512M_pcr02_v20_defconfig` | `iford_ssc029a_s01b_spinand_ap6303bh_pcr02_v20_defconfig` |
| `ap6303bh_512m_v20_debug` | `xcrz_ipc_ap6303bh_512M_pcr02_v20_debug_defconfig` | `iford_ssc029a_s01b_spinand_ap6303bh_pcr02_v20_debug_defconfig` |

两套配置显式启用 `CONFIG_NET=y`。这是必要约束：历史配置由 SSTAR EMAC
隐式选择 NET，若只关闭 EMAC，会同时使 cfg80211、Wi-Fi 和 Bluetooth 配置失效。

production 额外关闭 debugfs、kernel debug info、锁调试和 early printk；debug
保留对应诊断能力。旧 `ap6303bh_512m_v20_debug_customer` profile 不保留静默
别名，调用方必须迁移到 `ap6303bh_512m_v20_debug`；customer overlay 的文件系统
语义不因 profile 名称变化而改变。

## 验证与收益边界

- production/debug 内核 defconfig 展开均确认 NET、cfg80211、BT_LE、H4 保留，
  USB、ATA/AHCI、PHYLIB、NETPHY、EMAC 关闭。
- production/debug 内核和完整镜像均构建通过，load-address check 通过。
- 最终镜像与启动脚本反向扫描未发现 USB host/storage 或 EMAC 模块；Wi-Fi
  `kdrv_sdmmc`、`bcmdhd` 保留；GPIO55 启动写值为 0。
- USB-only 基线 uImage 为 6,893,056 字节，新 production 为 5,969,152 字节，
  合计减少 923,904 字节（约 13.4%）。该差值包含 EMAC/SATA/Classic BT 和
  production 诊断裁剪，不能拆分归因，也不等价于启动或功耗实测收益。

代码证据 SHA256：

- production kernel defconfig：`c67443a2b0c17b2982e96a96b2da57faf66f9f628a59f8f76941ebfe0a759d60`
- debug kernel defconfig：`a6cf4ee7eec5982bd243222d500e440ad4ebfb2a564c866ae26b228a835c028d`

## 风险与后续门禁

- 当前结论只通过 source/build/image gate，未自动刷机或部署。
- 板端必须验证 Wi-Fi/SDIO attach、BLE enable/advertise/disable/re-enable、
  冷启动 30 次 p95、OTA/回退、待机电流和温升。
- 原理图事实应与实际 PCB revision、BOM 和返修状态复核；测试点不能被当作
  对外产品接口，但产测若依赖这些测试点，需要单独保留产测方案。
- 若恢复 Classic Bluetooth、USB、有线网或 SATA，必须作为产品能力变更重新
  评审内核、启动脚本、功耗和镜像布局，不应直接复用通用 defconfig。

## Archive evidence

- Source: PCR02 V2.0 主板原理图、Knowledge Hub 既有硬件索引、本次内核与镜像实现。
- Captured at: 2026-08-02 Asia/Hong_Kong.
- Topic: hardware-aware kernel trimming / BLE-only / profile isolation.
- Sanitization: 未保存 raw build log、设备地址、凭证、二进制或 runtime state。
- Provenance: 原理图 SHA256、仓库相对路径、双配置展开和双完整镜像构建结果。
- Verification: defconfig assertions、双 kernel/compile、镜像反向扫描、旧 profile 负向拒绝。
- Memory candidate: no; reviewing decision only.
- Gate result: pass for archive candidate; HIL and owner review pending.
