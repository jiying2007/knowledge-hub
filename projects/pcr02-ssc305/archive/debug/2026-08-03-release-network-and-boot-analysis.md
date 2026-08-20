---
id: pcr02-release-network-boot-analysis-20260803
title: PCR02 release 网络恢复与启动时序分析
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-08-03-release-network-and-boot-analysis.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: current-codex-session
  from: 2026-08-03 Codex session, sanitized serial timing evidence and local kernel/init script inspection
  source_sha256: 77fd31d5a87c0d4b93db18e984982f954737edd414615bdd4481137af9202588
review_after: '2026-11-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- release
- wifi
- boot-performance
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-03-release-network-and-boot-analysis.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-08-03-release-network-and-boot-analysis.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-03'
manual_validation_pending: true
summary_zh: 记录 debug OTA 到 release 后的内核网络、WiFi 镜像完整性修复，以及剩余 rootfs 与设备身份串行启动耗时。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 release 网络恢复与启动时序分析

## 摘要

PCR02 从 debug OTA 到 release 后，release 镜像曾同时出现用户态程序缺失、IPv4 地址族不可用、WiFi 模块缺失以及 ZMQ 因 `EAFNOSUPPORT` 异常退出。最终验证表明，release 内核必须保留 IPv4 网络栈和 packet socket 支持，并将对应 WiFi 模块、固件以及 customer 应用程序完整打包。

修正后的串口证据显示，WiFi 能进入 station 模式并最终达到 LINKED/NETWORK UP，`errno 97`、ZMQ 地址族异常、BCMDHD SDIO reset error 8 和 WiFi power-up 失败均不再出现。整机从 CPU 复位到应用 `Startup complete` 由约 51 秒缩短至约 25.5 秒。

本记录是 reviewing debug candidate，不代表量产长稳或启动性能优化已经完成。

## 适用范围

- 平台：PCR02 / SigmaStar SSC305 / AP6303BH。
- 内核：Linux 5.10.117。
- 场景：开发 debug 镜像经 OTA 切换到 release，以及 release 启动完整性检查。
- release 版本证据：1.2.2。
- 生产设备仅使用 release；debug 只用于开发测试。

## 原始现象

首次 release 启动包含以下关键异常：

1. `/customer/bin/prog_cmd_server` 不存在，daemon 持续重启该进程。
2. socket 创建返回 `errno 97`，`ifconfig` 报地址族不支持。
3. ZMQ 抛出 `Address family not supported by protocol` 并终止主应用。
4. rootfs 启动脚本加载 `libarc4.ko`、`bcmdhd.ko` 时报告文件不存在。
5. IPv4 sysctl 项全部报告 unknown key。
6. customer 使用只读 lower 与 data upper 的 overlay；debug/release rootfs 差异使 OTA 兼容边界容易被误判。

## 根因与修复结论

### 内核网络配置

- `CONFIG_INET` 未启用是 AF_INET socket 返回 `EAFNOSUPPORT`、IPv4 sysctl 不存在和 ZMQ 异常退出的直接原因。
- 最终兼容配置还需保留 `CONFIG_PACKET=y`。在网络配置调整过程中缺少该选项时，BCMDHD 首次打开后会被关闭，后续 SDIO software reset 返回 error 8，WiFi 芯片无法再次上电；恢复该选项后最新日志未再复现。
- 因此不能只检查 `CONFIG_INET`，release 网络基线至少应同时覆盖 IPv4、packet socket 和实际使用的 BCMDHD 依赖。

### 镜像内容

- customer 镜像需要包含应用输出目录中的运行程序和资源，至少包括 `prog_daemon`、`prog_cmd_server`、`prog_pcr02` 及其运行依赖。
- `libarc4.ko`、`bcmdhd.ko`、WiFi firmware/NVRAM/CLM/config 必须与当前内核和 AP6303BH profile 配套进入镜像。
- 只升级 customer 而不升级 rootfs/kernel，无法修复内核网络栈缺失；是否必须升级 rootfs 取决于本次 OTA 变更是否涉及 kernel/rootfs，不取决于 debug/release 名称本身。

### debug/release rootfs 决策

- 当前生产设备只有 release，debug 仅用于开发测试，因此暂不建议为已生产 release 强制引入统一 rootfs 迁移。
- 推荐逐步减少 debug/release 的基础系统差异，把调试能力放在启动参数、配置文件或可选工具层；不把 debug 与 release 双向升级作为量产硬性验收项。
- 已决定先归档该兼容边界，不增加硬性构建校验。

## 验证证据

### 修复前日志

修复前串口日志显示：

- `prog_cmd_server` exec 失败；
- IPv4 socket 返回 `errno 97`；
- IPv4 sysctl unknown key；
- `libarc4.ko`、`bcmdhd.ko` 缺失；
- ZMQ 因地址族不支持终止；
- CPU 复位到应用启动完成约 51 秒，其中设备身份等待达到 30 秒超时。

### 修复后日志

2026-08-03 15:39 的修复后串口日志显示：

- CPU 复位：15:39:50；
- kernel 启动：15:39:52；
- `/linuxrc`：15:39:54；
- customer ubiblock 创建：15:40:00；
- launcher 启动：15:40:02；
- 应用 main：15:40:03；
- WiFi API station mode：15:40:07；
- Task 初始化完成：15:40:09；
- 设备身份返回：15:40:14.933；
- 应用 `Startup complete`：15:40:15.513。

总启动时间约 25.5 秒，比前一份日志缩短约 25 秒。设备身份能够返回后，原先 30 秒等待已消失。由于测试间还存在其他状态变化，该 25 秒改善不能全部严格归因于单一修改。

WiFi 最终达到 LINKED 和 NETWORK UP；以下旧异常均未出现：

- `errno 97`；
- ZMQ `Address family not supported`；
- SDIO reset error 8；
- WiFi power-up failed。

MQTT 未连接不构成 WiFi 驱动失败证据；日志中的设备尚未满足业务绑定/自动连接条件。

## 剩余启动耗时

### rootfs 初始化

从 `/linuxrc` 到 launcher 约 8 秒。OTA UBIFS recovery 完成到 customer `ubiblock0_3` 创建之间约有 4 秒空档，相关脚本段包含：

- `ubiblock -c`；
- 两次全量 `mdev -s`；
- 最多一次 `sleep 1`；
- customer squashfs mount。

当前证据只能把耗时限定在该区间，尚不能判定具体是哪条命令。修改前应给 UBIFS、ubiblock、mdev 和 mount 增加单调时钟标记。确认后再评估减少重复 `mdev -s`、延后非关键卷挂载或修复正常关机卸载。

### 设备身份请求被串行初始化延迟

Task 发起设备身份请求到实际发送相隔约 5.5 秒。实际发送紧跟在 `startSensors()` 完成之后，期间 IMU 与 ToF 初始化分别约 2.6 秒和 2.8 秒，并伴随 MCU 命令超时。

强证据支持身份请求与传感器控制共用串行队列或锁，但仍需在请求入队、锁等待和实际发送位置加时间戳确认。可选优化方向：

- 在 `startSensors()` 前读取并缓存 factory identity；
- 将身份读取放入独立非阻塞通道；
- IoT 使用已验证的本地身份缓存启动。

若两个阶段均按预期优化，CPU 复位到应用启动完成有机会降到约 16～20 秒；该数字是估计值，不是已验证指标。

## 其他异常与优先级

1. MCU `0x17`、`0x19` 对左右电机均出现 1 秒超时，并周期性重试。需核对电机 MCU 固件是否支持版本和霍尔标定状态查询；该问题同时影响首次启动和运行期 UART 占用。
2. 系统时间从 1970 切换到有效时间附近出现三次 `sh: write error: Broken pipe`。尚未定位具体 NTP/date 管道，不是已确认的主启动瓶颈。
3. ISP AF 参数的硬件最小/最大位置为零，相关 ioctl 返回 operation not permitted。需按硬件能力核对或禁用 AF 调用。
4. factory 中缺少 ToF、IMU、IMU bias 等标定文件，程序使用 fallback。它不明显阻塞启动，但可能影响功能精度。
5. 网络模块状态在未变化时每秒打印一次，建议改为边沿打印或低频节流。
6. `regulatory.db` 缺失目前不是 WiFi 启动阻塞项；BCMDHD firmware 已加载 CN CLM。

## 验证边界

- 本记录基于两份经脱敏摘要的串口证据和本地启动脚本检查，不保存原始串口日志。
- 未完成冷启动多轮统计、断电启动、OTA 回滚、WiFi 重连 soak 或量产长稳。
- 未确认 rootfs 4 秒空档的具体命令级根因。
- 未确认身份请求延迟的具体锁或队列实现。
- 本记录不授权把上述结论提升为 AGENTS 规则或硬性 CI 门禁。

## 后续验证

1. 在 rcS 的 UBIFS、ubiblock、mdev、mount 前后增加单调时钟标记，单变量重启验证。
2. 在 `startSensors()`、身份请求入队、锁获取和实际发送处增加时间戳。
3. 核对 MCU `0x17/0x19` 协议支持矩阵，停止对不支持目标的周期性查询。
4. 优化后至少采集 10 次冷启动，分别统计 kernel、rootfs、应用与网络 ready 的 P50/P95。
5. 独立执行 debug 到 release、release 到 release 和回滚场景，避免把开发 debug 互升要求扩展为量产硬门禁。

## 来源与状态

- Source：2026-08-03 当前 Codex 排障会话、本地内核配置和启动脚本检查、两份串口日志摘要。
- Captured at：2026-08-03，Asia/Hong_Kong。
- Sanitization：已移除设备 SN、MAC、私有服务地址、绝对个人构建路径、原始日志正文和二进制信息。
- Memory candidate：no。
- Gate result：reviewing；需命令级时序和多轮冷启动验证。
