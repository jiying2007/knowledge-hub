---
id: pcr02-bcmdhd-suspend-sd-boot-boundary-20260728
title: PCR02 BCMDHD suspend 竞态与可启动 SD 边界
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-07-28-bcmdhd-suspend-and-sd-boot-boundary.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session
  from: 2026-07-28 Codex session, local Git/source inspection, sanitized serial evidence and build artifact inspection
  source_sha256: 048287ddcad07ac7183f26992e00995cb6ed7ddf40a96c4fdcc7e82f6469f9ff
  temporary_source_retained: false
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- bcmdhd
- suspend
- sdio
- rtc
- bootable-sd
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-28-bcmdhd-suspend-and-sd-boot-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-28-bcmdhd-suspend-and-sd-boot-boundary.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 记录 BCMSDIO event wake lock、slpauto 状态提交竞态的定位修复，以及可启动调试 SD 导致 RTC 唤醒后重走 IPL/UBOOT 的测试边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 BCMDHD suspend 竞态与可启动 SD 边界

## 现象

SoC 应用已经停止网络模块并由 Sensor 关闭媒体推送后，Linux deep suspend 仍间歇失败，主要经历三类日志：

1. freeze 前退出：
   - `Last active Wakeup Source: mmc1:0001:2`
   - `/sys/power/state` 返回 `EBUSY`
2. SDIO function suspend 失败：
   - `dhdsdio_suspend blocked by slpauto timeout sleeping=0`
   - `Device mmc1:0001:2 failed to suspend: error -16`
3. suspend 成功后 RTC 唤醒看起来像 SoC 冷启动：
   - `HWrst`
   - `IPL_CUST Ld by SD`
   - `UBOOT Ld by SD`
   - `Starting kernel`

## 影响范围

- 平台：PCR02 / SigmaStar SSC305 / AP6303BH，BCMDHD over SDIO。
- 工作树：SSC305 SDK 编译仓 `robot_pcr02`，基线 `1b4207ea4...`。
- 场景：SLEEP/DEEP_SLEEP，TCP keepalive 已配置，Task/IOT 与 Sensor 为独立进程。
- 本记录不覆盖普通业务网络断连、服务器 TCPKA 语义或量产长稳结果。

## 环境与边界

- Task 的网络模块状态只能说明 MQTT/Agora 等模块已退出，不能证明最后一个媒体 producer 或 DHD event worker 已静止。
- Sensor 在收到低功耗请求后才开启本地 media flow gate，并在失败/恢复路径通过 guard 恢复；该 gate 是 SoC 应用侧最后一道本地数据门禁。
- raw 串口日志和可升级二进制仅作为临时证据，不进入 Hub 正文。
- 可启动调试 SD 中含 `IPL_CUST` / `UBOOT`；普通产品数据 SD 不应包含这些启动文件。

## 时间线

1. 最初低功耗 ARM 被 app_uart tracked ACK 槽竞争拒绝，修复 transaction mutex 后进入内核 suspend 阶段。
2. 内核在 freeze 前将 `mmc1:0001:2` 报为 last active wakeup source。DHD event wake lock 在 PM prepare 附近重新登记物理 wakeup event，使 wakeup_count 检查失败。
3. 将 BCMSDIO 物理 wakeup source 的 waive 前移到 firmware suspend preparation 之后、用户态提交 `/sys/power/wakeup_count` 之前，并增加 event wake lock 独立计数和有界 drain。
4. suspend 偶发继续失败，日志显示 `sleeping=0`。检查发现 SDIO suspend 过早设置全局 `dhd_mmc_suspend` / bus suspend 状态，阻断了进入 slpauto/devsleep 所需的最后 SDIO 事务。
5. 调整为先保持 bus DATA、同步执行 `dhdsdio_bussleep(TRUE)` 并有界等待，成功后再提交 suspend 状态；失败时保持 watchdog/DPC 可运行并输出详细状态。
6. 随后设备能够进入 deep suspend，但 WiFi IRQ 会通过 MCU 物理链唤醒 SoC；MCU shadow 用于独立隔离该问题。
7. RTC 60 秒测试在可启动调试 SD 插入时多次进入 BootROM/U-Boot/Linux；移除该 SD 后，同一内核正常 resume，证明 STR 链路有效，冷启动来自 SD boot selection，而不是 RTC 必然触发硬复位。

## 证据

### 源码观察

BCMDHD 相关 dirty 仅归档以下六个文件：

- `bcmsdh_sdmmc_linux.c`
- `dhd.h`
- `dhd_linux.c`
- `dhd_linux_priv.h`
- `dhd_sdio.c`
- `wl_android.c`

关键实现不变量：

- `dhd_mmc_suspend = TRUE` 只在 client suspend callback 和最终 SDIO 事务成功后设置；
- event wake lock 使用独立计数与 waitqueue，并纳入 wakeup source 保持/释放判断；
- `SETSUSPENDMODE 1` 在 firmware suspend preparation 后 drain event lock 并 waive BCMSDIO 物理 wakeup source；
- PM notifier 在 prepare 到 post-suspend 期间保持 waive，恢复路径幂等；
- slpauto 最小等待 500 ms，先同步请求 bussleep，成功后才提交 bus suspend；
- restore 时若普通或 event wake lock 仍有逻辑用户，再重新登记物理 wakeup source。

同一工作树还存在 spinand、generated header、库文件等 dirty，未验证其与本次 DHD 修改相关，不能随本记录归因。

### 构建与制品

regular release 构建命令：

```text
rtk ./build.sh release --profile ap6303bh_512m_v20_debug_customer --release-flow regular --allow-dirty --no-sync-sources --no-copy-nfs
```

2026-07-28 18:48 生成：

- `SStarOta.bin.gz`，SHA256 `b3b1794e935da79c2cf3d32f246bf682c2cfc2ffd0bfec7abbaa7caf37f6687a`；
- `SigmastarUpgradeSD.bin`，SHA256 `d0ef8c11fec8655be98a5904d07b71930a4fbf02201ef0a4c43abc6f53c6c3ce`；
- `ota_pkg_v1.1.40.tar.gz`，SHA256 `3fd71f79cda8a821e0021e75b88c04cd1a8de913e277bdd9b142061ff6d54742`。

OTA packager `validate.json` 与 `inspect.json` 均为 `ok: true`，三 component checksum 一致。由于使用 `--allow-dirty --no-sync-sources`，这些 hash 绑定本地候选制品，不绑定一个干净 Git commit。

### STR 与 SD 对照

可启动调试 SD 插入时，多轮日志在 `PM: suspend entry` 后出现：

```text
HWrst
IPL_CUST Ld by SD
UBOOT Ld by SD
Starting kernel
```

移除可启动 SD 后的 RTC 唤醒对照包含：

```text
PM: suspend entry (deep)
DDR resume
OS_JP:1 0x20000400
Restarting tasks
PM: suspend exit
SOC low power returned ... source=4
```

同时明确记录 `sdcard not present`，且没有 BootROM/U-Boot/kernel 启动标志。应用侧 `source=4` 映射 RTC TIMER。

## 假设与排除

| 假设 | 验证 | 结果 |
| --- | --- | --- |
| Task 显示网络模块 off 即可保证 DHD 静止 | Sensor 侧仍观察到 TX 增量，DHD event lock 可在 PM prepare 重新登记 | 排除；必须有 Sensor 本地门禁和 DHD 自身 drain |
| MCU NACK 导致 `/sys/power/state` EBUSY | app_uart 错误码映射和内核 last wake source 证据 | 排除；ACK 竞争与 DHD EBUSY 是不同层故障 |
| 所有 RTC 唤醒都要求 SoC 冷启动 | 同一镜像在无可启动 SD 时正常 resume | 排除 |
| WiFi wakeind 非零就是本次 RTC 冷启动根因 | shadow 隔离后仍可通过 RTC resume；SD 对照改变启动路径 | 排除为 RTC 冷启动主因；WiFi IRQ 来源仍需单独分析 |

## 根因

已确认两项内核竞态：

1. BCMSDIO event wake lock 与物理 wakeup source 的生命周期跨越用户态 wakeup_count 和 PM prepare，导致有效低功耗事务在 freeze 前被判为新 wakeup event。
2. SDIO suspend 状态提交早于进入 slpauto/devsleep 所需的最后事务，导致 `sleeping=0` 与 `-EBUSY`。

已确认一项测试环境干扰：

- 可启动调试 SD 中的 `IPL_CUST` / `UBOOT` 改变早期唤醒启动选择，表现为完整冷启动。普通产品数据 SD 不含这些文件，按 owner 当前边界不作为产品缺陷。

WiFi IRQ 的具体 packet/event 根因尚未确认。

## 修复或规避

- BCMSDIO 普通 wake lock 与 event wake lock 分开计数、联合判定；
- 在用户态 wakeup_count 提交前完成 event drain 和物理 wakeup source waive；
- 保持 prepare/post-suspend 生命周期一致；
- 在完成同步 bussleep/slpauto 后再提交 SDIO/bus suspend 状态；
- Sensor 低功耗入口切断本地媒体推送，所有失败路径恢复；
- STR 测试不插入带 `IPL_CUST` / `UBOOT` 的可启动升级 SD。

## 验证状态

- BCMDHD 六文件 `git diff --check`：通过。
- regular release 和 OTA packager inspect：通过。
- 无可启动 SD 的 RTC suspend/resume：通过一次有日志证据的对照。
- 当前静态门禁 `build/check_soc_low_power_flow.py --source-root <compile SourceCode>` 仍失败一项：检查器要求旧的单一 `wakelock_counter` restore 字符串，实现已变为普通与 event wake lock 的联合条件。需更新检查器后重跑。
- 尚无 20 次短循环、1000 次长循环和 soak 证据。

## 后续动作

1. 更新 SoC 静态检查器的 DHD restore 契约，并与实际条件保持结构化而非脆弱字符串匹配。
2. 使用普通数据 SD 或无 SD 环境做分级 HIL；每次记录 boot_id、uptime、应用 PID、RTC 误差、DHD wakeind 和 suspend 返回值。
3. 对 WiFi shadow 捕获的 IRQ 关联 firmware event/TCPKA timeout，确认是期望 keepalive 唤醒还是异常包。
4. 提交前拆分 BCMDHD 与 spinand/生成文件等无关 dirty；任何 app 或内核后续改动都重生 image/OTA。

## 状态

本记录为 reviewing debug candidate。它证明当前定位、源码策略、一次 STR 对照和候选制品完整性，不代表正式发布、长稳通过或 owner 已接受内核设计。
