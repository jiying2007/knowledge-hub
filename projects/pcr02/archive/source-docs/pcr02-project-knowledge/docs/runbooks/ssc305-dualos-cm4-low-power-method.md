---
title: SSC305 DualOS CM4 与低功耗方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, dualos, cm4, rtos, low-power, str]
related: [../standards/ssc305-feishu-knowledge-map.md, ../standards/sigmastar-platform-topic-catalog.md, sigmastar-platform-development-workflow.md, embedded-linux-performance-triage-guide.md]
validation_refs: [../archive/sigmastar/manifest.csv, ../standards/sigmastar-platform-topic-catalog.md]
---

# SSC305 DualOS CM4 与低功耗方法

## 1. 适用范围

本文用于 SSC305 的 DualOS、RTOS、CM4、快启、STR、低功耗和 PM 协同问题。

典型任务：

1. RTOS early init 或 IPL early init 移植。
2. 低功耗休眠、唤醒和功耗异常定位。
3. TTFF、TTUFF、TTCL 等快启耗时拆分。
4. CM4 侧外设、PM power、唤醒源调试。
5. Linux 与 RTOS/CM4 多进程和资源管理问题。

## 2. 资料主题入口

优先查以下 SSC305 主题：

| 方向 | 主题 ID |
| --- | --- |
| DualOS 架构 | `customer.DualOS.Development.arch_zh` |
| DualOS 客户开发 | `customer.DualOS.Development.dualos_customer_development_guide_zh` |
| DualOS 场景 | `customer.DualOS.Development.dualos_scene_guide_zh` |
| 多进程资源 | `customer.DualOS.Development.multiprocess_guide_zh` |
| RTOS early init | `customer.DualOS.Development.rtos_earlyinit_guide_zh` |
| IPL early init | `customer.DualOS.Development.ipl_earlyinit_guide_zh` |
| TTFF/TTUFF/TTCL | `customer.DualOS.Development.TTFF-TTUFF-TTCL_guide_zh` |
| STR 耗时 | `customer.Common.Development.STR_Time_consuming_Guide_zh` |
| CM4 PM | `platform.CM4.pm_power_zh` |
| CM4 API | `platform.CM4.cm4_api_zh` |

## 3. 分层职责

定位前先写清职责边界：

| 层级 | 职责 |
| --- | --- |
| Boot/IPL | 最早期硬件、启动链、唤醒路径 |
| RTOS | 快启、早期 sensor、轻量任务、实时路径 |
| CM4 | PM、电源域、低功耗外设、唤醒源 |
| Linux | 主业务、复杂媒体链路、网络、存储、日志 |
| App | 产品策略、状态机、诊断和回归 |

如果职责边界不清，后续调试容易出现重复初始化、资源抢占和状态不一致。

## 4. 快启耗时拆分

快启问题不要只看总耗时，应拆成：

```text
上电/唤醒
  -> Boot/IPL
  -> RTOS early init
  -> Sensor ready
  -> Linux kernel
  -> rootfs/init
  -> daemon/cmd_server/app
  -> 首帧/首个业务可用状态
```

每段记录：

| 字段 | 内容 |
| --- | --- |
| 阶段 | 例如 RTOS sensor ready |
| 起点 | 日志时间戳或 GPIO toggle |
| 终点 | 日志时间戳或帧计数 |
| 耗时 | ms |
| 责任层 | Boot/RTOS/CM4/Linux/App |
| 可优化动作 | 延后、并行、缓存、裁剪、配置调整 |

## 5. 低功耗定位

功耗异常按以下顺序检查：

1. 当前电源状态是否符合预期。
2. 唤醒源是否误触发。
3. CM4/PM power 状态是否正确。
4. Linux 侧是否有进程、线程、fd 或设备阻止休眠。
5. Sensor、IR、Wi-Fi、audio、storage 是否进入低功耗状态。
6. 日志、心跳、定时器是否过密。
7. 唤醒后资源是否重复初始化或未释放。

功耗结论必须包含：

```text
测试电源模式、板级连接、测量点、平均/峰值电流、唤醒源、软件版本、配置版本
```

## 6. CM4 外设问题定位

先判断外设归属：

1. 由 CM4 独占。
2. 由 Linux 独占。
3. Linux 与 CM4 共享，但有 mailbox、PM 或资源管理协议。

常见问题：

| 现象 | 检查点 |
| --- | --- |
| CM4 GPIO 无效 | padmux、方向、电源域、Linux 是否占用 |
| CM4 I2C 失败 | bus 归属、时钟、pull-up、设备地址 |
| CM4 RTC 异常 | 低功耗域供电、校准、唤醒配置 |
| CM4 PM 交互失败 | NonPM/PM 消息、状态机、唤醒源 |
| Linux 唤醒后异常 | 资源恢复顺序、重复初始化、状态同步 |

## 7. 多系统资源管理

必须明确：

1. 外设 owner。
2. 初始化 owner。
3. 运行期控制 owner。
4. 低功耗前保存状态的 owner。
5. 唤醒后恢复状态的 owner。
6. 失败回滚 owner。

禁止做法：

1. Linux 和 RTOS 同时初始化同一外设。
2. App 在不知道 CM4 状态的情况下强行切电。
3. 唤醒后只恢复 Linux 状态，不恢复 RTOS/CM4 状态。
4. 只用 sleep 延时掩盖状态同步问题。

## 8. 验证方式

最小验证：

1. 冷启动耗时。
2. 休眠进入耗时。
3. 唤醒耗时。
4. 唤醒后业务恢复。
5. 连续休眠/唤醒压力。
6. 异常断电或复位后的恢复。

输出建议：

```md
| 轮次 | 进入休眠 ms | 唤醒到系统 ready ms | 首帧 ms | 电流 | 结果 |
| --- | ---: | ---: | ---: | ---: | --- |
```

## 9. 收口标准

DualOS/CM4/低功耗问题完成时至少说明：

1. 问题发生在哪个系统层级。
2. owner 和资源归属是否明确。
3. 是否影响启动、快启、休眠、唤醒或业务恢复。
4. 关键日志和耗时数据。
5. 修复方案、配置变更和回归轮次。
