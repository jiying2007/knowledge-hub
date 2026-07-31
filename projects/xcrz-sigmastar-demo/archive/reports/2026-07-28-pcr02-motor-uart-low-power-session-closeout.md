---
id: pcr02-motor-uart-low-power-session-closeout-20260728
title: PCR02 2026-07-28 电机时间戳与低功耗联调收口
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session
  from: 2026-07-28 Codex session, local Git/source inspection, sanitized serial evidence and build artifact inspection
  source_sha256: 511a3966ab4cd7eec451186d891e4cf5ad400004bd63081151ff7b4982644f80
  temporary_source_retained: false
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- session-closeout
- motor-timestamp
- low-power
- cross-repo
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-28-pcr02-motor-uart-low-power-session-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 导航 2026-07-28 电机时间戳、UART 事务、DHD suspend、MCU WiFi shadow 与 RTC/SD 对照的跨仓调试成果、分支证据和剩余门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 2026-07-28 电机时间戳与低功耗联调收口

## 范围

本记录是 2026-07-28 跨 SoC 应用、SDK/内核和主板 MCU 联调的会话导航，不重复保存各子问题的完整技术正文。当天工作覆盖：

- 电机 MCU 采样时间戳同步、固定长度 `0x16` 上报和 SoC 侧时间重建；
- `app_uart` / `hdi_uart` tracked transaction、BOOTTIME 时间语义和低功耗命令竞争；
- Sensor 低功耗媒体流门禁、MCU ARM/DISARM 和 RTC 唤醒闭环；
- Broadcom DHD/SDIO suspend 的 wakeup-source、event wake lock 和 slpauto 竞态；
- MCU WiFi wake shadow，用于隔离 WiFi 中断与 SoC 物理唤醒链；
- 可启动调试 SD 对 SSC305 唤醒启动路径的影响边界。

raw 串口日志、二进制制品、设备地址、云端标识和无关 dirty 变更未进入 Knowledge Hub 正文。

## 结论

1. 电机时间戳方案已经落为 MCU 采样 BOOTTIME、SoC 0x1A 时间同步、固定 40 字节 0x16 上报和算法侧 Unix 时间戳重建。速度控制保持事件驱动，不增加“固定周期未刷新即 stop”的错误语义。详细设计与验证见：
   - `projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md`
   - `projects/xcrz-sigmastar-demo/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md`
2. 低功耗 ARM/DISARM 的 `-65540` 已定位为 0x1A 时间同步与 0x04 低功耗控制争用单一 tracked ACK 槽，而非 MCU NACK。修复为统一 transaction mutex，详见：
   - `projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-app-uart-time-sync-low-power-busy.md`
3. DHD suspend 失败经历了两层独立竞态：
   - PM prepare 前后的 BCMSDIO event wake lock 重新登记，使 `mmc1:0001:2` 成为 last active wakeup source；
   - SDIO suspend 过早提交 bus suspend 状态，使最终 slpauto/devsleep 请求无法完成。
   处理和验证边界见：
   - `projects/pcr02-ssc305/archive/debug/2026-07-28-bcmdhd-suspend-and-sd-boot-boundary.md`
4. MCU WiFi shadow 已支持 SLEEP 和 DEEP_SLEEP，仅保留 EXTI 与计数日志，不输出 PA8、不恢复 PA15、不上报 FIRED。该模式默认关闭，只用于诊断，详见：
   - `projects/gd32l235/archive/debug/2026-07-28-wifi-wake-shadow-validation.md`
5. RTC 60 秒唤醒在不带可启动文件的 SD 环境中走正常 STR resume；此前看到的 BootROM/U-Boot/Linux 完整启动来自可启动调试 SD 中的 `IPL_CUST` / `UBOOT`，按项目 owner 给出的产品边界不视为正常产品问题。

## 相关分支快照

以下是归档时的只读观察，不代表干净提交或可复现 release 基线：

| 工程 | 分支与基线 | 相关 dirty 范围 |
| --- | --- | --- |
| SoC 应用根仓 | `dev/pcr02`，`ea5a306b9132568b9a4034026a5356023a10e2d2` | 公共 UART/HDI 头、bridge/proto、生成库及其他未归档变更 |
| `modules/app` | `master`，`ae6d460ea2731bc39ece40887f0837499dc0be4d` | app_uart tracked transaction、时间同步和协议处理 |
| `modules/hdi` | `master`，`2962e86acad6248335c9634b3c51b6ee3b134751` | UART TX/RX BOOTTIME 与 `hdi_os_time` |
| `modules/sensor` | `master`，`6c3b17ba05746cf514c6e53f390da46e27996629` | SensorSerial 时间重建和低功耗串口协调 |
| SSC305 SDK 编译仓 | `robot_pcr02`，`1b4207ea4...` | BCMDHD 六个源码文件；同仓 spinand、生成文件等 dirty 不归因于本次 DHD 调试 |
| GD32L235 MCU | `master`，`6fd343db...` | motor timestamp、低功耗 wake/disarm、WiFi shadow、构建与静态检查；同仓其他 dirty 需独立审查 |

## 验证证据

### 应用与协议

- 电机时间戳实现已有模块构建、静态契约与映射检查记录，见既有 validation。
- MCU `Tools/tests/check_wakeup_diagnostics.py` 在归档前通过。
- SoC `build/check_soc_low_power_flow.py` 指向当前 SDK 编译仓后仅剩一项旧字符串契约失败：检查器仍要求 `if (dhd->wakelock_counter > 0)`，而实现已扩展为普通 wake lock 与 event wake lock 的联合恢复条件。该检查器需要后续同步，当前不能作为全绿门禁。

### SDK 与发布制品

使用 regular release 流生成制品：

```text
rtk ./build.sh release --profile ap6303bh_512m_v20_debug_customer --release-flow regular --allow-dirty --no-sync-sources --no-copy-nfs
```

2026-07-28 18:48 生成并通过 packager inspect：

- SoC OTA `SStarOta.bin.gz`：71,893,178 字节，SHA256 `b3b1794e935da79c2cf3d32f246bf682c2cfc2ffd0bfec7abbaa7caf37f6687a`；
- SD 升级包 `SigmastarUpgradeSD.bin`：91,189,272 字节，SHA256 `d0ef8c11fec8655be98a5904d07b71930a4fbf02201ef0a4c43abc6f53c6c3ce`；
- 整机 OTA `ota_pkg_v1.1.40.tar.gz`：71,952,615 字节，SHA256 `3fd71f79cda8a821e0021e75b88c04cd1a8de913e277bdd9b142061ff6d54742`。

整机 OTA inspect 中 SoC、主板 MCU、电机 MCU 三个 component 的 MD5/CRC32 均与 manifest 一致。制品来自 `--allow-dirty --no-sync-sources` 工作树，只能作为本轮联调候选，不能替代 commit、source lock 或发布签收。

### 板级低功耗

- 修复 DHD 后，设备能够进入 deep suspend。
- MCU shadow 日志证明 WiFi 边沿到达时 `p8=0`、PA15 保持原状态，物理唤醒链被隔离。
- 不带可启动 SD 文件时，RTC 唤醒日志包含 `PM: suspend entry`、DDR resume、`Restarting tasks`、`PM: suspend exit`，应用返回 `source=4`；未出现 `HWrst`、`IPL_CUST Ld by SD`、`UBOOT Ld by SD` 或 `Starting kernel`。

## 未决风险与下一步

1. 将 `check_soc_low_power_flow.py` 的 DHD restore 契约更新为普通 wake lock 与 event wake lock 的联合条件，并重新跑全绿静态门禁。
2. 在普通产品 SD 或无 SD 环境下执行至少 20 次短循环、1000 次长循环和 soak；统计 suspend 成功率、RTC 误差、WiFi shadow 计数、TCPKA wake reason、boot_id 和应用 PID 连续性。
3. WiFi shadow 是诊断开关，产品 release 必须保持默认关闭；找到 WiFi IRQ 来源后再决定正式唤醒策略，不能把 shadow 当作永久产品行为。
4. 相关仓库均为 mixed dirty 工作树。提交前必须按模块拆分 diff，排除 spinand、生成库、版本号、温度阈值等未被本记录证明属于本任务的改动。
5. app 后编译不会自动进入既有 image/OTA；任何后续源码改动都必须重生 SoC/整机制品并重新核对 hash。

## 归档状态

本记录为 reviewing project archive，用于导航当日调试成果和证据边界；不代表分支已提交、release 已发布、owner 已签收或长稳验证完成。
