---
related:
- pcr02-data-ubifs-single-page-shift-readonly-20260720
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-bdma-ch0-ubifs-deadlock-20260828
title: PCR02 BDMA CH0 未释放导致 UBIFS 与 /data 阻塞排障记录
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-08-28-bdma-ch0-ubifs-deadlock.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-08-28 板端 ADB 分层取证、SysRq 任务栈与本地 SDK 源码审计；原始设备日志不归档。
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-11-26'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- bdma
- mspi
- fsp-qspi
- spinand
- ubifs
- data-partition
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-bdma-ch0-ubifs-deadlock.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-28-bdma-ch0-ubifs-deadlock.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-28'
updated_at: '2026-08-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-28'
manual_validation_pending: true
summary_zh: 现场内核栈确认 MSPI LCD 与 FSP/QSPI NAND 共享 BDMA CH0；MSPI DMA 异常退出未取消 BDMA，导致 CH0 信号量未归还，进而阻塞 NAND 回写、UBIFS 与 /data 访问。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 BDMA CH0 未释放导致 UBIFS 与 `/data` 阻塞排障记录

## 现象

设备未重启但出现部分应用仍运行、终端命令无法继续执行的状态。一个在 `/data` 工作目录中创建文件的 `touch` 进程长期处于不可中断等待；目录遍历与应用文件打开也随后阻塞。网络、ADB 和新的远程 shell 心跳仍可用，表明并非整机或网络栈完全失效。

受影响时系统负载约为 34（双核设备）。`ifconfig` 可正常返回；对 `/data` 的文件元数据访问和写入则卡住。

## 影响范围

- 平台：PCR02 / SigmaStar SSC305 / Linux 5.10.117。
- 受影响链路：MSPI LCD DMA、FSP/QSPI SPI-NAND、UBI、UBIFS `/data` 与其上层日志/运行态文件访问。
- 业务表现：`prog_pcr02` 部分线程、交互 shell、目录扫描和写入操作可永久等待；常规重启可恢复运行态，但不是根因修复。
- 风险：若在 NAND 写入中强制释放 BDMA，可能扩大数据损坏；本记录不授权在运行设备上执行该操作。

## 环境

- 现场内核：Linux 5.10.117，2026-08-26 构建。
- 分区：`ubi0:data` 挂载为 UBIFS `/data`。现场 `ro_error=0`、UBI `ro_mode=0`、volume `corrupted=0`，未进入历史 UBIFS 自我只读保护。
- 取证：分层 ADB 只读探测、`/proc` 状态、SysRq 任务栈和本地 SDK 源码审计。
- 脱敏边界：不记录设备端点、原始 dmesg、完整任务栈、二进制或现场文件。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-08-28 | 分层连通性探测 | 网络、ADB、远程 shell 和主应用进程均仍可用。 |
| 2026-08-28 | `/proc` 取证 | `touch`、shell、UBIFS 回写线程与应用线程出现 D 状态。 |
| 2026-08-28 | SysRq 任务栈 | 定位到 NAND/UBIFS 阻塞由 BDMA CH0 信号量等待扩散。 |
| 2026-08-28 | SDK 源码审计 | 确认 MSPI 与 Flash FSP/QSPI 共用 CH0，且 MSPI DMA 异常路径未取消 BDMA。 |

## 证据

### 现场调用链摘要

- UBIFS 回写 worker `flush-ubifs_0_4`：`UBIFS writeback -> UBI -> NAND page program -> FSP/QSPI BDMA write -> hal_bdma_transfer -> down`。
- LCD 相关应用线程 `sensor_disp1`：`framebuffer ioctl -> MSPI DMA write -> hal_bdma_transfer -> down`。
- 一个 `prog_pcr02` 线程：`nand_get_device -> NAND read -> UBI -> UBIFS -> readdir`。
- `touch`、应用 `task_poller` 与目录扫描 shell：在 `ubifs_tnc_locate` 或 `ubifs_tnc_next_ent` 的 `__mutex_lock` 等待。

这说明 `/data` 访问卡住是下游症状；卡住的共同前置条件是 BDMA 通道无法再次取得。

### 源码对应事实

- `drivers/sstar/mspi/iford/hal_mspi.c`：MSPI bus 0 映射到 `HAL_BDMA_CH0`，DMA 读写均以中断模式调用 `hal_bdma_transfer()`。
- `drivers/sstar/flash/os/drv_flash_os_impl.c`：Flash FSP/QSPI BDMA 传输也固定调用 `hal_bdma_transfer(HAL_BDMA_CH0, ...)`。
- `drivers/sstar/bdma/iford/hal_bdma.c`：`hal_bdma_transfer()` 先执行无超时的 `CamOsTsemDown()`；正常归还只发生在 BDMA 中断处理函数的 `CamOsTsemUp()`，或显式 `hal_bdma_cancel_transfer()`。
- `hal_mspi_dma_write()` / `hal_mspi_dma_read()`：BDMA 已成功启动后，若 `hal_mspi_transfer()` 超时或失败，仅关闭 MSPI DMA 并返回，未调用 `hal_bdma_cancel_transfer()`。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| NFS 硬挂载失联导致 shell 卡住 | 有界读取 `/mnt`、查看 NFS 服务状态 | 目录读取可完成 | 排除 |
| `/data` 已进入 UBIFS 只读保护 | 读取 UBIFS/UBI 调试状态 | `ro_error=0`、`ro_mode=0` | 排除本次为只读保护 |
| 单纯应用退出 | ADB、shell、进程和线程状态检查 | 应用仍运行，多个线程在内核 I/O 路径等待 | 排除 |
| MSPI 与 Flash 竞争/遗失 CH0 释放 | SysRq 栈与源码映射 | 两链路同卡 `hal_bdma_transfer()->down`，且同用 CH0 | 强证据 |

## 根因

已确认的持久卡死软件根因是：MSPI DMA 使用 BDMA CH0 后，若传输未产生完成中断或 MSPI 等待先超时，错误路径没有调用 BDMA 取消接口，导致 CH0 的信号量不被归还。此后 Flash FSP/QSPI 也无法取得同一 CH0，NAND 写回停滞，再导致 UBIFS `/data` 的文件查找、目录遍历和写入级联阻塞。

首次传输为何未完成（硬件中断丢失、MSPI 外设状态、BDMA 控制器或其他底层触发）未在本次偶发现场直接捕获，仍为待验证触发条件；不得将其直接归因于 NAND 介质损坏。

## 修复或规避

- 最小修复：在 MSPI DMA 读写中，仅当 `hal_bdma_transfer()` 已成功启动后，任何后续错误/超时路径都调用 `hal_bdma_cancel_transfer(dma_ch)`，然后关闭 MSPI DMA 并解锁。
- 健壮性修复：为 CH0 获取增加有界等待、超时日志、寄存器快照和取消后的状态计数；统一 `hal_bdma_transfer()` 失败分支的清理。
- 运行态规避：故障发生后不要继续触发 `/data` 写入、日志清理或大范围目录扫描；也不要在 NAND 写入未知状态下手工释放 BDMA。
- 本次未修改源码、未部署内核、未执行重启。

## 验证

- 已完成：现场 SysRq 任务栈与本地源码的调用链一致性核对。
- 尚未完成：修复前后 HIL 对照、首次 MSPI DMA 未完成的触发复现、BDMA 取消后数据完整性验证。
- 通过判据：在 LCD DMA 与 `/data` 写压力并发时，CH0 等待可在有界时间内返回或取消；无新增 D 状态 NAND/UBIFS 任务；`touch`、目录读取及应用日志写入保持可用；无 UBIFS/UBI/FSP 错误或数据校验异常。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason: 已确认持续阻塞的软件缺陷；首次 BDMA 完成中断缺失的触发条件尚未复现，修复与 HIL 数据完整性验证待补。
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: '2026-11-26'
```

## 后续动作

1. 在 MSPI DMA 异常路径补充 BDMA cancel 与统一清理，完成内核构建和最小回归。
2. 增加 CH0 超时、取消和完成中断诊断计数，完成 LCD 刷新与 `/data` 写入并发 HIL。
3. 仅在修复、数据完整性和 HIL 都通过后，新增 validation；本条不自动提升为 runbook、决策或通用规则。
4. 与 `pcr02-data-ubifs-single-page-shift-readonly-20260720` 保持关联但不合并：前者是持久化 UBIFS 页面异常，本条是 BDMA 未释放导致的运行态阻塞。
