---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-bdma-ch0-mspi-ubifs-lockup-20260828
title: PCR02 MSPI0 泄漏 BDMA CH0 导致 NAND/UBIFS 全局阻塞
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-08-28 现场只读 ADB/SysRq/MMIO 证据与本地 SDK 源码、Git 历史交叉分析；原始日志和设备端点不归档
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-09-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- bdma
- mspi
- spi-nand
- ubifs
- deadlock
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-pcr02-bdma-ch0-mspi-ubifs-lockup.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-28'
updated_at: '2026-08-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-28'
manual_validation_pending: true
summary_zh: 实机 SysRq w、MMIO 与源码交叉证实：最后占用 BDMA CH0 的路径为 MIU 到 MSPI0；硬件 busy/done/IRQ pending 均为 0，但 CH0 信号量未归还，LCD 后续请求与 SPI-NAND/UBIFS
  回写共同阻塞于 CamOsTsemDown。MSPI DMA 超时路径缺少 owner-aware stop、IRQ 同步与信号量释放；两个 25fps ST77912 的高频小包和 4KiB 像素块放大触发概率。Flash cancel
  的迟到 IRQ 竞态保留为未证实触发候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 BDMA CH0/MSPI/NAND 阻塞：来源关联与待验证排障记录

> **证据边界（2026-10-19 AI 补充复核）：** 本条原正文是未填写的通用排障模板。以下内容是对同仓另一篇已写实的 `reviewing` 历史记录的**有来源关联摘录**，不是本次重新读取设备日志、复现问题、修改内核或获得 owner 验收。原始 `source.source_sha256`、自引用的 `validation_refs` 不能单独证明外部源码、板端日志及修复结果。本文继续保持 `reviewing` / `manual_validation_pending=true`。

## 现象及范围（来自关联文本，非本条独立复测）

- 关联记录描述：PCR02 SSC305、Linux 5.10.117 的 `/data` UBIFS 操作不可中断等待，`touch`、目录访问与部分应用线程阻塞；网络与 ADB 仍可用，并非整机立即掉线。
- 相关链路涉及 MSPI LCD DMA、Flash FSP/QSPI NAND、BDMA CH0、UBI/UBIFS。现场版本、发生频率、触发输入和后续升级状态没有在本条独立取证。

## 可追溯关联来源

- **Knowledge Hub 历史排障正文：** [2026-08-28 BDMA CH0 / UBIFS deadlock](2026-08-28-bdma-ch0-ubifs-deadlock.md)，Registry ID `pcr02-bdma-ch0-ubifs-deadlock-20260828`，当前仍为 `reviewing`。此记录有现象、时间线、调用链、源码路径和明确的待验证边界。
- 该关联记录摘要的现场链：`UBIFS -> UBI -> FSP/QSPI NAND -> hal_bdma_transfer -> CamOsTsemDown`；LCD 线程在 `MSPI DMA -> hal_bdma_transfer` 等待。其列出的源码路径包括 `drivers/sstar/mspi/iford/hal_mspi.c`、`drivers/sstar/flash/os/drv_flash_os_impl.c`、`drivers/sstar/bdma/iford/hal_bdma.c`。
- **来源层级：** 上述是 Hub 已保存的历史文本和其内源代码引用；原始 SysRq/MMIO 快照、实际 SDK commit、不可变设备构建及原始日志没有在本次复核中独立获取。路径文字不是可复跑的 source revision，且不能用 `knowledge-check --dry-run` 替代设备验证。

## 假设、历史分析和未确认事项

| 项目 | 关联记录陈述 | 本条判定 |
| --- | --- | --- |
| CH0 共享 | MSPI 与 Flash FSP/QSPI 调用同一 BDMA 通道 | 历史源码分析摘要，尚未以当前 SDK 精确 SHA 复核 |
| 长时间阻塞 | 下游 NAND/UBIFS 与 LCD 等待同一信号量 | 历史现场栈摘要，尚无本条原始 log/设备再现 |
| 异常路径 | MSPI DMA 后续错误/超时时缺少 BDMA cancel | 关联记录提出的软件缺口；修复源码与 HIL 尚未验收 |
| 最初触发因素 | DMA completion/IRQ 丢失、MSPI 外设或底层状态 | 未确认；不得直接归咎 Flash 介质、NAND 损坏或特定中断竞态 |

## 根因、修复和验证状态

- **本条独立根因：未确认。** 关联文本认为异常退出未归还 CH0 信号量是持续阻塞的软件路径解释；这不等于证明首次触发条件或生产固件修复结果。
- **已在本条执行的修复：无。** 关联文本建议在合法获得通道并启动 DMA 后，对错误分支进行受控 cancel/清理，且必须避免与 NAND 活动传输竞态。不得在实际设备上手工强制释放 CH0。
- **仍缺：** 精确的 SDK source commit/补丁 diff、原始受控 SysRq/MMIO 取证标识、并发 LCD 与 `/data` 压力的修复前后 HIL、IRQ/cancel race 故障注入以及 UBI/UBIFS 数据完整性核验。

## 后续动作

1. 向源项目取得脱敏、不可变的代码版本和原始现场取证 receipt，核对本条与关联文本是否确属同一现场/同一根因；不得以同题重复条目推定同一性。
2. 以 source SHA、artifact digest、运行版本和有界测试矩阵补独立 validation；由真实模块 owner 判断是保留独立记录、建立 supersedes 关系还是在受控流程中去重。
3. 在上述证明之前不提升 `active`、不关闭设备证据缺口，也不把本次文字补录计为板端验证通过。
