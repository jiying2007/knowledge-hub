---
doc_type: runbook
knowledge_type: guideline
maturity: active
created: 2026-05-26
last_updated: 2026-08-07
related:
- ../../decisions/diag-command-architecture-final.md
- ../../../pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
id: pcr02-diag-usage-guide
title: Diag 测试使用指南
kind: project-current
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/diag-usage-guide.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: runbooks/diag-usage-guide.md
  source_sha256: f08a4cc8899fc0fa8b3a04f62b81ffb13d4687310a68bdf7cd62dbbcccc4a867
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- current
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/diag-usage-guide.md
- projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
- rtk python3 -m unittest codex_assets.tests.test_diag_curl_large_download_contracts -v
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
evidence_refs:
- projects/pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-08-07'
summary_zh: 本文基于 2026-08-07 当前源码刷新 diag v4 的 CLI、router、command node、provider、suite、异步大文件直链下载、自动删除压测与故障定位方法，并保留电机、OTA、媒体等高风险命令的操作边界。该条目生命周期仍为 archived retired-source provenance，内容刷新不代表 active promotion、发布完成或 owner 签收。
---

# Diag 测试使用指南

## 1. 定位

本文面向设备侧测试人员，说明如何通过 `prog_cli` 和 `prog_tool` 执行常用 `diag` 命令、判断返回结果、
记录问题现象，并规避电机、OTA、温度阈值等有副作用操作的风险。

本文在 2026-08-07 按当前源码重新核对，覆盖：

- `cli/cli.c` 的 canonical 命令入口；
- `cmd_server/cmd_router.c` 的本地观测与路由错误语义；
- `modules/app/src/app_diag/ipc/app_diag_cmd_node.c` 的 profile、provider 托管和发现命令；
- `modules/app/src/app_diag/provider/` 的命令元数据；
- `app_tool/app_tool.c` 的 local/remote、suite 与 session；
- `modules/sensor` 的 `MainAppDiag` 编译开关和 `app_product_test` 的 `ProductTestDiag` 初始化；
- `API_CURL` 的同步/异步下载、续传、校验、删除前置和线程退出边界。

生命周期说明：Knowledge Hub 条目仍保持 `archived`，本次只刷新可操作内容和验证引用，不自动产生
active promotion、发布结论或 owner 决策。设备实际能力始终以本机固件运行时发现结果为准。

使用原则：

- 文档示例是常用模板，不替代当前固件的运行时 help。
- 业务命令是否存在、需要哪些参数、返回字段如何解释，以当前设备 `catalog/help` 输出为准。
- 所有会改变设备状态的命令必须逐条执行并保存返回 JSON，失败后不要连续重试高风险动作。
- 问题反馈至少包含命令、参数、执行模式、完整返回 JSON、设备版本、现场现象和复现步骤。

## 2. 入口选择

### 2.1 运行链路与节点

远端调用链路如下：

```text
prog_cli / prog_tool --mode=remote
              |
              v
cmd_server gateway + registry + router
      |                         |
      | cmd.router.*            | diag.*
      | 本地直接处理             v
      |                MainAppDiag / ProductTestDiag
      |                         |
      +-------------------------+--> app_diag registry/dispatcher --> provider
```

- `cmd_server` 只负责 gateway、注册和路由，不执行业务诊断。
- `cmd.router.*` 由 `cmd_server` 本地处理，即使没有任何 diag command node，也能用于确认节点和 owner。
- `diag.*` 必须命中活跃 command owner，之后才进入该进程内的 registry/dispatcher/provider。
- `MainAppDiag` 使用 MAIN_APP profile，路由优先级 100；`ProductTestDiag` 使用 PRODUCT_TEST profile，优先级 50。
- 当前源码中 `modules/sensor/lib.mk` 的 `SENSOR_DIAG_CMD_NODE_ENABLE` 默认值为 `0`；只有编译为 `1`
  且初始化成功，主应用才会启动 `MainAppDiag`。`prog_product_test` 会显式启动 `ProductTestDiag`。
- 两个 profile 的 provider 集合不同；不要把 ProductTestDiag 的 catalog 直接当作主应用 catalog。

### 2.2 通过 `prog_cli` 调用运行中设备

适用于设备业务进程和 `cmd_server` 已运行的场景。

```bash
/customer/bin/prog_cli diag list
/customer/bin/prog_cli diag catalog
/customer/bin/prog_cli diag help
/customer/bin/prog_cli diag help <diag.command>
/customer/bin/prog_cli diag run <diag.command> '<json>'
```

常用状态入口：

```bash
/customer/bin/prog_cli diag provider registry state list
/customer/bin/prog_cli diag provider manager state list
```

无活跃节点或目标命令返回 `no_active_handler` 时，先使用 router 本地命令，不要先依赖
`diag.provider.*`，因为后者本身也需要活跃 diag owner：

```bash
/customer/bin/prog_cli diag run cmd.router.node.list '{}'
/customer/bin/prog_cli diag run cmd.router.module.list '{}'
/customer/bin/prog_cli diag run cmd.router.owner.list '{}'
/customer/bin/prog_cli diag run cmd.router.conflict.list '{}'
/customer/bin/prog_cli diag run cmd.router.route.stats '{}'
```

router 远端动态入口当前只放行 `diag.*` 和 `cmd.router.*`。`maint.*` 不应通过 `prog_cli` 或
`prog_tool --mode=remote` 转发，应使用 `prog_tool --mode=local`，并遵守维护命令的安全前置条件。

### 2.3 通过 `prog_tool` 直接执行

`prog_tool` 支持本地进程内执行和远端转发执行。

```bash
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=local
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=remote
```

模式差异：

| mode | 执行位置 | 依赖 | 典型用途 |
|---|---|---|---|
| `local` | `prog_tool` 进程内启动本地诊断运行时 | 自动拉起本地诊断能力和必要依赖 | 本地单元/组件诊断、strict suite |
| `remote` | 通过 `cmd_server` 转发到目标业务进程 | 目标进程和 `cmd_server` 已在线 | 现场设备诊断、业务运行态检查 |

当前发布实现中，`prog_tool run-cmd --mode=local` 使用本地独立诊断运行时。local 模式下的 `diag.sys.*`
和 `diag.provider.*` 只反映 `prog_tool` 当前进程内的诊断运行时状态，不等同于运行中业务进程状态。
现场发现、catalog、help 和 provider manager 状态查询优先使用 `prog_cli` 或 `prog_tool --mode=remote`；
local 模式用于直接执行已知业务命令，或排查 `prog_tool` 本地 provider 注册和拉起情况。

本地模式若 provider up 失败，会直接返回失败，不再继续伪装成 command-not-found。
失败时 `prog_tool` 会输出本地 provider up 摘要，列出失败 provider 和返回码。

## 3. 标准发现流程

不要凭文档猜参数。标准流程固定为：

1. 确认诊断链路可用。
2. 用 `cmd.router.node.list` / `owner.list` 确认目标节点与 owner。
3. 查询命令目录。
4. 查询单命令 help。
5. 按 help 返回的 example 执行。
6. 根据返回 JSON 判断结果。

示例：

```bash
/customer/bin/prog_cli diag list
/customer/bin/prog_cli diag catalog
/customer/bin/prog_cli diag help <diag.command>
/customer/bin/prog_cli diag run <diag.command> '<json>'
```

使用 `prog_tool` 时：

```bash
/customer/bin/prog_tool run-cmd diag.sys.catalog.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.version.matrix.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=local
```

如果只做运行中设备诊断，也可以三条都使用 `--mode=remote`。如果只做本地 provider 命令验证，先从
remote help 或文档确认参数，再用 `--mode=local` 直接执行业务命令。

读取设备 SN 的只读命令：

```bash
/customer/bin/prog_cli diag help diag.api.factory.identity.sn.get.run
/customer/bin/prog_cli diag run diag.api.factory.identity.sn.get.run '{}'
```

## 4. 测试人员常用指令

本节命令面向设备侧测试人员，默认使用发布路径 `/customer/bin/prog_tool`，并使用 `--mode=local`
在工具进程内拉起本地诊断运行时和相关诊断能力。执行具体业务命令前，仍建议先通过 `prog_cli` 或
`prog_tool --mode=remote` 执行 help，查看当前固件实际参数说明。

### 4.1 当前命令面概览

对当前源码中的 `DIAG_CommandMeta_t` 声明扫描得到 146 条命令元数据。该数字用于代码覆盖审计，
不等于任一设备、profile 或制品必然可执行 146 条；运行时 `diag.sys.version.matrix.run` 的
`command_count`、`diag.sys.catalog.run` 和 `cmd.router.owner.list` 才是现场事实。

| 层 | 源码元数据数 | 主要能力 |
|---|---:|---|
| APP | 55 | SYS/provider 9、UART 20、UART maintenance 16、AI 4、PERF 4、ZMQ 1、archive maintenance 1 |
| API | 63 | DVR 25、media 11、curl 4、WiFi 3，以及 factory/event/msg/tick/ws 和 strict smoke |
| HDI | 28 | OS/硬件探测、AI/AO/VI、ADC、disk、IMU、IRCUT、LCD、light、TOF |

按风险选择命令：

- 只读优先：`diag.sys.*`、`cmd.router.*`、版本/状态/统计/get/probe/list。
- 有运行态副作用：媒体 start/stop、WiFi connect/disconnect、音视频参数 set、UART recv debug。
- 有数据或设备风险：factory SN set、DVR format/delete、archive extract、性能写盘、电机动作与 OTA。
- `maint.*` 仅在 local 模式执行；OTA、格式化、删除、重启类命令执行前必须确认恢复步骤。

### 4.2 基础发现

```bash
/customer/bin/prog_tool run-cmd diag.sys.ping.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.list.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.catalog.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.version.matrix.run '{}' --mode=remote
```

### 4.3 Provider 状态

```bash
/customer/bin/prog_tool run-cmd diag.provider.registry.state.list.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.provider.manager.state.list.run '{}' --mode=remote
```

### 4.4 读取设备 SN

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.api.factory.identity.sn.get.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.factory.identity.sn.get.run '{}' --mode=local
```

### 4.5 UART 与版本检查

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.versions.check.run '{"soc":"1.0.0","mcu":"1.0.0","motor":"1.0.0"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"right"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.boot_version.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.boot_version.run '{"target":"right"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.ota_meminfo.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.ota_meminfo.run '{"target":"right"}' --mode=local
```

如果这些命令失败，先处理 UART/MCU 链路，不要继续做电机 OTA 或温度阈值写入。
`versions.check` 的 `soc`、`mcu`、`motor` 必须替换为当前发布基线版本；电机版本支持 `major.minor.patch`
形式，命令返回 `mismatch` 时按返回 JSON 中的 `match` 字段区分是哪一路不一致。

### 4.6 电机 Hall 标定

Hall 标定会让电机进入标定动作，执行前必须固定设备、清空运动区域，并确认电机和线束连接正常。建议先查
help，执行标定后再查状态；如需确认历史标定结果，可在执行标定前单独查询 status。

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.app.uart.motor.hall_calibration.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.app.uart.motor.hall_calibration.run '{"target":"both","timeout_ms":35000}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.hall_calibration_status.run '{"target":"both"}' --mode=local
```

单边复测时把 `target` 改为 `left` 或 `right`：

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.motor.hall_calibration.run '{"target":"left","timeout_ms":35000}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.hall_calibration_status.run '{"target":"left"}' --mode=local
```

结果判断重点：

- `hall_calibration.run` 返回 `code=0` 且 `data.success=1`：标定流程成功。
- `hall_calibration.run` 返回 `data.timed_out=1`：标定等待超时，优先检查电机供电、Hall 线束和电机 MCU 状态。
- 任一返回中的 `data.fail_mask` 非 0：至少一路电机标定失败，按 `target` 拆成左右单边复测。
- `hall_calibration_status.run` 返回 `entry*_lut_read_ok=1` 且 `entry*_lut` 非空，才说明 LUT 读取成功。

### 4.7 电机运动与故障控制

这些命令会改变电机状态。执行速度命令前，先确认设备固定、周边安全；停止电机优先把转速设为 0，
紧急情况再使用 `estop`。

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.app.uart.motor.speed.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.app.uart.motor.speed.run '{"target":"both","rpm":3000}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.speed.run '{"target":"both","rpm":0}' --mode=local
```

左右电机不同转速：

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.motor.speed.run '{"target":"both","left_rpm":3000,"right_rpm":-3000}' --mode=local
```

清故障与急停：

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.motor.clear_fault.run '{"target":"both"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.estop.run '{"target":"both"}' --mode=local
```

参数规则：

- `target` 支持 `left`、`right`、`both`，默认 `both`。
- `rpm`、`left_rpm`、`right_rpm` 取值范围为 `-6000` 到 `6000`；超出范围会被代码钳位到边界值。
- 需要对比左右电机扭矩或低速表现时，建议分别记录同一 `rpm` 下的实际现象、故障码和 Hall 标定状态。

### 4.8 UART 接收调试

用于排查 MCU 主动上报、里程、电源、充电、红外等 UART 接收链路。调试结束后应关闭，避免长期占用回调。

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.recv_debug.list.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.recv_debug.status.run '{"type":"all"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.recv_debug.set.run '{"mode":"on","type":"all"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.recv_debug.status.run '{"type":"all"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.recv_debug.set.run '{"mode":"off","type":"all"}' --mode=local
```

`type` 可先从 `recv_debug.list` 返回中选择，例如 `heartbeat_notify`、`odometer_report`、
`power_status_report`、`charge_status_report`、`infrared_report`、`infrared_distance_report`。

### 4.9 修改充电温度保护阈值

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.app.uart.charge_temp_range.set.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.app.uart.charge_temp_range.set.run '{"low_cutoff_c":-3,"low_recover_c":1,"high_recover_c":42,"high_cutoff_c":46}' --mode=local
```

阈值必须满足：

```text
low_cutoff_c < low_recover_c < high_recover_c < high_cutoff_c
```

### 4.10 充电、休眠与唤醒控制

这些命令会改变主板 MCU 状态，现场脚本中建议逐条执行并保留返回 JSON。

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.charge_enable_control.run '{"enable":1}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.charge_enable_control.run '{"enable":0}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.sleep_control.run '{"mode":1}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.wakeup_request.run '{"source":0}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.heartbeat_notify.run '{"packet_id":1}' --mode=local
```

参数含义：

- `charge_enable_control.enable`：`1` 开启充电，`0` 关闭充电。
- `sleep_control.mode`：`0` sleep，`1` standby，`2` keepalive。
- `wakeup_request.source` 和 `heartbeat_notify.packet_id` 范围都是 `0` 到 `255`。

### 4.11 主板 MCU OTA

主板 MCU OTA 使用 `maint.app.uart.ota.*` 命令，不带 `target` 参数。执行前确认固件文件已经在设备本地，
例如 `/tmp/mcu.bin`。

先确认维护命令参数：

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"maint.app.uart.ota.upgrade.run"}' --mode=remote
```

执行升级：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.upgrade.run '{"file":"/tmp/mcu.bin","retry":3}' --mode=local
```

排查串口或 flash 写入异常时，先保留失败现场，失败后立即查询 OTA 状态：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.upgrade.run '{"file":"/tmp/mcu.bin","chunk":128,"retry":5,"clear_on_failure":0}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.ota.status.run '{}' --mode=local
```

如果日志出现 `mcu ota progress rollback`，表示 MCU OTA 运行态进度回退，工具会自动用当前 chunk 起点执行 `set offset` 后续传；若多次 `mcu ota rollback recover` 后仍失败，保留 `clear_on_failure:0` 后的 `ota.status` 输出继续排查 MCU 复位、看门狗或 flash 写入错误。

MCU OTA 写入路径默认在 chunk 间插入短延时；现场不稳定时优先使用 `chunk=64` 或 `chunk=128` 复测，不建议继续增大 chunk。

升级成功后重启主板 MCU，并查询版本确认：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.reboot.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
```

失败排查时可查询 OTA 状态；如果确认需要清除 OTA 标记，再执行 `clear_flag`：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.status.run '{}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.ota.clear_flag.run '{}' --mode=local
```

### 4.12 电机 MCU OTA

先确认维护命令参数：

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"maint.app.uart.motor_ota.upgrade.run"}' --mode=remote
```

升级左电机：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"left","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"left"}' --mode=local
```

升级右电机：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"right","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"right"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"right"}' --mode=local
```

左右电机使用同一固件时可使用 `target=both`，但现场排障优先建议左右分开升级：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"both","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"both"}' --mode=local
```

### 4.13 硬件状态快检

这些命令适合产测或现场快速确认基础硬件资源是否可见。返回 `code=0` 只代表命令执行成功，仍要看
`data` 中的设备状态字段。

```bash
/customer/bin/prog_tool run-cmd diag.hdi.os.stats.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.debug.logger.status.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.hw.probe.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.disk.status.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.adc.light.read.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.imu.state.get.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.tof.state.get.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.ircut.hw.probe.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.lcd.hw.probe.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.hdi.light.hw.probe.run '{}' --mode=local
```

### 4.14 APP 运行态与媒体快检

这些命令用于确认业务服务、ZMQ 计数、音频播放和 WiFi 状态。涉及播放、网络或业务进程运行态时，
优先使用 `--mode=remote`，避免本地独立 runtime 的状态和真实业务进程状态混淆。

```bash
/customer/bin/prog_tool run-cmd diag.app.zmq.stats.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.wifi.status.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.media.player.start.run '{"file":"/customer/res/test.wav","loop_times":1}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.media.player.volume.set.run '{"volume":70}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.media.player.stop.run '{}' --mode=remote
```

如果只验证 `prog_tool` 本地播放器链路，可使用 local 并加 `--hold-ms` 保活：

```bash
/customer/bin/prog_tool run-cmd diag.api.media.player.start.run '{"file":"/customer/res/test.wav","loop_times":1}' --mode=local --hold-ms=5000
```

### 4.15 性能与存储快检

性能命令会占用 CPU、内存或读写临时文件。现场排查优先使用小轮次，避免长时间影响业务。

```bash
/customer/bin/prog_tool run-cmd diag.perf.cpu.run '{"rounds":5,"target_us":200000}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.mem.run '{"rounds":5,"block_bytes":4096}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.sd.run '{"path":"/tmp/diag_perf_sd.bin","rounds":3,"block_bytes":4096}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.flash.run '{"path":"/tmp/diag_perf_flash.bin","rounds":3,"block_bytes":4096}' --mode=local
```

`sd` / `flash` 命令会创建、读写并删除 `path` 指定的测试文件。不要把 `path` 指到业务数据文件。

### 4.16 本地 suite

```bash
/customer/bin/prog_tool list
/customer/bin/prog_tool run strict --mode=local
/customer/bin/prog_tool run hdi.strict --mode=local
/customer/bin/prog_tool run api.strict --mode=local
/customer/bin/prog_tool run app.strict --mode=local
```

`env` suite 依赖硬件、网络、存储和业务状态，现场执行时建议带 `--continue`：

```bash
/customer/bin/prog_tool run env --mode=local --continue
```

## 5. 大文件直链下载与压测

### 5.1 命令选择

`API_CURL` 提供四个命令：

| 命令 | 模型 | 用途 |
|---|---|---|
| `diag.api.curl.download.run` | 同步 | 兼容、小文件或调用方明确允许请求阻塞 |
| `diag.api.curl.download.start.run` | 异步 | 大文件下载；立即返回 `job_id` |
| `diag.api.curl.download.status.get.run` | 查询 | 查询进度和终态 |
| `diag.api.curl.download.cancel.run` | 控制 | 请求取消活跃任务 |

大文件默认使用异步三命令。provider 当前只维护一个异步 job；前一个 job 未结束或线程尚未成功回收时，
新 `start` 返回 `download_busy` 或 `thread_reap_failed`。HTTP/HTTPS 默认允许重定向，因此 GitHub HTTP
地址跳转到 HTTPS 可正常跟随，但正式使用仍建议直接给 HTTPS 地址。

默认参数：

| 参数 | 默认/约束 | 说明 |
|---|---|---|
| `connection_timeout` | 30 秒，1～3600 | 建连超时，不是整个文件下载总超时 |
| `retries` | 0，最大 10 | curl 失败重试次数 |
| `retry_sleep` | 1 秒，最大 300 | 重试间隔 |
| `strict_ssl` | 1 | 正式环境必须保持严格校验 |
| `ca_file` | `/customer/bin/resource/ssl/cacert.pem` | HTTPS CA bundle，可显式覆盖 |
| `debug` | 0 | 开启后日志增多；带签名 URL 可能含敏感 query，压测保持 0 |
| `resume` | 0 | 异步断点续传开关 |
| `expected_size` | 0 | 非零时启用空间预检和完成尺寸校验 |
| `sha256` | 空 | 64 位十六进制；非空时完成后校验 |
| `delete_before_download` | 0 | 压测删除开关，仅允许 `/data` 目标 |

### 5.2 标准异步下载

推荐同时提供真实 `expected_size` 和 SHA-256。这样能在联网前检查剩余空间，并在发布最终文件前校验
大小与内容：

```bash
/customer/bin/prog_cli diag run diag.api.curl.download.start.run \
'{"url":"https://server/path/file.bin","dest":"/data/file.bin","ca_file":"/customer/bin/resource/ssl/cacert.pem","expected_size":123456789,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","connection_timeout":30,"retries":2,"retry_sleep":1,"strict_ssl":1,"debug":0}'
```

`start` 返回：

```json
{"code":0,"msg":"accepted","data":{"job_id":"curl-1-4918153","state":"queued"}}
```

`accepted` 只表示线程创建成功并入队，不表示删除、联网、写盘、校验或 rename 成功。必须保存实际
`job_id` 并查询到终态：

```bash
/customer/bin/prog_cli diag run diag.api.curl.download.status.get.run \
'{"job_id":"curl-1-4918153"}'
```

状态流转为：

```text
queued -> running -> verifying -> succeeded
                    \-> failed
queued/running/verifying -> canceled
```

`status.get` 找到 job 时外层 `code` 可以是 0，但下载是否成功要同时检查：

- `data.state` 必须为 `succeeded`；
- `data.ret` 必须为 0；
- 有校验要求时，核对 `file_size`、`sha256` 与预期一致；
- `total=0` 或日志提示 `Channel does not report total download size` 只表示服务端未报告总大小，
  `percent` 不可信，不等于下载失败。

取消命令也只返回取消请求已接受，仍需继续查询到 `canceled`：

```bash
/customer/bin/prog_cli diag run diag.api.curl.download.cancel.run \
'{"job_id":"curl-1-4918153"}'
```

### 5.3 临时文件、续传与发布

- 异步下载写入同目录 `<dest>.part`，校验成功后通过同目录 `rename` 发布为 `<dest>`。
- `resume=0` 时，已有 `.part` 会先删除并从零下载；已有最终普通文件不会在传输阶段导致 curl error 23。
- `resume=1` 必须同时提供非零 `expected_size` 和 `sha256`，否则返回 `bad_request`。
- `.part` 已等于预期大小时先校验，成功后直接发布；校验失败会删除错误分片并从零下载。
- 服务端不兼容 Range 时，代码删除 `.part` 后自动从零重试，避免把完整响应追加到旧分片。
- 尺寸不匹配或 checksum 失败不会发布最终文件；checksum 失败会删除 `.part`。
- 取消或可恢复网络失败保留 `.part`，便于后续显式续传。
- 同步 `download.run` 也先写 `<dest>.part`，但失败时会删除 `.part`；它不提供异步进度、取消和续传契约。

续传示例：

```bash
/customer/bin/prog_cli diag run diag.api.curl.download.start.run \
'{"url":"https://server/path/file.bin","dest":"/data/file.bin","resume":1,"expected_size":123456789,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","strict_ssl":1}'
```

### 5.4 下载前删除与空间保护

压测可设置 `delete_before_download=1`，在空间检查和网络连接前删除现有 `<dest>` 与 `<dest>.part`：

```bash
/customer/bin/prog_cli diag run diag.api.curl.download.start.run \
'{"url":"https://server/path/file.bin","dest":"/data/file.bin","delete_before_download":1,"resume":0,"expected_size":123456789,"sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef","connection_timeout":30,"retries":2,"retry_sleep":1,"strict_ssl":1,"debug":0}'
```

安全边界：

- 这是不可恢复的显式删除，只能用于已确认可删的压测文件。
- 仅接受父目录 realpath 和目标 realpath 均位于 `/data` 内的普通文件或软链接；目录、`/data` 外目标、
  父目录软链接逃逸和不可解析路径会被拒绝。同步命令返回 `delete_failed`；异步命令在 status 中报告
  `state=failed` 和非零 `ret`。
- 最终文件与 `.part` 会先全部预检，再执行删除；默认值 0 不改变既有文件。
- `delete_before_download=1` 与 `resume=1` 互斥，同时设置返回 `bad_request`，且不会开始删除。
- 异步 `start` 仍可能先返回 `accepted`；实际删除失败体现在 `status.get` 的 `failed/ret`。
- 只有 `expected_size` 非零才会做下载前空间预检。未提供时仍可能写到一半触发 ENOSPC/curl error 23。

现场出现 `No space left on device` 时，先停止循环，确认哪些文件可删除。对于专用压测目标，使用上述
开关由 provider 删除同名文件；不要在脚本中对 `/data` 做通配或递归删除。

### 5.5 自动循环压测

先跑 5～10 次短循环，通过后再扩到 1000 次和 soak。每轮必须等待前一 job 进入终态，否则下一轮会
返回 `download_busy`。以下脚本不依赖 `jq`，中断时会请求取消当前 job：

```sh
#!/bin/sh

CLI=/customer/bin/prog_cli
COUNT=10
POLL_SEC=2
URL=https://server/path/file.bin
DEST=/data/diag_download_stress.bin
EXPECTED_SIZE=123456789
SHA256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
JOB_ID=

cancel_current()
{
    if [ -n "$JOB_ID" ]; then
        "$CLI" diag run diag.api.curl.download.cancel.run \
            "{\"job_id\":\"$JOB_ID\"}" >/dev/null 2>&1
    fi
}
trap cancel_current EXIT INT TERM

i=1
while [ "$i" -le "$COUNT" ]; do
    START_OUT=$("$CLI" diag run diag.api.curl.download.start.run \
        "{\"url\":\"$URL\",\"dest\":\"$DEST\",\"delete_before_download\":1,\"resume\":0,\"expected_size\":$EXPECTED_SIZE,\"sha256\":\"$SHA256\",\"connection_timeout\":30,\"retries\":2,\"retry_sleep\":1,\"strict_ssl\":1,\"debug\":0}" 2>&1)
    JOB_ID=$(printf '%s\n' "$START_OUT" | sed -n 's/.*"job_id": *"\([^"]*\)".*/\1/p' | head -n 1)
    if [ -z "$JOB_ID" ]; then
        printf 'round=%s start_failed\n%s\n' "$i" "$START_OUT"
        exit 1
    fi

    while :; do
        STATUS_OUT=$("$CLI" diag run diag.api.curl.download.status.get.run \
            "{\"job_id\":\"$JOB_ID\"}" 2>&1)
        STATE=$(printf '%s\n' "$STATUS_OUT" | sed -n 's/.*"state": *"\([^"]*\)".*/\1/p' | head -n 1)
        case "$STATE" in
            succeeded)
                printf 'round=%s job=%s succeeded\n' "$i" "$JOB_ID"
                JOB_ID=
                break
                ;;
            failed|canceled)
                printf 'round=%s job=%s state=%s\n%s\n' "$i" "$JOB_ID" "$STATE" "$STATUS_OUT"
                exit 1
                ;;
            queued|running|verifying)
                sleep "$POLL_SEC"
                ;;
            *)
                printf 'round=%s job=%s unknown_status\n%s\n' "$i" "$JOB_ID" "$STATUS_OUT"
                exit 1
                ;;
        esac
    done
    i=$((i + 1))
done
```

压测停止条件：任一 `failed/canceled`、core、致命 dmesg、进程重启、空间持续下降、句柄/线程泄漏或
command owner 漂移。每阶段记录成功轮次、首个失败的完整 status、`df -h /data`、`df -i /data`、
进程 PID/uptime 和关键 dmesg。

### 5.6 curl error 60 与 error 23

| 日志/现象 | 含义 | 首要检查 |
|---|---|---|
| curl error 60 | TLS peer/CA 校验失败 | `date`、CA bundle 存在且可读、`ca_file`、证书链/域名 |
| curl error 23 | curl 写回调未能把接收数据写入 `.part` | 空间/配额、只读挂载、目录与 `.part` 权限、闪存 I/O |
| `Failure writing output to destination` | error 23 的 curl 文本 | 同上；不是“最终同名普通文件已存在”的直接证据 |
| `Channel does not report total download size` | 服务端没有报告总长度 | 结合后续 curl/HTTP 错误判断，本身不是失败 |

error 60 不应通过 `strict_ssl=0` 作为正式修复；默认 CA 是
`/customer/bin/resource/ssl/cacert.pem`，仍需确认该资源与新版应用一起进入设备制品。

error 23 的只读取证：

```sh
df -h /data
df -i /data
mount
ls -ld /data /data/file.bin /data/file.bin.part
dmesg | tail -n 100
```

异步下载写入 `.part`，完成后才 rename。单纯存在同名最终普通文件不会导致传输阶段 error 23；最终
路径是目录或目录不允许替换时，通常是在下载完成后的发布阶段失败。若 `/data` 上 `touch` 已返回
`No space left on device`，可直接把空间/配额不足作为当前 error 23 的高置信根因。

## 6. 系统、路由与状态命令

系统命令用于确认诊断链路、命令目录和 provider 状态。测试脚本中查询类命令使用 `--mode=remote`；
`diag.provider.up.run` / `diag.provider.down.run` 会改变运行态，除非开发明确要求，一般不建议测试人员直接执行。

| 命令 | 用途 |
|---|---|
| `diag.sys.ping.run` | 验证 diag 调用路径是否可达 |
| `diag.sys.list.run` | 返回已注册命令名列表 |
| `diag.sys.catalog.run` | 返回命令目录、summary、args_schema、example |
| `diag.sys.help.run` | 返回单命令帮助 |
| `diag.sys.version.matrix.run` | 返回 diag 版本和命令数量 |
| `diag.provider.registry.state.list.run` | 返回当前已注册 provider 的状态和最近错误 |
| `diag.provider.manager.state.list.run` | 返回运行中设备托管 provider 的上线策略和最近 up/down 返回码 |
| `diag.provider.up.run` | 拉起允许外部管理的 provider，需开发确认后使用 |
| `diag.provider.down.run` | 下线允许外部管理的 provider，需开发确认后使用 |

router 本地观测命令不经过 diag owner：

| 命令 | 用途 |
|---|---|
| `cmd.router.node.list` | 查看已注册节点、profile、mode、state、priority、startup_seq 和命令数 |
| `cmd.router.module.list` | 查看节点声明的模块 |
| `cmd.router.owner.list` | 查看每条命令当前选中的 owner |
| `cmd.router.conflict.list` | 查看同命令多 owner 冲突和胜出者 |
| `cmd.router.route.stats` | 查看请求、回复、超时、拒绝及各类路由错误计数 |

目标命令完全不可达时，排障顺序固定为：`node.list` → `owner.list` → `conflict.list` →
`route.stats`。确认存在活跃 owner 后，再查询 `diag.sys.catalog.run` 和 provider 状态。

provider 状态查询必须明确对象：

- 查 registry 状态：`diag.provider.registry.state.list.run`
- 查运行中设备托管状态：`diag.provider.manager.state.list.run`

执行方式见 [4.3 Provider 状态](#43-provider-状态)。

重点字段：

| 字段 | 含义 |
|---|---|
| `provider` | provider 名称 |
| `state` / `managed_up` | provider 当前是否已上线 |
| `last_error` | 最近错误摘要 |
| `last_up_ret` | 最近一次 up 返回码 |
| `last_down_ret` | 最近一次 down 返回码 |
| `allow_external_control` | 是否允许通过 `diag.provider.up/down.run` 手动管理 |

判断规则：

- catalog 中缺少目标命令时，先保存 node/owner/conflict、catalog、registry state、manager state 返回。
- `last_up_ret` 非 0 或 `last_error` 非空时，把 provider 名称和返回码一起反馈给开发。
- `allow_external_control=false` 时，不要执行 `diag.provider.up.run` 或 `diag.provider.down.run`。

## 7. 返回值判断

标准 diag 返回 JSON：

```json
{"code":0,"msg":"ok","data":{}}
```

判断顺序：

1. 先看工具进程退出码。
2. 再看 diag 返回 JSON 的 `code`。
3. 再看 `msg` 和 `data` 中的业务字段。

常见语义：

| 现象 | 优先检查 |
|---|---|
| `no_active_handler` | router 没有收到该精确命令的活跃 owner；先查 `cmd.router.node.list/owner.list` |
| `owner_not_ready` | owner 已知但节点当前不 ready；查节点 state、heartbeat 和进程健康 |
| `route_busy` | router 待处理槽位不足；停止并发压测，等待旧请求结束 |
| `route_timeout` | owner 未在路由超时内回复；保存 route stats、进程状态和命令耗时 |
| `rate_limited` | caller/命令触发 router 限流；降低调用频率 |
| `unauthorized` | 远端 token 不在 `diag.*`/`cmd.router.*` 白名单；`maint.*` 改为 local |
| `--mode=local` 执行 `diag.sys.*` / `diag.provider.*` 与 remote 结果不一致 | local 反映 `prog_tool` 本地 runtime，remote 反映运行中业务进程；现场状态以 remote 或 `prog_cli` 为准 |
| `--mode=local` 执行已知系统命令返回 `no_active_handler` | 可能是目标固件或 `prog_tool` 版本不含该命令；保存 `diag.sys.version.matrix.run`、catalog 和完整返回后反馈开发 |
| `provider_owner_managed` | 该 provider 不允许外部 up/down |
| `bad_request` | JSON 参数缺失、类型/范围不符合 help，或参数组合互斥 |
| `unsupported_provider` | provider 名称或当前 profile 不支持 |
| `reply_too_large` | 命令返回超过当前回复缓冲 |
| `download_busy` | 已有异步下载活跃或旧线程句柄尚未回收 |
| `thread_reap_failed` | 已结束线程 join 超时/失败，句柄保留以便重试；不要继续启动新任务 |
| `delete_failed` | 同步压测删除失败；异步同类错误通过 status 的 `failed/ret` 报告 |
| curl error 60 | TLS 证书/CA 校验，见 5.6 |
| curl error 23 | `.part` 写盘失败，见 5.6 |
| local provider up failed | 本地依赖或 provider 拉起失败，保存 `provider/up_failures` 摘要并反馈 |

## 8. Suite 使用

`prog_tool` 支持批量 suite：

```bash
/customer/bin/prog_tool list
/customer/bin/prog_tool run <suite> --mode=local
/customer/bin/prog_tool run <suite> --mode=remote
```

常见 suite：

| suite | 定位 |
|---|---|
| `strict` | 全部确定性 strict 用例 |
| `env` | 全部环境依赖用例 |
| `all` | strict + env |
| `hdi.strict` / `api.strict` / `app.strict` | 分层确定性用例 |
| `hdi.env` / `api.env` / `app.env` | 分层环境依赖用例 |

执行原则：

- strict 用例必须稳定，不能依赖在线设备、外设状态或现场网络。
- env 用例允许受硬件、存储、网络、业务进程状态影响。
- 不要通过放宽 strict 期望来隐藏真实初始化错误。

## 9. Session 模式

交互或脚本化连续诊断使用 session：

```bash
/customer/bin/prog_tool session --mode=local
/customer/bin/prog_tool session --mode=remote
/customer/bin/prog_tool session --mode=remote --script=<file>
```

remote 脚本适合把 catalog、help、状态查询和业务命令串联成一次可复现诊断流程。local session 使用
本地独立诊断运行时，适合验证工具进程内 provider 和本地业务命令；local 脚本应在脚本外先通过
`prog_cli` 或 `prog_tool --mode=remote` 确认运行中设备的参数与状态，再只放入本地业务命令或本地
runtime 自检命令。

## 10. 快速排障与反馈

先按现象分类，再决定继续测试、切换模式或反馈开发。

1. 任意 `diag.*` 返回 `no_active_handler`：先查 router node/owner，确认是节点未启动、命令未宣布还是 owner 冲突。
2. router 无 `MainAppDiag`：查主应用进程和启动日志，并确认 `SENSOR_DIAG_CMD_NODE_ENABLE=1` 的新对象已进入制品。
3. router 有节点但返回 `owner_not_ready`：查节点 state、heartbeat、进程阻塞或重启。
4. `diag.sys.catalog.run` 无目标命令：查 manager state、registry state 和当前 profile。
5. `diag.sys.help.run` 查不到参数或 example：保存 help 返回并反馈开发补齐命令元数据。
6. local 模式失败、remote 模式正常：保存 local 返回、`provider/up_failures` 摘要和本机环境信息。
7. remote 模式失败、local 模式正常：查目标业务进程、`cmd_server` 转发和目标设备状态。
8. 异步下载 `accepted` 后失败：以 `status.get` 的 `state/ret/http_code/file_size` 为准，不以 start 回包判成功。
9. 命令有副作用：先确认测试前置条件、停止/恢复步骤和现场安全，再继续执行。

本地 `run-cmd` 返回 `no_active_handler` 时，如果本次启动存在 provider up 失败，`prog_tool` 会追加
`provider/up_failures` 摘要。该摘要只用于工具侧排障，不属于 diag 命令自身 reply。

问题反馈建议包含：

- 设备版本：SOC、主板 MCU、电机 MCU。
- 执行入口：`prog_cli` / `prog_tool`，以及 `--mode=local` 或 `--mode=remote`。
- 完整命令和参数。
- 完整返回 JSON，包括 `trace_id`、`code`、`msg`、`data`。
- 现场现象、是否可复现、执行前后是否做过重启/OTA/标定/清故障。

## 11. 构建、部署与验证边界

### 11.1 刷新 diag provider

对象、模块库和最终应用是不同制品阶段。只刷新 `modules/app` 对象不会自动更新 `libapp`，只重新链接
应用也可能继续使用旧库。当前 `API_CURL` 变更的最小构建顺序：

```bash
rtk make modules/app_obj_all -j20
rtk make modules/app_lib_all -j20
rtk make app_product_test_app_all -j20
rtk make pcr02_app_all -j20
```

如果同时修改过底层 `modules/api` curl 实现，应先追加：

```bash
rtk make modules/api_obj_all -j20
rtk make modules/api_lib_all -j20
```

### 11.2 启用 MainAppDiag

`SENSOR_DIAG_CMD_NODE_ENABLE` 是编译期宏，当前源码默认 0。Make 规则没有把该编译 flag 作为已有对象的
自动失效条件；从 0 改为 1 后必须先清理 sensor 对象，再在整个重建链路保持同一取值：

```bash
rtk make modules/sensor_obj_clean
rtk make modules/sensor_obj_all SENSOR_DIAG_CMD_NODE_ENABLE=1 -j20
rtk make modules/sensor_lib_all SENSOR_DIAG_CMD_NODE_ENABLE=1 -j20
rtk make pcr02_app_all SENSOR_DIAG_CMD_NODE_ENABLE=1 -j20
```

部署后至少核对：

```bash
/customer/bin/prog_cli diag run cmd.router.node.list '{}'
/customer/bin/prog_cli diag run cmd.router.owner.list '{}'
/customer/bin/prog_cli diag version
/customer/bin/prog_cli diag help diag.api.curl.download.start.run
```

看到 `MainAppDiag` 和目标 owner 后，才能说明路由注册生效；`start` 返回 `accepted` 也仍不能说明下载成功。

### 11.3 发布与 HIL 门禁

- 后编译 app 不会自动进入已生成的 image/OTA；若要在正式包生效，必须重新生成制品。
- 逐级核对 `out/arm/app`、候选包、release、设备 staged/installed、image、OTA 的 size、MD5、BuildID 和时间。
- 当前源码契约与交叉构建已有验证，但大文件成功终态、取消时延、断网续传、磁盘耗尽和 soak 仍需板端 HIL。
- HIL 按单次 smoke、5～10 次短循环、1000 次长循环、soak 逐级放大；前一级有 core、致命 dmesg、
  状态泄漏或身份漂移时停止。
- 退出 command node/provider 时，curl 线程最多等待 5 秒 join；超时会向上返回并保留 provider/线程句柄，
  不应继续释放其下层公共资源或强行启动新任务。

详细实现与构建证据见
[PCR02 diag 大文件直链下载实现与构建边界验证](../../../pcr02-ssc305/validation/2026-08-06-diag-curl-large-download.md)。
