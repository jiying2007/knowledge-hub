---
id: pcr02-tcpka-low-power-protocol-v1-20260722
title: PCR02 SoC TCPKA 协议 v1 与低功耗生命周期实现归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-code-and-build-summary
  from: current PCR02 SoC source plus 2026-07-22 local build and static-check evidence; runtime endpoints, raw logs and binaries
    deliberately not retained
  source_sha256: de8226e718197b5b68e8122a33f8a2ed9ae4ebdaed46bc52c0807e1027e32a12
  temporary_source_retained: false
review_after: '2026-10-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- tcpka
- low-power
- standby
- sleep
- deep-sleep
- protobuf
- dns
- product-sn
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-22-pcr02-tcpka-low-power-protocol-v1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-22'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 固化 PCR02 SoC TCPKA 协议 v1、产品 SN payload、DNS/IPv4 解析、WiFi firmware 布防及 STANDBY/SLEEP/DEEP_SLEEP 生命周期接入；源码构建和静态检查通过，板级与服务器联合验证仍待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SoC TCPKA 协议 v1 与低功耗生命周期实现归档

## 归档目的与结论边界

本文固化 PCR02 SoC 侧 TCP keepalive（TCPKA）配置协议、产品 SN payload、DNS/IPv4 解析、WiFi firmware 布防以及 STANDBY、SLEEP、DEEP_SLEEP 生命周期接入的当前实现。

当前结论是“协议与源码实现已完成，生成代码、静态检查及 SoC 全量应用构建已通过”。这不等于板级链路已经验收：服务器收包、生产 DNS、WiFi firmware keepalive、MCU 唤醒和 SoC 掉电重启仍需联合实机验证。因此本条目保持 `reviewing`，不得据此声明量产可用、发布通过或 owner 已签收。

本文不保存测试/生产服务器的具体地址、内网 IP、设备真实 SN、凭证、raw log、构建二进制或本机绝对路径。

## 目标与非目标

### 目标

- 上层只负责下发 TCPKA 服务器地址、端口、配置版本和协议版本。
- 产品 SN 与 wlan0 IPv4 由 Sensor 模块在 SoC 内部获取，避免上层重复传入可本地确定的数据。
- TCPKA 配置与实际低功耗布防分离，保证 RUNNING 阶段配置不会立即触发 WiFi suspend。
- STANDBY、SLEEP、DEEP_SLEEP 在进入不可逆阶段前完成所需唤醒源布防，失败则中止转换并恢复 RUNNING。
- SoC 与上层同步升级，不保留旧 `uid/device_ip/server_ip` 字段兼容。
- DNS hostname 与 IPv4 字符串使用同一套解析和候选地址回退逻辑。

### 非目标

- 本轮不改变 MCU PA8 唤醒脉冲宽度；继续保持 9 ms。
- 本轮不把 TCPKA 服务器配置固化在 Sensor 内部。
- 本轮不把未执行的板级、服务器或生产网络验证标记为通过。
- 本轮不定义服务器业务处理逻辑，只定义服务器必须解析的首包 payload v1。

## Proto 破坏性升级

`modules/proto/sensor_ctrl.proto` 中的 `KeepAlivePayload` 当前契约为：

```proto
message KeepAlivePayload {
    bool   enable           = 1;
    string server_host      = 2;
    uint32 server_port      = 3;
    uint32 revision         = 4;
    uint32 contract_version = 5;
}
```

字段语义：

| 字段 | 约束 | 语义 |
| --- | --- | --- |
| `enable` | bool | `true` 保存/更新配置，`false` 清除配置 |
| `server_host` | 非空；IPv4 字符串或 DNS hostname | TCPKA 服务端地址，由 Sensor 在布防时解析 |
| `server_port` | 1-65535 | TCPKA 服务端端口 |
| `revision` | 非零，单调递增 | 配置顺序、幂等和过期消息防护；disable 也必须携带新 revision |
| `contract_version` | 固定为 1 | 明确拒绝旧协议和未知新协议 |

旧版 `server_ip`、`uid`、`device_ip` 已删除，不做双读、字段回退或混合部署兼容。`contract_version` 使用 tag 5，可使旧版 tag 5 的 string wire type 无法被误认成合法的新协议版本；新 SoC 对非 1 版本明确返回失败。

## 配置 revision 语义

TCPKA 配置是带 tombstone 的单调状态，不应把 disable 当作“忘记最后版本”：

- 收到更大的 revision：接受，并更新 enable/disable 状态。
- 收到相同 revision 且内容完全一致：视为幂等成功。
- 收到相同 revision 但内容不同：拒绝，避免同一版本表达多个状态。
- 收到更小 revision：拒绝，避免乱序消息恢复旧配置。
- disable 成功后保留 revision tombstone，使旧 enable 消息不能重新激活 TCPKA。

`SensorEntry` 的 `KEEP_ALIVE` 命令使用 `low_power_mutex_` 的 `try_lock`。低功耗转换持锁期间拒绝配置变更，避免 TCPKA 已布防而服务器配置在 suspend 前被替换。

## 产品 SN 与 payload v1

产品 SN 不由上层传入。`SensorEntry` 通过 `DeviceIdentityService` 读取本机身份快照，再把产品 SN 传给 `Tcpka::configure()`。

SN 约束：

- 长度 1-63 字节；
- 只允许 ASCII 字母、数字、下划线和连字符；
- payload 中不带结尾 `NUL`；
- 日志不得打印、截断或哈希真实 SN。

TCP 建连后的首包与 WiFi firmware `tcpka_conn_add` 使用完全相同的二进制 payload：

| 偏移 | 长度 | 字段 | 编码 |
| ---: | ---: | --- | --- |
| 0 | 4 | magic | `FB FC FD FE` |
| 4 | 1 | version | `01` |
| 5 | 1 | reserved | `00` |
| 6 | 2 | total_len | 大端，值为 `10 + sn_len` |
| 8 | 2 | sn_len | 大端 |
| 10 | `sn_len` | product SN | ASCII，无 `NUL` |

服务器需要按 payload v1 同步升级，并以完整帧长度校验为准。旧测试工具只可参考连接和 keepalive 流程，不可作为新 payload 的兼容承诺。

## Tcpka 生命周期

核心接口位于 `modules/sensor/hardware/tcpka.h/.cpp`：

```text
configure()   只校验并保存 host/port/SN/revision
arm()         解析地址、建 TCP、下发 firmware session、进入 WiFi suspend
disarm()      退出 WiFi suspend、关闭 PM/session/socket，可重复重试清理
clearConfig() 带 revision tombstone 清除配置
reset()       模块退初始化时清理运行态和配置态
```

`configure()` 不执行 WiFi suspend。只有低功耗 transition owner 在准备进入 STANDBY、SLEEP 或 DEEP_SLEEP 时调用 `arm()`。

`arm()` 的关键顺序与平台参考实现一致：

1. 读取 wlan0 当前 IPv4。
2. 使用 `getaddrinfo(AF_INET, SOCK_STREAM)` 解析 `server_host`；IPv4 字符串和 DNS hostname 走同一路径。
3. 逐个尝试返回的 IPv4 地址；DNS multi-A 中一个地址失败时继续下一个。
4. 执行 WiFi PM0。
5. 创建 TCPKA firmware session，payload 使用上述十六进制字节序列。
6. dump session 状态，创建 TCP socket，绑定本地源端口 9000，非阻塞连接并发送同一 payload。
7. 等待约 300 ms，再次读取 session 状态。
8. 启用 TCPKA，执行 PM2，再进入 `setsuspendmode 1`。

TCP connect 和 send 均有 3 秒有界超时。创建 firmware session 后的失败不会简单清空本地标志；实现保留已完成步骤的清理状态，让 `disarm()` 能真实重试关闭 suspend、PM、session 和 socket。进入新一轮 arm 前还会清理可能由 DEEP_SLEEP 掉电残留的 firmware session 1。

## 低功耗模式接入

| 模式 | SoC 行为 | 允许/要求的唤醒源 | TCPKA 规则 |
| --- | --- | --- | --- |
| STANDBY | SoC suspend 后返回；IMU/TOF 切低功耗唤醒态 | MCU IMU、MCU TOF；已配置时可叠加 WiFi | TCPKA 可选；只要已配置就必须 arm 成功，否则拒绝进入 |
| SLEEP | SoC suspend 后返回；IMU/TOF 停止运行态采集 | SoC RTC、MCU WiFi，二者可同时启用 | RTC 秒数为 0 时 TCPKA 必须已配置；已配置时必须 arm 成功 |
| DEEP_SLEEP | SoC 掉电，由 MCU/WiFi 事件重新上电 | MCU WiFi keepalive | TCPKA 必须已配置并 arm 成功，随后 MCU 才可确认 ARMED 并切断 SoC 电源 |

STANDBY 不接受 RTC 参数；RTC 只属于 SLEEP。SLEEP 在既无 RTC 又无 TCPKA 时直接拒绝。DEEP_SLEEP 不依赖 SoC RTC，因为 SoC 会掉电。

STANDBY/SLEEP 的准备顺序为：清旧 RTC alarm、准备 IMU/TOF、通知 MCU ARM、按需 arm TCPKA、按需设置 RTC，然后在进入内核 suspend 前最后一次消费 MCU 已排队的 wake result。若此时已有有效唤醒，则清 RTC、disarm TCPKA、恢复传感器、同步 MCU RUNNING，并取消本次 suspend。

从 suspend 返回后，优先识别 SoC RTC 唤醒；否则等待 MCU 提供确认过的 wake source。随后清 RTC、disarm TCPKA、恢复传感器并同步 RUNNING。唤醒源不明确或恢复步骤失败时返回失败，不伪造成功来源。

DEEP_SLEEP 的顺序更严格：Sensor 先完成安全 deinit，TCPKA 配置和 arm 必须成功，然后才向 MCU 发送 DEEP_SLEEP ARMED。MCU 在 ACK 后可以立即切断 SoC 电源，因此 ARMED 之后不再依赖 SoC 执行清理。若 MCU ARM 失败，则 disarm TCPKA 并恢复 MCU RUNNING profile。

## 可靠性约束与取舍

- 采用轻量 transition owner：低功耗转换由 `SensorEntry` 和 `SocPowerService` 串行持有，不引入复杂的分布式事务框架。
- 保留 MCU PA8 9 ms 脉冲；通过转换末端消费已排队唤醒缩小 STANDBY/SLEEP 的 ARMED-to-suspend 窗口。
- 允许 DEEP_SLEEP 阶段偶发强制断电；协议把真正不可逆点对齐到 MCU 收到 ARMED 之后，SoC 重启时依赖 RUNNING 同步和残留 session 清理恢复。
- DNS 解析发生在 `arm()`，因此网络变化会在每次低功耗布防时重新获取地址；不把上次 IPv4 永久缓存为配置真相。
- 配置失败、DNS 失败、TCP 失败、WiFi 命令失败或清理失败均阻止进入需要该唤醒源的低功耗模式。

## 主要源码位置

- Proto 契约：`modules/proto/sensor_ctrl.proto`
- 上层命令解析与低功耗 transition owner：`modules/sensor/main/sensor_entry.cpp`
- TCPKA 生命周期与网络实现：`modules/sensor/hardware/tcpka.h`、`modules/sensor/hardware/tcpka.cpp`
- payload/服务器联调说明：`modules/sensor/docs/tcpka_keepalive_protocol.md`
- SoC 低功耗静态检查：`build/check_soc_low_power_flow.py`
- SoC reboot 静态检查：`build/check_soc_reboot_flow.py`

关联的 MCU 状态机与电源转换设计在 GD32L235 项目另有 `reviewing` 候选；本条目只对 PCR02 SoC 源码和协议实现负责，不用跨项目候选替代本项目板级证据。

## 已完成验证

2026-07-22 对当前工作区执行并通过：

```text
rtk make modules/proto_lib_all -j20 NC=1
rtk make modules/sensor_lib_all -j20 NC=1
rtk make modules/common_lib_all -j20 NC=1
rtk make modules/app_lib_all -j20 NC=1
rtk make modules/hdi_lib_all -j20 NC=1
rtk make modules/bridge_lib_all -j20 NC=1
rtk make pcr02_app_all -j20 NC=1
rtk python3 build/check_soc_low_power_flow.py
rtk python3 build/check_soc_reboot_flow.py
rtk git diff --check
rtk git -C modules/sensor diff --check
```

生成后的 Proto 访问器包含 `server_host` 和 `contract_version`；旧契约字段负向扫描无命中。最终 SoC 应用链接成功。

构建过程暴露两项操作性注意事项：

1. 修改共享接口后，若直接复用旧的 common/app/hdi 静态库，最终链接可能缺少新符号；应顺序重建相关库后再链接应用。
2. 不要在同一并行 make 中同时启动互相依赖的多个顶层归档目标，否则可能并发写同一静态库；本次最终证据来自顺序执行各顶层目标。

## 尚未完成的联合验证

下列项目仍是发布前门禁：

1. 测试服务器按 payload v1 收包、完整帧校验、SN 解析和 keepalive 唤醒。
2. 生产 DNS hostname 的解析、multi-A 回退、连接和服务器解析。
3. STANDBY 下 IMU、TOF 和可选 WiFi 唤醒；确认 SoC 已运行时不会重复触发无效唤醒。
4. SLEEP 下 RTC-only、TCPKA-only、RTC+TCPKA 三种组合及唤醒源回报。
5. DEEP_SLEEP 下 SoC 电源实际关闭、WiFi firmware 保活、MCU 收到 WiFi 事件后重新上电，以及 SoC 启动后的来源恢复。
6. DHCP 地址变化、DNS 无结果/多地址、服务器不可达、源端口占用、发送超时和清理重试。
7. Proto 负向用例：旧消息、未知 `contract_version`、revision 为 0、过期 revision、同 revision 不同内容、非法 SN。
8. STANDBY/SLEEP 在 MCU ARMED 到 SoC 真正进入 suspend 之间的边界压力测试；当前实现仅在最后一个 userspace 点消费已排队唤醒，不能据源码证明硬件级零窗口。

## 后续动作

1. 上层与 SoC 使用同一 Proto 版本同步部署；先下发 `contract_version=1` 和单调 revision，再进行低功耗测试。
2. 服务器先完成 payload v1 解析和可观测日志，再做测试网络及生产 DNS 联调。
3. 使用匹配当前源码的固件完成上述板级矩阵，保存去标识化的命令、结果和 BuildID 作为 validation 条目。
4. 只有 owner 复核正文、联合验证闭环并具备独立授权后，才评估从 `reviewing` 提升；不得自动写 memory 或改变 active 状态。

## Provenance 与脱敏说明

- `captured_at`：2026-07-22。
- 来源：当前 PCR02 SoC 工作区中的 Proto、SensorEntry、Tcpka 实现、协议文档，以及本轮定向构建/静态检查结果。
- 证据等级：源码实现加本地构建/静态检查；板级、服务器和生产网络证据缺失。
- 已脱敏：测试/生产端点、内网地址、真实产品 SN、本机绝对路径、raw log、二进制和凭证均未保留。
- memory candidate：否。本条目仅为 Knowledge Hub `reviewing` archive candidate，不做 memory 写入或 active promotion。
