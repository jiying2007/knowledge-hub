---
title: Diag 测试使用指南
doc_type: runbook
knowledge_type: guideline
maturity: active
status: active
owner: team-core
created: 2026-05-26
last_updated: 2026-06-09
tags: [diag, prog-cli, prog-tool, tester-runbook]
related:
  - ../standards/diag-command-metadata-standard.md
  - ../architecture/diag-command-architecture-final.md
validation_refs: []
---

# Diag 测试使用指南

## 1. 定位

本文面向设备侧测试人员，说明如何通过 `prog_cli` 和 `prog_tool` 执行常用 `diag` 命令、判断返回结果、
记录问题现象，并规避电机、OTA、温度阈值等有副作用操作的风险。

使用原则：

- 文档示例是常用模板，不替代当前固件的运行时 help。
- 业务命令是否存在、需要哪些参数、返回字段如何解释，以当前设备 `catalog/help` 输出为准。
- 所有会改变设备状态的命令必须逐条执行并保存返回 JSON，失败后不要连续重试高风险动作。
- 问题反馈至少包含命令、参数、执行模式、完整返回 JSON、设备版本、现场现象和复现步骤。

## 2. 入口选择

### 2.1 通过 `prog_cli` 调用运行中设备

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

### 2.2 通过 `prog_tool` 直接执行

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
2. 查询命令目录。
3. 查询单命令 help。
4. 按 help 返回的 example 执行。
5. 根据返回 JSON 判断结果。

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

### 4.1 基础发现

```bash
/customer/bin/prog_tool run-cmd diag.sys.ping.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.list.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.catalog.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.sys.version.matrix.run '{}' --mode=remote
```

### 4.2 Provider 状态

```bash
/customer/bin/prog_tool run-cmd diag.provider.registry.state.list.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.provider.manager.state.list.run '{}' --mode=remote
```

### 4.3 读取设备 SN

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.api.factory.identity.sn.get.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.factory.identity.sn.get.run '{}' --mode=local
```

### 4.4 UART 与版本检查

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

### 4.5 电机 Hall 标定

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

### 4.6 电机运动与故障控制

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

### 4.7 UART 接收调试

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

### 4.8 修改充电温度保护阈值

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.app.uart.charge_temp_range.set.run"}' --mode=remote
/customer/bin/prog_tool run-cmd diag.app.uart.charge_temp_range.set.run '{"low_cutoff_c":-3,"low_recover_c":1,"high_recover_c":42,"high_cutoff_c":46}' --mode=local
```

阈值必须满足：

```text
low_cutoff_c < low_recover_c < high_recover_c < high_cutoff_c
```

### 4.9 充电、休眠与唤醒控制

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

### 4.10 主板 MCU OTA

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

### 4.11 电机 MCU OTA

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

### 4.12 硬件状态快检

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

### 4.13 APP 运行态与媒体快检

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

### 4.14 性能与存储快检

性能命令会占用 CPU、内存或读写临时文件。现场排查优先使用小轮次，避免长时间影响业务。

```bash
/customer/bin/prog_tool run-cmd diag.perf.cpu.run '{"rounds":5,"target_us":200000}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.mem.run '{"rounds":5,"block_bytes":4096}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.sd.run '{"path":"/tmp/diag_perf_sd.bin","rounds":3,"block_bytes":4096}' --mode=local
/customer/bin/prog_tool run-cmd diag.perf.flash.run '{"path":"/tmp/diag_perf_flash.bin","rounds":3,"block_bytes":4096}' --mode=local
```

`sd` / `flash` 命令会创建、读写并删除 `path` 指定的测试文件。不要把 `path` 指到业务数据文件。

### 4.15 本地 suite

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

## 5. 系统与状态命令

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

provider 状态查询必须明确对象：

- 查 registry 状态：`diag.provider.registry.state.list.run`
- 查运行中设备托管状态：`diag.provider.manager.state.list.run`

执行方式见 [4.2 Provider 状态](#42-provider-状态)。

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

- catalog 中缺少目标命令时，先保存 catalog、registry state、manager state 三份返回。
- `last_up_ret` 非 0 或 `last_error` 非空时，把 provider 名称和返回码一起反馈给开发。
- `allow_external_control=false` 时，不要执行 `diag.provider.up.run` 或 `diag.provider.down.run`。

## 6. 返回值判断

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
| command not found | catalog 是否包含命令、provider 状态是否异常 |
| `--mode=local` 执行 `diag.sys.*` / `diag.provider.*` 与 remote 结果不一致 | local 反映 `prog_tool` 本地 runtime，remote 反映运行中业务进程；现场状态以 remote 或 `prog_cli` 为准 |
| `--mode=local` 执行已知系统命令返回 `no_active_handler` | 可能是目标固件或 `prog_tool` 版本不含该命令；保存 `diag.sys.version.matrix.run`、catalog 和完整返回后反馈开发 |
| provider_owner_managed | 该 provider 不允许外部 up/down |
| bad_request | JSON 参数缺失或类型不符合 help |
| unsupported_provider | provider 名称或 profile 不支持 |
| reply_too_large | 命令返回超过当前回复缓冲 |
| local provider up failed | 本地依赖或 provider 拉起失败，保存 `provider/up_failures` 摘要并反馈 |

## 7. Suite 使用

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

## 8. Session 模式

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

## 9. 快速排障与反馈

先按现象分类，再决定继续测试、切换模式或反馈开发。

1. `diag.sys.ping.run` 不通：先查目标业务进程和 `cmd_server` 是否在线。
2. `diag.sys.catalog.run` 无目标命令：查 manager 状态和 registry 状态。
3. `diag.sys.help.run` 查不到参数或 example：保存 help 返回并反馈开发补齐命令元数据。
4. local 模式失败、remote 模式正常：优先保存 local 返回、`provider/up_failures` 摘要和本机环境信息。
5. remote 模式失败、local 模式正常：优先查目标业务进程、`cmd_server` 转发和目标设备状态。
6. 命令有副作用：先确认测试前置条件、停止/恢复步骤和现场安全，再继续执行。

本地 `run-cmd` 返回 `no_active_handler` 时，如果本次启动存在 provider up 失败，`prog_tool` 会追加
`provider/up_failures` 摘要。该摘要只用于工具侧排障，不属于 diag 命令自身 reply。

问题反馈建议包含：

- 设备版本：SOC、主板 MCU、电机 MCU。
- 执行入口：`prog_cli` / `prog_tool`，以及 `--mode=local` 或 `--mode=remote`。
- 完整命令和参数。
- 完整返回 JSON，包括 `trace_id`、`code`、`msg`、`data`。
- 现场现象、是否可复现、执行前后是否做过重启/OTA/标定/清故障。
