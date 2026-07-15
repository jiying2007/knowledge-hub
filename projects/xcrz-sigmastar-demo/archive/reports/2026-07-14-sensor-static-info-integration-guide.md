---
title: PCR02 Sensor 静态数据上报 Task/App 联调指南
date: 2026-07-14
project: xcrz-sigmastar-demo
tags:
- pcr02
- sensor
- device-static-info
- task
- app
- protobuf
- chip-id
- schema-v2
- integration-guide
- source-reviewed
- manual-validation-pending
source: current-session-source-contract-review
captured_at: 2026-07-14
last_verified: 2026-07-14
manual_validation_reason: Schema 2.0、Chip ID、HDI 初始化和静态发布源码/构建契约已核对；当前检出树缺少完整 modules/task 源码，且尚未完成板端 Task/App/Bridge 与 MI_SYS UUID 实机联调。
required_followup: 使用包含同一版 Proto/HDI/Sensor 改动的制品重新生成 Task/App Protobuf 代码，执行本文 Schema 2.0 验收用例，并补充 Chip ID 与 Task/App/Bridge 消费日志。
memory_candidate: false
id: xcrz-sigmastar-demo-sensor-static-info-integration-guide-20260714
kind: project-archive
domain: projects/xcrz-sigmastar-demo
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-08-14'
review_status: manual-entry-pending-review
promotion: none
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-14'
manual_validation_pending: true
summary_zh: 基于当前源码固化 DeviceStaticInfo Schema 2.0 的 Chip ID、MAC/SN、版本、标定状态、同进程订阅、缓存、旧协议兼容和 Task/App 联调要求；源码与定向构建契约已核对，板端联调待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
---

# PCR02 Sensor 静态数据上报 Task/App 联调指南

## 摘要

本文固化 PCR02 `DeviceStaticInfo` Schema 2.0 静态数据上报的消费契约，供同一 `prog_pcr02` 进程中的 Task、`pcr02::Application`、Bridge、IoT 等模块联调。该接口发布的是“最新状态全量快照”：生产者缓存不可配置的 SoC Chip ID，以及 MAC、SN、SoC/MCU/左右电机版本、Camera/TOF/IMU 标定状态和左右电机持久化标定结果；内容变化时立即发布，稳定后每 10 秒重发缓存；只有尚未成功读取的数据源才每 30 秒重试。

本文结论来自 2026-07-14 当前工作区源码核对，不包含真实设备 Task/App/Bridge 联调结果。由于本地工作区存在未提交源码和生成库改动，本文只能作为当前源码快照的 `reviewing` 归档候选，不能直接提升为 release 已验证事实。

## 问题对比表

| 问题 | 现象/信号 | 核心判断 | 当前结论 | 影响 |
| --- | --- | --- | --- | --- |
| Task/App 如何获得静态数据 | Sensor 启动、Task/App 初始化顺序不同 | PUB/SUB 不补发订阅前消息，必须依赖周期性全量快照 | 同进程订阅 `sensor/device/static/info`，消费者维护一份最新缓存 | 首包等待应按 10 秒重发周期设计 |
| 如何区分“未标定”和“读取失败” | 标定状态与读取质量是两个维度 | 仅看字符串或 `all_sources_ready` 会误判 | 同时读取 `meta.quality`、`meta.reason` 和 `status` | 文件缺失可表示权威的 `NOT_CALIBRATED` |
| Chip ID 如何接入 | Chip ID 是 SoC 硬件根标识，MAC/SN 仍可能被配置或更换 | 三者必须使用独立字段和质量元数据 | `chip_id` 来自 `VSHDISYS_GetChipId`，固定为 16 位小写十六进制 | 读取前必须完成 HDI `SOC_SYSTEM` 初始化 |
| Schema 1.x 消费方是否可直接复用 | 2.0 调整了身份、版本和标定字段号 | 同类型字段号复用可能被旧代码静默误解 | Task/App 必须使用同一版 `.proto` 重新生成绑定，并在取字段前拒绝非 major 2 | 不能只依赖 Protobuf “未知字段可跳过” |
| 左右电机如何兼容旧协议 | 旧协议只有一个电机版本字段 | 旧协议不能表达左右不一致 | 新协议分别上报；旧协议不一致时发布 `0.0.0` | 新消费者不能再用旧值覆盖左右真实值 |
| C App 和独立进程如何接入 | Transport 使用 `inproc://sensor` 和 C++ Protobuf | C ABI 与跨进程都不能直接复用当前订阅对象 | C 模块由上层 C++ 适配；独立进程由 Bridge/IPC 转发 | 不应让底层 App 反向依赖 Sensor 内部实现 |
| 电机标定过程是否可当事件流使用 | 静态 topic 是状态快照，PUB/SUB 可丢中间包 | 不能保证观察到每个 `RUNNING` 状态 | 命令链路确认本次执行结果，静态 topic 核对最终持久化状态 | 避免把状态快照误作命令应答 |

## 结论对比表

| 主题 | 结论 | 依据 | 风险/边界 |
| --- | --- | --- | --- |
| 接口主契约 | Channel=`sensor`，Topic=`sensor/device/static/info`，消息=`proto.sensor_info.DeviceStaticInfo`，Schema=`2.0` | `channel_list.*`、`sensor_info.proto` | 当前仅保证同进程传输；1.x 与 2.0 不兼容 |
| 发布策略 | 启动立即发布非串口快照；串口稳定等待约 2 秒；变化立即发布；稳定后 10 秒重发 | `sensor_static_info_service.cpp` | 后启动订阅者可能错过启动首包 |
| 缓存与重试 | 读取成功后只从缓存发布；仅未成功源每 30 秒重试 | 静态服务的 source-ready mask 和 retry 调度 | `all_sources_ready=false` 不等于整包无效 |
| 电机标定时序 | MCU 内部超时 35 秒，应用等待窗口 40 秒，状态轮询 500ms | `app_uart_packet.h` 与静态服务共用常量 | 消费方不要再定义另一套超时 |
| 扩展兼容 | 按枚举查找 repeated 元素；仅支持 major=2，接受兼容的新增 minor 和未知字段 | Protobuf 向前兼容和 Schema 字段 | 不允许依赖 repeated 下标、固定长度或源码声明顺序 |
| 验证状态 | 源码契约已复核，板端跨模块联调尚未完成 | 当前工作区定向检索 | 保持 `reviewing`、`manual_validation_pending=true` |

## 关键结论

1. `DeviceStaticInfo` Schema 2.0 是新消费者的唯一静态数据事实源；旧 `sensor/mcu/version` 只用于存量版本协议兼容。
2. `chip_id` 是不可配置的 64-bit SoC UUID，格式必须是 16 位小写十六进制且不带 `0x`；MAC/SN 仍按可配置身份分别处理。
3. 每条消息都是完整快照，Task/App 只需保存最新一份；sequence 丢失或不连续不要求补包。
4. 消费方必须先校验 `schema_major==2`，再逐字段判断质量和状态；不能用 `all_sources_ready` 作为整包准入门槛。
5. 左右电机版本和标定结果必须分别消费；整体 `MOTOR_HALL` 仅用于概览，不能反推单侧结果。
6. 当前 topic 只在同一进程有效；跨进程和纯 C 模块需要明确的适配层。

## 接口契约

### Transport 与 Schema

| 项目 | 契约 |
| --- | --- |
| Channel | `sensor` |
| Topic | `sensor/device/static/info` |
| Protobuf | `proto.sensor_info.DeviceStaticInfo` |
| 当前版本 | `schema_major=2`、`schema_minor=0` |
| 传输地址 | `inproc://sensor` |
| 消息形态 | 全量、可幂等覆盖的最新状态快照 |
| 周期 | 稳定后每 10 秒重发 |
| 未成功源重试 | 每 30 秒 |
| UART 首次读取 | Sensor 后台线程先等待约 2 秒 |

Protobuf 已处理序列化和字节序；这里不存在共享 C struct 的对齐契约。消费者不得校验固定包长，也不得依赖字段在 `.proto` 中的声明顺序。Schema 2.0 在联调阶段调整过字段号，Task/App 必须从同一版 `sensor_info.proto` 重新生成并链接 `.pb.*`/语言绑定，不能混用 1.x 生成代码或旧 `libproto`。

### 字段号和扩展区间

| 区间 | 当前字段 | 约束 |
| --- | --- | --- |
| 1 | `header=1` | 公共消息头 |
| 2-9 | `schema_major=2`、`schema_minor=3`、`content_revision=4`、`all_sources_attempted=5`、`all_sources_ready=6` | 7-9 约定留给协议元信息扩展 |
| 10-19 | `chip_id=10`、`wifi_mac=11`、`sn=12` | 按硬件根标识、可配置身份排序；13-19 约定预留 |
| 20-29 | `versions=20` | 21-29 约定留给版本类扩展 |
| 30-39 | `calibrations=30`、`motor_hall_calibrations=31` | 32-39 约定留给标定类扩展 |
| 40-49 | 当前无字段 | 约定留给硬件能力类扩展 |
| 50-59 | 当前无字段 | 约定留给生产/出厂类扩展 |

这里的“约定预留”是当前接口治理规则；新增字段应进入对应区间并提升 `schema_minor`，不得复用已发布字段号或改变既有字段类型。发生不兼容语义或字段号调整时必须提升 `schema_major`。

### 字段映射

| 业务数据 | 新协议位置 |
| --- | --- |
| SoC Chip ID | `chip_id.value`，来源为 `VSHDISYS_GetChipId`/`MI_SYS_ReadUuid`；64-bit UUID 格式化为 16 位小写十六进制，不带 `0x` |
| Wi-Fi MAC | `wifi_mac.value`，来源为 `VSAPIWIFI_GetMacAddress` |
| SN | `sn.value`，来源为现有 factory store 接口 |
| SoC/System 版本 | `versions` 中 `component=SOC`、`kind=SYSTEM` |
| MCU App 版本 | `versions` 中 `component=MCU`、`kind=APP` |
| 左电机 App 版本 | `versions` 中 `component=MOTOR_LEFT`、`kind=APP` |
| 右电机 App 版本 | `versions` 中 `component=MOTOR_RIGHT`、`kind=APP` |
| Camera 标定 | `calibrations` 中 `type=CAMERA` |
| TOF 标定 | `calibrations` 中 `type=TOF` |
| IMU 标定 | `calibrations` 中 `type=IMU` |
| 电机整体状态 | `calibrations` 中 `type=MOTOR_HALL` |
| 左右电机状态 | `motor_hall_calibrations` 中分别按 `side=LEFT/RIGHT` 查找 |

标定文件为：

- `/factory/camera_extrinsics.bin`
- `/factory/tof_calibration.toml`
- `/factory/imu_calibration.toml`

存在、是普通文件且大小大于 0 时表示已标定；文件不存在或为空时表示权威的未标定结果，而不是通信异常。

### 元数据和错误语义

| `meta.quality` | 含义 | 消费策略 |
| --- | --- | --- |
| `UNKNOWN` | 尚未完成首次读取 | 显示读取中/未知，不使用 value |
| `VALID` | 当前结果权威有效 | 正常使用 |
| `STALE` | 最新尝试失败，保留历史有效值 | 可按业务继续使用，同时显示降级 |
| `INVALID` | 读取失败且没有历史有效值 | 保留消费者旧缓存或显示不可用，不把空值当有效值 |

`meta.reason` 用于解释 `NOT_READY`、`NOT_FOUND`、`EMPTY`、`IO_ERROR`、`TIMEOUT`、`PROTOCOL_ERROR`、`INVALID_DATA` 等状态；`native_error` 保存底层错误码。文件缺失或为空时可出现 `quality=VALID`、`status=NOT_CALIBRATED`、`reason=NOT_FOUND/EMPTY`，表示已权威确认未标定。

Chip ID 首次成功后作为不可变值进入缓存，不再周期读取；读取失败时为 `INVALID`，已有成功缓存后再次读取失败时为 `STALE`，并随其他未成功源每 30 秒重试。当前实现把 `VSHDISYS_GetChipId` 失败统一映射为 `IO_ERROR`，具体原因看 `native_error`；若为 `VS_ERROR_INVALID_STATE`，优先检查进程是否在启动 Sensor 前以 `VSHDI_INIT_FLAG_SOC_SYSTEM` 初始化 HDI。

### 全局状态字段

- `all_sources_attempted=false`：通常是启动首包，UART 数据尚未首次读取。
- `all_sources_ready=false`：至少一个源尚未成功，不代表其他字段无效，也不代表消息不可解析。
- `header.sequence`：每次发布递增；PUB/SUB 丢包、进程重启导致间断或回退都属于可接受情况。
- `content_revision`：仅在缓存业务语义变化时递增；周期重发可出现新 sequence、相同 revision。

消费者收到相同 `content_revision` 时可跳过昂贵的 UI 重建或数据库写入，但仍应更新“最近收到时间”和各字段尝试时间。

## Task/App 消费规则

### C++ 同进程模块

1. 模块初始化时尽早创建 `common::ThreadSubscriber(channel_sensor_, topic_sensor_device_static_info_, 2)`。
2. 在独立消费线程中调用 `pollReceive()`，或加入模块现有 `ZmqPoller`。
3. `ParseFromString()` 失败时保留上一份缓存，不清空业务状态。
4. `ParseFromString()` 后立即检查 `schema_major==2`，通过前不得读取或写入任何业务字段；minor 增加时继续读取已知字段。
5. Task/App 构建必须使用与 Sensor 制品一致的 Schema 2.0 生成代码和 `libproto`，禁止只更新头文件或只替换动态库。
6. 将通过 major 检查的消息整体复制到受 mutex 保护的本地缓存，业务线程读取缓存副本。
7. repeated 字段始终按枚举查找，不允许用固定下标。
8. 模块退出时，先从 Poller 移除 socket，再销毁 Subscriber；不要在当前回调栈中直接销毁。

伪代码：

```cpp
auto payload = subscriber.pollReceive(500);
if (payload) {
    DeviceStaticInfo next;
    if (next.ParseFromString(*payload) && next.schema_major() == 2U) {
        lock(cache_mutex);
        cache.CopyFrom(next);
        has_cache = true;
    }
}
```

### C App

`modules/app` 下的纯 C 代码不应直接依赖 C++ `ThreadSubscriber`、C++ Protobuf 或 Sensor 内部头文件。推荐由 `pcr02::Application`、Task 或 Bridge 等 C++ owner 订阅并缓存，再提供窄 C ABI，例如只暴露所需的标定状态、质量、原因和更新时间。

### 独立进程

当前 Transport 使用 `inproc://sensor`，独立产测程序、OTA 程序、PC 工具或独立 App 可执行程序无法直接订阅。确需跨进程时，应新增 Bridge/TCP/MQTT/其他 IPC 转发契约，并单独定义字段裁剪、版本兼容、鉴权和错误语义。

## 启动和超时约定

| 场景 | 建议 |
| --- | --- |
| 等待第一条静态快照 | Subscriber 建立后最多等待 15 秒再判定无消息 |
| 首包 UART 字段未就绪 | 接受 `UNKNOWN/NOT_READY`，等待变化快照或 10 秒周期快照 |
| 单字段读取失败 | 继续使用其他有效字段；生产者仅对未成功源 30 秒重试 |
| 电机标定运行 | 使用统一 500ms 轮询和 40 秒应用等待窗口 |
| sequence 缺失 | 不补包，直接覆盖为最新完整快照 |
| 进程重启 | 接受 sequence/revision 重新起算，不仅凭数字大小拒绝消息 |

15 秒首包超时来自 10 秒缓存重发余量，不应缩短为 UART 的 2 秒稳定等待。Sensor 可能早于 Task/App 建立订阅，PUB/SUB 不会补发订阅前的启动消息。

## 旧协议兼容和迁移

- Sensor 每次发布新静态快照时继续兼容发布旧 `sensor/mcu/version`。
- 旧协议只有单一电机版本：左右版本均有效且相同才发布实际值；不一致、任一侧无效或缺失时发布 `0.0.0`。
- 新消费者不得把旧 topic 写入新缓存，否则 `0.0.0` 可能覆盖新协议中的左右真实版本。
- Bridge 下游若仍只有单一电机版本字段，维持上述回退；若可扩展，应增加左右独立字段。
- 旧 topic 只兼容版本信息，没有 Chip ID、MAC/SN、标定状态或左右电机标定结果的等价字段。
- Schema 兼容策略为“major 严格、minor 宽松”：当前消费者仅支持 major 2，可忽略兼容新增的未知字段和 repeated 枚举项。
- Schema 1.x 与 2.0 不做线兼容承诺：1.x 的 `wifi_mac=10`、`sn=11`、`versions=12`、`calibrations=13`、`motor_hall_calibrations=14` 已调整为 2.0 的身份/版本/标定分区。旧生成代码可能把字段 10 的 Chip ID 静默当作 MAC，因此必须在消费业务字段前拒绝非 major 2，而不是依赖解析失败兜底。

## 电机标定职责边界

静态 topic 是最终状态快照，不是电机标定命令应答：

- 发起标定以及确认本次命令成功/失败，继续使用现有 UART/diag/产测命令链路。
- 静态 topic 用于页面展示、设备信息查询、启动恢复和最终持久化结果核对。
- 左右结果以 `motor_hall_calibrations` 为准；整体 `MOTOR_HALL` 只用于概览。
- 未被最近一次持久化操作选中的一侧可能是权威 `UNKNOWN`，不能自动解释为失败。
- 生产者与产测、diag 共用：电机内部超时 35 秒、额外等待 5 秒、总等待 40 秒、轮询 500ms。

## 联调验收矩阵

| 用例 | 操作 | 预期结果 |
| --- | --- | --- |
| 正常已标定设备 | 启动 Sensor 和 Task/App | 15 秒内收到可解析 Schema 2.0；Chip ID、MAC/SN、版本有效；标定状态与设备一致；10 秒后收到周期快照 |
| Chip ID 格式 | 读取 `chip_id` | `quality=VALID`，value 严格匹配 16 位小写十六进制且不含 `0x`；重发快照值保持一致 |
| Chip ID 首读失败 | 模拟 `MI_SYS_ReadUuid` 瞬态失败 | 不影响其他字段消费；Chip ID 为 `INVALID + IO_ERROR` 并保留 `native_error`，底层恢复后最迟随 30 秒重试变为 `VALID` |
| Chip ID 初始化缺失 | 不带 `VSHDI_INIT_FLAG_SOC_SYSTEM` 启动进程 | Chip ID 为 `INVALID + IO_ERROR`，`native_error=VS_ERROR_INVALID_STATE`；修正初始化 flags 并重启进程后，首次读取变为 `VALID` |
| Schema 1.x 消费方 | 使用旧生成代码或旧 `libproto` 进行负向测试 | 集成层识别制品不一致并阻止发布；运行时适配层不得把 Chip ID 显示为 MAC，收到非 major 2 必须拒绝整包业务字段 |
| UART 首次读取未完成 | 观察启动前后消息 | 可先收到 `all_sources_attempted=false`；后续 UART 字段变化；消费者不阻塞、不清空其他字段 |
| 标定文件不存在 | 移除某一标定文件 | 对应字段为 `VALID + NOT_CALIBRATED + NOT_FOUND`，其他字段继续可用 |
| 标定文件为空 | 创建 0 字节标定文件 | 对应字段为 `VALID + NOT_CALIBRATED + EMPTY` |
| 左右电机版本不同 | 使用左右版本不一致的设备/模拟响应 | 新协议分别保留真实值；旧协议电机版本为 `0.0.0` |
| 电机标定成功/失败/超时 | 通过既有命令执行标定 | 命令链路给出本次结果；静态快照最终反映左右持久化终态；最长等待 40 秒 |
| 消费者晚启动 | Sensor 先启动，延迟创建 Subscriber | 不要求收到启动首包；下一个 10 秒周期内收到完整快照 |
| 跨进程误用 | 独立进程创建 ThreadSubscriber | 无法收到 `inproc` topic；应转为 Bridge/IPC 需求，不归因于 Sensor 发布失败 |

## 调试和数据安全

测试固件可定义 `SENSOR_STATIC_INFO_PUBLISH_DEBUG=1`，检查 `[static-publish]` 和 `[legacy-version-publish]` 日志。日志包含 Chip ID、MAC、SN、版本、标定状态及左右电机详细信息，只允许在受控测试环境使用；正式固件保持宏关闭，归档中不记录真实 Chip ID、MAC、SN、设备地址、凭据、原始日志或二进制。

## 联调前置检查

1. Proto、HDI、Sensor、Task/App 必须来自同一源码基线；确认生成的 `sensor_info.pb.*` 已包含 `chip_id=10`、`versions=20`、`calibrations=30` 和 `motor_hall_calibrations=31`。
2. 承载 Sensor 的主进程必须在启动 Sensor 前成功调用 `VSHDI_Init(VSHDI_INIT_FLAG_OS_CORE | VSHDI_INIT_FLAG_SOC_SYSTEM [| VSHDI_INIT_FLAG_MEMORY_POOL])`。Chip ID 依赖 `SOC_SYSTEM`；内存池只按进程实际需要选择，不是读取 Chip ID 的前置条件。当前 `app_main` 使用三项全开配置。
3. 重新构建受影响的 Proto、HDI、Sensor 和最终 App/Task；若设备通过 image/OTA 部署，后编译的 app 不会自动进入已生成制品，必须重新生成并部署 image/OTA。
4. 启动消费者后先打印一次 Schema、sequence、revision、各字段 quality/reason；仅在受控测试固件开启完整发布日志，采证时对 Chip ID、MAC、SN 做脱敏。
5. 记录同一轮联调的源码提交/dirty 标识、Proto 生成物、可执行文件和库版本，避免把新 Sensor 与旧 Task/App 或旧 `libproto` 混装。

## 必要实现位点

| 位点 | 逻辑/作用 | 为什么关键 |
| --- | --- | --- |
| `modules/proto/sensor_info.proto` | 定义 Schema 2.0、字段号分区、Chip ID、质量/原因、版本和标定结构 | 是 Task/App 的序列化与兼容基线 |
| `include/hdi/hdi_init.h`、`modules/hdi/src/hdi_init.c` | 按 flags 初始化 `OS_CORE`、`SOC_SYSTEM` 和可选内存池 | `SOC_SYSTEM` 是读取 SigmaStar UUID 的运行时前置条件 |
| `include/hdi/hdi_sys.h`、`modules/hdi/src/hdi_hw/hdi_sys.c` | 通过 `VSHDISYS_GetChipId` 封装 `MI_SYS_ReadUuid` | 统一 Chip ID 的 HDI 边界和错误码语义 |
| `app_main/app_main.c` | 主应用以 `OS_CORE | SOC_SYSTEM | MEMORY_POOL` 初始化 HDI | 保证 Sensor 启动前 MI_SYS 已就绪 |
| `modules/common/transport/channel_list.{h,cpp}` | 定义 channel 和 topic 常量 | 避免消费方硬编码不一致的字符串 |
| `modules/sensor/main/sensor_static_info_service.cpp` | 读取并格式化 Chip ID，负责缓存、刷新、重试、时序和全量发布 | 决定首包、周期、字段质量和 revision 语义 |
| `modules/sensor/main/device_identity_service.cpp` | 通过 Wi-Fi API 获取 MAC | 证明 MAC 不依赖 `/factory` 文件 |
| `modules/sensor/serial/sensor_serial.cpp` | 发布旧版本兼容消息 | 固化左右电机不一致时旧协议回退 `0.0.0` |
| `include/app/app_uart_packet.h` | 统一电机标定超时和轮询常量 | 保证 Sensor、产测和 diag 时序一致 |
| `modules/common/transport/thread_pub_sub.*` | 实现进程内 PUB/SUB | 明确同进程边界和 latest-snapshot 消费模型 |

## 验证记录

2026-07-14 在当前源码工作区执行定向源码与构建契约核对：

- 确认 channel/topic 为 `sensor` / `sensor/device/static/info`。
- 确认 `DeviceStaticInfo` 当前为 Schema 2.0，身份字段为 `chip_id=10`、`wifi_mac=11`、`sn=12`，版本和标定字段按 20/30 段分区。
- 确认 `VSHDISYS_GetChipId` 封装 `MI_SYS_ReadUuid`，Sensor 将 64-bit UUID 格式化为 16 位小写十六进制；主应用在 Sensor 前初始化 `SOC_SYSTEM`。
- 确认发布周期 10 秒、未成功源重试 30 秒、UART 启动稳定等待 2 秒。
- 确认 MAC 调用 `VSAPIWIFI_GetMacAddress`，三类标定使用 `/factory` 文件。
- 确认电机标定内部超时 35 秒、应用等待 40 秒、轮询 500ms，并由 Sensor/产测/diag 共用。
- 确认每次新快照发布后调用旧版本兼容发布。
- Proto、HDI、Sensor 和 App 定向构建目标已通过；HDI 公共头检查和导出符号核对未发现旧初始化接口残留调用。

验证边界：当前检出树没有完整 Task 消费源码，未部署设备，未实测 `MI_SYS_ReadUuid` 返回值，也未采集 Task/App/Bridge 的真实订阅日志；当前工作区存在与本主题并存的既有脏改动和生成库，且现有 Sensor 制品带 dirty 版本标识，归档不对这些改动作提交或发布判断。

## 未决项 / 后续建议

| 项目 | 说明 |
| --- | --- |
| Task 实际接入 | 当前检出树缺少完整 `modules/task` 源码，需要在 Task 所在源码树使用 Schema 2.0 重新生成绑定，套用本文 Subscriber/缓存规则并编译 |
| Bridge 下游字段 | 确认下游继续单电机版本兼容，还是扩展左右独立字段 |
| Chip ID 板端验证 | 多台设备核对 `MI_SYS_ReadUuid` 的稳定性、差异性和 16 位格式；验证瞬态失败后的 30 秒重试，以及 `VS_ERROR_INVALID_STATE` 修正 flags 后重启恢复 |
| 板端 HIL | 按验收矩阵补齐 Schema 2.0、启动、晚订阅、文件缺失、左右版本不一致和电机超时证据 |
| 跨进程需求 | 若产测或独立 App 需要数据，单独设计 Bridge/IPC，不扩大当前 inproc topic 的隐含职责 |
| 复核 | 板端联调完成后更新 validation refs；未完成前保持 reviewing，不提升为 active/runbook/AGENTS 规则 |

## 归档证据

- Source: 当前会话中的静态数据终态设计、实现审查与 Task/App 联调指南，以及 2026-07-14 当前源码定向核对。
- Topic: `sensor-static-info-integration-guide`。
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-14-sensor-static-info-integration-guide.md`。
- Sanitization: 未记录真实 Chip ID、MAC、SN、设备地址、凭据、原始日志、SDK 包或二进制内容。
- Provenance: `workspace://xcrz-sigmastar-demo` 当前工作区源码；实现尚未形成干净提交基线。
- Verification: Schema 2.0、Chip ID/HDI、静态缓存和定向构建契约核对完成；Task 与板端 Task/App/Bridge/UUID 联调 pending。
- Memory Candidate: no。
- Gate Result: archive candidate 可写入；人工复核和板端验证待完成。

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: Schema 2.0、Chip ID、HDI 初始化和定向构建契约已核对；当前检出树缺少完整 modules/task 源码，且尚未完成板端 Task/App/Bridge 与 MI_SYS UUID 实机联调。
required_followup: 使用包含同一版 Proto/HDI/Sensor 改动的制品重新生成 Task/App Protobuf 代码，执行本文 Schema 2.0 验收矩阵，并补充 Chip ID、消费日志和制品标识。
owner: leiwenjun
review_after: 2026-08-14
```
