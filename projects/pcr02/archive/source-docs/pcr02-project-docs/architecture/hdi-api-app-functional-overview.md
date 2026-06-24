---
title: HDI API APP 模块功能总览
doc_type: architecture
knowledge_type: model
maturity: verified
status: active
owner: team-core
created: 2026-05-13
last_updated: 2026-05-13
tags: [pcr02, module, hdi, api, app]
related: [project-core-module-design.md, project-detailed-design.md, module-catalog.md]
validation_refs: [modules/hdi, modules/api, modules/app]
---

# HDI API APP 模块功能总览

## 1. 目标

本文档补齐 `modules/hdi`、`modules/api`、`modules/app` 的功能级说明，作为终版架构的功能视图。

### 1.1 能力复用快速检索矩阵（先复用，再新增）

| 需求能力 | 当前是否支持 | 优先复用模块 | 入口头文件 | 关键实现文件 |
|---|---|---|---|---|
| JSON 解析/生成 | 支持 | `modules/api` | `modules/api/include/api_json.h` | `modules/api/src/api_utils/api_json.c` |
| INI 配置解析 | 支持 | `modules/api` | `modules/api/include/api_ini.h` | `modules/api/src/api_config/api_ini.c` |
| TOML 配置解析 | 支持 | `modules/api` | `modules/api/include/api_toml.h` | `modules/api/src/api_config/api_toml.c` |
| 字典配置与文件配置 | 支持 | `modules/api` | `modules/api/include/api_dict.h`, `api_filecfg.h` | `modules/api/src/api_config/api_dict.c`, `api_filecfg.c` |
| HTTP/CURL 请求 | 支持 | `modules/api` | `modules/api/include/api_curl.h` | `modules/api/src/api_protocol/api_curl.c` |
| WebSocket/MQTT | 支持 | `modules/api` | `modules/api/include/api_websocket.h`, `api_mqtt.h` | `modules/api/src/api_protocol/api_websocket.c`, `api_mqtt.c` |
| ZMQ IPC 通信 | 支持 | `modules/api`, `modules/app` | `modules/api/include/api_zmq.h`, `modules/app/include/app_zmq.h` | `modules/api/src/api_ipc/api_zmq.c`, `modules/app/src/app_zmq.c` |
| 串口通信/串口 OTA | 支持 | `modules/hdi`, `modules/app` | `modules/hdi/include/hdi_uart.h`, `modules/app/include/app_uart.h` | `modules/hdi/src/hdi_hw/hdi_uart.c`, `modules/app/src/app_uart/app_uart.c`, `app_uart_ota.c` |
| GPIO/I2C/PWM/WDT 控制 | 支持 | `modules/hdi` | `hdi_gpio.h`, `hdi_i2c.h`, `hdi_pwm.h`, `hdi_wdt.h` | `modules/hdi/src/hdi_hw/hdi_gpio.c`, `hdi_i2c.c`, `hdi_pwm.c`, `hdi_wdt.c` |
| 音视频采集/输出（AI/AO/VI） | 支持 | `modules/hdi` | `hdi_ai.h`, `hdi_ao.h`, `hdi_vi.h` | `modules/hdi/src/hdi_audio/hdi_ai.c`, `hdi_ao.c`, `modules/hdi/src/hdi_video/hdi_vi.c` |
| 命令注册/分发/执行框架 | 支持 | `modules/app` | `app_diag_center.h`, `app_diag_registry.h`, `app_diag_dispatcher.h` | `modules/app/src/app_diag/framework/app_diag_center.c`, `app_diag_registry.c`, `app_diag_dispatcher.c` |
| 诊断 Provider 生命周期管理 | 支持 | `modules/app` | `app_diag_cmd_node.h`, `app_diag_*_provider.h` | `modules/app/src/app_diag/ipc/app_diag_cmd_node.c`, `modules/app/src/app_diag/provider/*.c` |
| 线程/同步/内存抽象 | 支持 | `modules/hdi` | `modules/hdi/include/hdi_os.h` | `modules/hdi/src/hdi_os/hdi_os_*.c` |

### 1.2 复用优先级规则（强制）

1. 先查本节矩阵，再查第 2-4 节三级索引表。
2. 若能力在 `api` 已存在（如 JSON/INI/TOML），禁止在 `app` 或业务层重复造轮子。
3. `hdi` 负责硬件/OS 抽象；`api` 负责通用能力；`app` 负责业务编排与诊断执行。
4. 复用评估必须记录“为什么不能复用现有实现”后，才允许进入新增方案。

## 2. `modules/hdi` 功能介绍

`hdi` 负责硬件与 OS 适配，向上层提供统一调用接口。

- OS 基础能力：线程、锁、条件变量、信号量、原子、内存、时间、文件、进程执行。
- 硬件访问能力：GPIO、UART、I2C、ADC、PWM、WDT、Key、Hotplug、Disk、TOF、IMU、Light、IRCut。
- 音视频能力：AI/AO、VI 及相关帧处理。
- 平台适配能力：SigmaStar 平台（`hdi_plat_ss`）多媒体链路封装。
- 诊断采集能力：APP runtime provider 通过 HDI 公共接口采集 OS/VI/AO/AI 诊断数据。

### 2.1 三级索引表（能力 -> 头文件 -> 关键实现文件）

| 能力 | 头文件 | 关键实现文件 |
|---|---|---|
| OS 抽象（线程/锁/内存/时间） | `modules/hdi/include/hdi_os.h` | `modules/hdi/src/hdi_os/hdi_os.c`, `modules/hdi/src/hdi_os/hdi_os_thread.c`, `modules/hdi/src/hdi_os/hdi_os_mutex.c`, `modules/hdi/src/hdi_os/hdi_os_mem.c` |
| 基础硬件 IO（GPIO/UART/I2C/PWM/WDT） | `modules/hdi/include/hdi_gpio.h`, `hdi_uart.h`, `hdi_i2c.h`, `hdi_pwm.h`, `hdi_wdt.h` | `modules/hdi/src/hdi_hw/hdi_gpio.c`, `hdi_uart.c`, `hdi_i2c.c`, `hdi_pwm.c`, `hdi_wdt.c` |
| 传感器与设备（ADC/Key/Hotplug/Disk/TOF/IMU/IRCut/Light） | `modules/hdi/include/hdi_adc.h`, `hdi_key.h`, `hdi_hotplug.h`, `hdi_disk.h`, `hdi_tof.h`, `hdi_imu.h`, `hdi_ircut.h`, `hdi_light.h` | `modules/hdi/src/hdi_drv/hdi_adc/hdi_adc.c`, `hdi_drv/hdi_tof/hdi_tof.c`, `hdi_drv/hdi_imu/hdi_imu.c`, `hdi_drv/hdi_ircut/hdi_ircut.c`, `hdi_drv/hdi_light/hdi_light.c` |
| 音视频（AI/AO/VI） | `modules/hdi/include/hdi_ai.h`, `hdi_ao.h`, `hdi_vi.h` | `modules/hdi/src/hdi_audio/hdi_ai.c`, `hdi_audio/hdi_ao.c`, `hdi_video/hdi_vi.c` |
| 平台适配（SigmaStar） | （平台内部封装） | `modules/hdi/src/hdi_plat_ss/ssplat_sys.c`, `ssplat_vif.c`, `ssplat_isp.c`, `ssplat_venc.c`, `ssplat_vdec.c` |
| 诊断数据 Provider | `include/app/app_diag_managed_providers.h` | `modules/app/src/app_diag/provider/hdi/app_diag_hdi_*_provider.c` |

## 3. `modules/api` 功能介绍

`api` 负责可跨业务复用的中间层能力。

- 容器与数据结构：list/hash/ring/ringbuf/priority_queue/skiplist/rbtree 等。
- 配置与文件：ini/toml/dict/filecfg 解析与管理。
- 编解码与加密：byteorder/hex/base64/md5/sha1/sha256/aes/crc 等。
- IPC 与网络：socket/multi_socket/conn_pool/local_ip/http_utils/ntp/wifi。
- 协议与外部连接：curl/websocket/mqtt/zmq。
- 业务支撑算法：fsm/bt/decisiontree/blackboard/evaluator/robot 相关算法。
- 多媒体与外设支持：audio/video/dvr/rtsp/qrcode。
- 诊断数据能力：APP runtime provider 通过 API 公共接口提供消息、媒体、网络、事件等诊断数据。

### 3.1 三级索引表（能力 -> 头文件 -> 关键实现文件）

| 能力 | 头文件 | 关键实现文件 |
|---|---|---|
| 容器与数据结构 | `modules/api/include/api_list.h`, `api_hash.h`, `api_ring.h`, `api_ringbuf.h`, `api_priority_queue.h`, `api_skiplist.h`, `api_rbtree.h` | `modules/api/src/api_container/api_list.c`, `api_hash.c`, `api_ring.c`, `api_ringbuf.c`, `api_priority_queue.c`, `api_skiplist.c`, `api_rbtree.c` |
| 配置与文件 | `modules/api/include/api_ini.h`, `api_toml.h`, `api_dict.h`, `api_filecfg.h` | `modules/api/src/api_config/api_ini.c`, `api_toml.c`, `api_dict.c`, `api_filecfg.c` |
| JSON 工具 | `modules/api/include/api_json.h` | `modules/api/src/api_utils/api_json.c` |
| 编解码与加密 | `modules/api/include/api_hex.h`, `api_base64.h`, `api_md5.h`, `api_sha1.h`, `api_sha256.h`, `api_aes.h`, `api_crc.h` | `modules/api/src/api_codec/api_hex.c`, `api_crypto/api_base64.c`, `api_md5.c`, `api_sha1.c`, `api_sha256.c`, `api_aes.c`, `api_crc.c` |
| IPC 与网络 | `modules/api/include/api_msg.h`, `api_event.h`, `api_zmq.h`, `api_socket.h`, `api_multi_socket.h`, `api_conn_pool.h`, `api_http_utils.h`, `api_ntp.h` | `modules/api/src/api_ipc/api_msg.c`, `api_event.c`, `api_zmq.c`, `api_network/api_socket.c`, `api_multi_socket.c`, `api_conn_pool.c`, `api_http_utils.c`, `api_ntp.c` |
| 协议接入（curl/ws/mqtt） | `modules/api/include/api_curl.h`, `api_websocket.h`, `api_mqtt.h` | `modules/api/src/api_protocol/api_curl.c`, `api_websocket.c`, `api_mqtt.c` |
| 业务算法（AI/Robot） | `modules/api/include/api_fsm.h`, `api_bt.h`, `api_decisiontree.h`, `api_blackboard.h`, `api_evaluator.h`, `api_pid.h`, `api_astar.h`, `api_kalman.h` | `modules/api/src/api_ai/api_fsm.c`, `api_bt.c`, `api_decisiontree.c`, `api_blackboard.c`, `api_evaluator.c`, `modules/api/src/api_robot/api_pid.c`, `api_astar.c`, `api_kalman.c` |
| 多媒体与外设支持 | `modules/api/include/api_audio.h`, `api_video.h`, `api_dvr.h`, `api_rtsp.h`, `api_qrcode_zbar.h`, `api_qrcode_zxing.h` | `modules/api/src/api_audio_pipe/api_audio.c`, `api_video_pipe/api_video.c`, `api_dvr/api_dvr_record.c`, `api_rtsp/api_rtsp.c`, `api_qrcode/api_qrcode_zbar.c`, `api_qrcode/api_qrcode_zxing.c` |
| 诊断 Provider | `include/app/app_diag_managed_providers.h` | `modules/app/src/app_diag/provider/api/app_diag_api_*_provider.c` |

## 4. `modules/app` 功能介绍

`app` 是业务聚合层，负责命令执行编排与运行时集成。

- 诊断运行时框架：
  - `app_diag_center`：总控入口。
  - `app_diag_registry`：命令注册与索引。
  - `app_diag_dispatcher`：命令分发执行。
  - `app_diag_node_bridge`：节点桥接。
- IPC 适配层：
  - `app_diag_ipc_adapter_cmdserver`：与 `cmd_server` 的协议适配。
  - `app_diag_cmd_node`：命令节点交互。
- Provider 层：
  - `perf`（CPU/MEM/FLASH/SD）
  - `ai`
  - `uart`
  - `uart_maint`
  - `archive_maint`
- 参数与结果处理：
  - 参数解析（`app_diag_json_param`）
  - 结果封装（`app_diag_result_json`）
- 应用通道能力：
  - `app_uart*` 串口升级与报文
  - `app_zmq` 通信适配

### 4.1 三级索引表（能力 -> 头文件 -> 关键实现文件）

| 能力 | 头文件 | 关键实现文件 |
|---|---|---|
| 诊断中心与注册分发 | `modules/app/include/app_diag_center.h`, `app_diag_registry.h`, `app_diag_dispatcher.h`, `app_diag_node_bridge.h` | `modules/app/src/app_diag/framework/app_diag_center.c`, `app_diag_registry.c`, `app_diag_dispatcher.c`, `app_diag_node_bridge.c` |
| IPC 适配与命令节点 | `modules/app/include/app_diag_ipc_adapter.h`, `app_diag_cmd_node.h` | `modules/app/src/app_diag/ipc/app_diag_ipc_adapter_cmdserver.c`, `app_diag_cmd_node.c` |
| Provider（PERF/AI/UART/UART_MAINT/ARCHIVE_MAINT） | `modules/app/include/app_diag_perf_provider.h`, `app_diag_ai_provider.h`, `app_diag_uart_provider.h`, `app_diag_uart_maint_provider.h`, `app_diag_archive_maint_provider.h` | `modules/app/src/app_diag/provider/app_diag_perf_provider_cpu.c`, `app_diag_perf_provider_mem.c`, `app_diag_perf_provider_sd.c`, `app_diag_perf_provider_flash.c`, `app_diag_ai_provider.c`, `app_diag_uart_provider.c`, `app_diag_uart_maint_provider.c`, `app_diag_archive_maint_provider.c` |
| 参数解析与结果封装 | （内部头）`modules/app/src/app_diag/core/app_diag_json_param.h`, `app_diag_result_json.h` | `modules/app/src/app_diag/core/app_diag_json_param.c`, `app_diag_result_json.c` |
| 应用通道（UART/ZMQ） | `modules/app/include/app_uart.h`, `app_uart_packet.h`, `app_uart_ota.h`, `app_zmq.h` | `modules/app/src/app_uart/app_uart.c`, `app_uart_packet.c`, `app_uart_ota.c`, `modules/app/src/app_zmq.c` |

## 5. 使用边界

1. `hdi` 只向上提供硬件/OS 能力，不依赖 `api/app`。
2. `api` 提供通用能力，不依赖 `app`。
3. `app` 负责聚合与编排，可以依赖 `hdi/api`。
4. 新功能优先落在正确层级，禁止把业务逻辑下沉到 `cmd_server` 或上浮到 `cli`。

## 6. 变更影响矩阵（强制回归）

> 适用纳管模块：`hdi`、`api`、`app`、`sensor`、`proto`、`proto_c`。
> 应用回归默认包含：`prog_pcr02`（公共主应用）+ 受影响专项应用。

| 变更模块 | 必回归应用 | 必回归命令（最小集合） | mode | preconditions | 回归目标 |
|---|---|---|---|---|---|
| `modules/hdi` | `prog_pcr02`, `prog_product_test`, `prog_cmd_server` | `diag.sys.ping.run`, `diag.sys.list.run`, `diag.provider.registry.state.list.run`, `diag.perf.cpu.run` | APP + PRODUCT_TEST | `cmd_server` 与目标业务进程在线 | 验证硬件/OS 抽象稳定、诊断链路可用 |
| `modules/api` | `prog_pcr02`, `prog_product_test`, `prog_cli` | `diag.sys.catalog.run`, `diag.sys.help.run`, `diag.perf.mem.run`, `diag.perf.flash.run` | APP + PRODUCT_TEST | PERF provider 为 UP（默认可由 `diag.provider.up.run` 拉起） | 验证通用算法/协议/编解码未回归 |
| `modules/app` | `prog_pcr02`, `prog_product_test`, `prog_cli`, `prog_cmd_server` | `diag.sys.list.run`, `diag.provider.up.run`, `diag.provider.down.run`, `diag.provider.registry.state.list.run`, `diag.provider.manager.state.list.run`, `diag.app.ai.wakeup.start.run`, `diag.app.uart.versions.get.run` | APP（AI/UART 命令）+ PRODUCT_TEST（基础命令） | APP 模式下 `APP_AI`、`APP_UART` provider 可上线 | 验证命令注册/分发/provider 生命周期 |
| `modules/sensor` | `prog_pcr02` | `diag.sys.list.run`, `diag.provider.registry.state.list.run` | APP | `prog_pcr02` 启动完成，命令链路可达 | 验证主应用启动链路与传感器相关集成稳定 |
| `modules/proto` | `prog_pcr02`, `prog_cmd_server` | `diag.sys.ping.run`, `diag.sys.catalog.run` | APP | 命令协议编解码路径启用 | 验证 C++ 协议编解码与 IPC 命令链路 |
| `modules/proto_c` | `prog_product_test`, `prog_pcr02` | `diag.sys.list.run`, `diag.provider.registry.state.list.run` | PRODUCT_TEST 为主（APP 补充） | `prog_product_test` 可启动并接入 `cmd_server` | 验证 C 协议编解码与产测链路稳定 |

## 7. 回归执行规则

1. 任一模块改动，必须先通过其对应“最小命令集合”。
2. 涉及跨层改动（如 `hdi+api`、`api+app`）时，回归集合按并集执行。
3. `app` 改动默认追加 provider 上下线测试（`diag.provider.up/down.run`）。
4. `pcr02` 作为公共主应用，除构建成功外必须至少完成一次命令链路 smoke。

## 8. 新增模块判定清单（避免无效拆分）

以下条件必须同时满足，才允许新增模块：

1. 在第 1.1 节与第 2-4 节检索后，确认现有模块无等价能力。
2. 能力不适合放入现有分层（`hdi/api/app`）且会被多个应用长期复用。
3. 有明确公共接口边界（至少包含对外头文件与最小实现集合）。
4. 已给出“复用现有模块不可行”的证据（性能、依赖、生命周期、职责冲突）。
5. 已给出回归策略（受影响应用、命令、构建目标）。

不满足以上任一条件时，不新增模块，优先扩展现有模块。
