---
id: gd32l235-pcr02-power-transition-owner-tcpka-20260722
title: GD32L235 与 PCR02 SoC 电源状态、TCPKA 和关机事务协同归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-implementation-and-local-validation
  from: workspace://gd32l235 and workspace://pcr02-ssc305 source diffs plus local build/static-check evidence captured 2026-07-22
  source_sha256: 6a7ef05a71d8bbf8f92a44fc886db51d9a1782dbbacb0c7224c36d81eaeea0ce
  temporary_source_retained: false
review_after: '2026-08-22'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- power-transition
- tcpka
- wake-source
- shutdown-transaction
- hil-pending
validation_refs:
- projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/design/2026-07-22-soc-mcu-power-transition-owner-tcpka.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 归档 GD32L235 与 PCR02 SoC 的统一电源状态语义、轻量 transition owner、TCPKA 配置、0x09 关机事务、紧凑唤醒日志和双端软件验证；板级 HIL 仍待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 与 PCR02 SoC 电源状态、TCPKA 和关机事务协同归档

## 摘要

本记录归档 2026-07-22 在 GD32L235 MCU 与 PCR02 SoC 工作树完成的电源协同优化：统一 RUNNING、STANDBY、SLEEP、DEEP_SLEEP 语义；由 SoC 轻量 `PowerTransitionOwner` 串行化低功耗、reboot 与拨动开关关机；由 MCU 通过 PA15 独立控制 SoC 电源；将 WiFi KEEPALIVE 改为 SoC 上层通过 protobuf 下发 TCPKA 参数；将 `0x09` 定义为可重发、幂等、带业务确认的关机事务。

软件静态检查和两端构建已通过，但未执行板级 HIL。本记录是 `reviewing` 历史证据，不是 active 设计规范、发布签收或硬件验收结论。

## 背景与目标

原实现存在三类可靠性风险：

1. ToF 运行态以 15 Hz 输出 data-ready，MCU 会把每个边沿转换成 PA8 唤醒脉冲，并打印多条长日志。
2. SoC 的待机、休眠、深度休眠、reboot 和物理开关关机缺少统一 transition owner，存在多个流程并发或相互覆盖的可能。
3. 物理开关 OFF 时需要允许 SoC 偶发强制断电，同时尽量先完成应用层收口；DEEP_SLEEP 又要求 SoC 真正掉电而 MCU/WiFi 保持工作。

本轮目标是在不增加重型分布式状态机的前提下，建立单一状态语义、轻量 transition owner、可重发关机事务和可验证的唤醒源上报链路。

## 最终状态语义

| 状态 | SoC 状态 | 可用唤醒源 | MCU 行为 |
| --- | --- | --- | --- |
| `RUNNING` | SoC 正常运行；WiFi、IMU、ToF 工作 | 不需要外部唤醒 | IMU/ToF data-ready 仅作运行数据，丢弃唤醒动作，不输出 PA8 |
| `STANDBY` | SoC 应用待机 | MCU IMU、MCU ToF、MCU WiFi/TCPKA | MCU 记录来源，输出固定 9 ms PA8 脉冲，并通过可靠事件把唤醒源交给 SoC |
| `SLEEP` | SoC suspend；原 STR 命名统一为 SLEEP | SoC RTC 定时唤醒、MCU WiFi/TCPKA | IMU/ToF 不作为 SLEEP 唤醒源；WiFi 唤醒仍使用固定 9 ms PA8 |
| `DEEP_SLEEP` | SoC 完成安全收口后由 MCU 拉 PA15 断电 | 仅 MCU WiFi/TCPKA | MCU/WiFi 保持；WiFi 事件使 MCU 重新给 SoC 上电，属于冷启动式唤醒 |

SoC RTC 只用于 `SLEEP`，不用于 SoC 已掉电的 `DEEP_SLEEP`。

## 轻量 transition owner

SoC 进程新增原子 `PowerTransitionOwner`：`None`、`Standby`、`Sleep`、`DeepSleep`、`Reboot`、`SwitchOff`。

核心规则：

- STANDBY、SLEEP、DEEP_SLEEP 和 reboot 通过 compare-and-swap 获取 owner；失败即拒绝新转换。
- reboot 采用 reserve/commit/cancel 两阶段，避免“已声明 reboot”与“实际开始 reboot”之间失配。
- 非 deep 的低功耗返回运行态后释放 owner。
- 物理开关 `SwitchOff` 是唯一允许抢占软件低功耗或 reboot 的流程，因为最终硬件事实必须收敛为 SoC 掉电。
- owner 只串行化 transition，不复制所有模块状态，避免形成第二套复杂状态机。

主要实现位置：

- `workspace://pcr02-ssc305/pcr02/main.cpp`
- `workspace://pcr02-ssc305/modules/sensor/power/soc_power_service.cpp`
- `workspace://pcr02-ssc305/include/modules/sensor/sensor_module.h`

## `0x09` 物理开关关机事务

`0x09` 不保留旧兼容语义，采用双向、无帧 ACK、业务阶段确认的负载：`stage + reason + detail`。

MCU 发送阶段：

- `COMMAND_SENT`：已收到 PA11 OFF，并请求 SoC 收口。
- `TIMEOUT_FORCE_OFF`：6 秒未确认，准备强制断电。
- `CANCELLED`：在可取消窗口内拨回 ON。

SoC 发送阶段：

- `SOC_CONFIRMED`：SoC 已跨过关机 point-of-no-return，MCU 可继续执行断电。

可靠性策略：

- MCU 在等待确认期间每约 400 ms 重发完全相同的 `COMMAND_SENT`，总超时仍为 6 秒。
- SoC 对相同 reason/detail 的重复请求幂等处理。
- STANDBY/SLEEP 下，PA11 OFF 先关闭模块 EXTI、保持 UART 接收、输出一次固定 9 ms PA8，使 SoC 有机会退出浅睡，然后进入 `0x09` 事务。
- RUNNING 下不额外输出 PA8，直接发送关机事务。
- DEEP_SLEEP 下 SoC 已掉电，PA11 OFF 不重新上电；MCU 直接保持或收敛为 SoC 断电状态。
- 允许 6 秒后偶发强制断电，使软件行为与物理拨动开关的最终硬件语义一致。

主要实现与规范位置：

- `workspace://gd32l235/App/bsp.c`
- `workspace://gd32l235/App/wakeup.c`
- `workspace://gd32l235/Docs/串口通信协议规范.md`

## WiFi TCPKA 配置和唤醒

WiFi KEEPALIVE 由 SoC `tcpka.cpp` 实现。上层通过 protobuf `KeepAlivePayload` 下发：

- `enable`
- `server_ip`
- `server_port`
- `uid`
- `device_ip`
- `revision`

`revision` 必须非零。完全相同 revision 和参数视为幂等；配置变化时先 deinit 再 init。禁用请求执行 deinit。enable=true 但参数不完整时拒绝命令。

所有低功耗模式在接受前要求 TCPKA 已初始化，避免进入只声明 WiFi 可唤醒、实际未建立保活配置的状态。

主要实现位置：

- `workspace://pcr02-ssc305/modules/proto/sensor_ctrl.proto`
- `workspace://pcr02-ssc305/modules/sensor/hardware/tcpka.cpp`
- `workspace://pcr02-ssc305/modules/sensor/main/sensor_entry.cpp`

行为兼容边界：protobuf 字段是追加字段，wire 编码兼容；但 enable=true 缺少 endpoint、UID、device IP 或 revision 的旧调用会被拒绝，属于有意的行为收紧。

## 唤醒源和日志策略

MCU 的运行态模块边沿不再制造 PA8：

```text
WAKE_DROP t=... src=tof reason=soc_running count=...
```

真正触发唤醒时只保留紧凑事件：

```text
WAKE_FIRE t=... src=tof soc_state=... policy=...
SOC_WAKE t=... count=... duration=...
```

PA8 脉冲继续保持 9 ms。SoC 唤醒后通过现有可靠事件链获知 IMU、ToF、WiFi 或 switch 等来源；DEEP_SLEEP 是冷启动路径，来源必须由 MCU 在 SoC 重新上电后补报。

为避免 MCU debug 固件 flash 溢出和串口占用，详细 `CHG_CUR`、`CHG_SNAP` 等充电诊断分别由 `CHARGE_DIAG_LOG_ENABLED` 和 `BSP_CHARGE_DIAG_LOG_ENABLED` 控制，二者默认均为 `0`，且不与 `GD32L235_CHARGE_CERT_PROFILE` 关联；启用 charge-cert profile 不会隐式打开这些详细日志。紧凑唤醒日志按独立门控保留。

## 未扩展的复杂度边界

STANDBY/SLEEP 的 `ARMED` 到 SoC 真正进入 suspend 之间仍有理论丢唤醒窗口。本轮没有增加第三阶段硬件握手，理由是：

- MCU 已可靠排队唤醒结果；
- SoC 在 suspend 前已有最后一次 userspace 事件消费；
- PA8 保持固定 9 ms；
- 继续增加握手会扩大 MCU/SoC 双边状态和恢复分支。

这不是“已证明可忽略”，而是有意保留的板级验证项。若 HIL 观察到真实丢唤醒，再增加最小必要的 suspend-entry 门控或电平保持，不预先引入重型协议。

## 软件验证证据

### MCU

以下静态检查通过：

```text
rtk python3 Tools/tests/check_wakeup_diagnostics.py
rtk python3 Tools/tests/check_application_soc_offline_fast_shutdown.py
rtk python3 Tools/tests/check_application_soc_exit_commit.py
rtk python3 Tools/tests/check_boot_reset_diagnostics.py
rtk python3 Tools/tests/check_application_debug_uart.py
rtk python3 Tools/tests/check_charge_cert_build_guard.py
rtk git diff --check
```

构建与容量结果：

- debug UART 构建通过：App FLASH 49,028 / 51,200 bytes，RAM 14,424 / 24,576 bytes。
- production 构建通过：App FLASH 45,392 / 51,200 bytes，剩余 5,808 bytes，满足 4 KiB OTA reserve；RAM 14,384 / 24,576 bytes。
- 两个 build-dir 的 `fwtool.py check --scope build` 均通过。

负向证据也保留：详细充电日志未门控时 debug 构建曾超出 FLASH 492 bytes；只门控部分日志后仅余 420 bytes。将两组详细充电日志统一限制到 charge-cert profile 后得到上述最终容量。

### SoC

以下生成、构建和静态检查通过：

```text
rtk bash modules/proto/build_proto.sh
rtk make modules/proto_obj_all -j20
rtk make modules/sensor_obj_all -j20
rtk make modules/proto_lib_all modules/sensor_lib_all pcr02_app_all -j20 NC=1
rtk python3 build/check_soc_low_power_flow.py
rtk python3 build/check_soc_reboot_flow.py
rtk git diff --check -- <本轮目标文件>
```

首次 `pcr02_app_all` 曾因增量构建仍链接旧 `libsensor` 而出现新 callback API undefined reference；显式重建 proto/sensor 库后应用构建通过。这是构建依赖刷新证据，不是运行时缺陷。

## 板级 HIL 待验证

以下项目尚未验证，不能从软件门禁推导为硬件已通过：

1. PA11 OFF 从 STANDBY/SLEEP 触发一次 9 ms PA8，随后 `0x09` 约 400 ms 重发，并在确认或 6 秒超时后断电。
2. DEEP_SLEEP 中 PA15 确实切断 SoC 电源，同时 MCU/WiFi 保持；此时 PA11 OFF 不会反向给 SoC 上电。
3. WiFi TCPKA、IMU、ToF、SoC RTC 分别产生正确的唤醒动作与来源上报。
4. reboot 全流程不拉 PA15，不误进入物理断电路径。
5. 快速 OFF→ON：确认前能够取消；确认后完成至少 100 ms 的 SoC 断电窗口。
6. STANDBY/SLEEP `ARMED` 到真实 suspend 窗口在压力和边沿时序下无可复现丢唤醒。

## 来源、时间与适用边界

- captured_at：2026-07-22（Asia/Hong_Kong）
- last_verified：2026-07-22
- MCU source：`workspace://gd32l235` 的未提交工作树实现与本地命令证据
- SoC source：`workspace://pcr02-ssc305` 的未提交工作树实现与本地命令证据
- provenance：本记录由 Codex 根据用户确认的目标、两端源码差异、生成物、静态检查和构建输出整理
- 非来源：未复制原始串口日志、私有 TCP endpoint、UID、token、凭证或二进制制品
- Git 边界：两个工作树均存在用户已有改动；本记录不对应一个已提交 commit，也不声明可合并或可发布

## 后续动作

1. 按“板级 HIL 待验证”逐项形成同一时间基准的串口和 GPIO/电源波形证据。
2. HIL 通过后更新本条目的 `evidence_validation_status`；在 owner 复核前保持 `reviewing`。
3. 只有观察到真实 ARMED/suspend 丢唤醒，才引入最小附加握手；不得仅为理论完备性扩大协议。
