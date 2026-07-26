---
id: pcr02-imu-tof-driver-runtime-reference-20260721
title: PCR02 IMU/TOF 驱动规格与运行时设计参考
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-21-pcr02-imu-tof-driver-runtime-reference.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-and-vendor-documentation-summary
  from: current production source, previously verified vendor datasheets/reference packages, and historical commit; binary
    attachments deliberately not retained
  source_sha256: c34cab086e765f6bd1cc807c8b1a860ab93d55d123f4353593c08f606eba22d6
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- imu
- tof
- qmi8658b
- vl53l8cx
- low-power-wakeup
- sensor-lifecycle
- scheduling
- timestamp
- no-binary-dependency
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-21-pcr02-imu-tof-driver-runtime-reference.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-21-pcr02-imu-tof-driver-runtime-reference.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-21'
updated_at: '2026-07-21'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-21'
manual_validation_pending: true
summary_zh: 固化 PCR02 QMI8658B IMU 与 VL53L8CX TOF 的当前运行/低功耗配置、状态机、返回码、时间戳、热路径和双核调度约束，使原厂 PDF/ZIP 删除后仍可直接维护；未完成的板级验证保留为显式门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 IMU/TOF 驱动规格与运行时设计参考

## 目的与使用规则

本文固化 PCR02 当前 QMI8658B IMU 与 VL53L8CX TOF 的已核实规格、驱动配置、生命周期、接口语义、调度策略和验证边界。原厂 PDF、ZIP 后续可以从源码仓删除；日常开发、评审和排障应先查本文与当前源码，不再把原始附件作为必需输入。

回退到原厂资料的条件仅限：本文未覆盖的寄存器位、器件版本差异、模拟/电气指标、安全边界，或板测结果与本文冲突。若重新取得原厂资料并发现差异，应先更新本文的事实和证据等级，再修改实现。

本文不保存 PDF/ZIP、本地绝对路径、raw log、完整会话、客户资料、设备地址或二进制；附件名称只作为来源追溯信息。

## 系统契约

- 平台：PCR02，SigmaStar SSC305，双核 Cortex-A32；高负载下调度余量有限。
- IMU 运行态：硬件 ODR 250Hz，业务发布目标 100Hz。
- TOF 运行态：8x8、单目标、continuous 15Hz；允许丢帧，采用新鲜帧语义，不补发旧帧。
- SOC 休眠时，IMU 与 TOF 保留供电；两路 I2C 均在 SOC，MCU 只读取传感器 INT 电平/中断，不访问传感器 I2C。
- IMU 低功耗唤醒只负责检测拨动、翻转等动作并唤醒 SOC，不在 MCU 侧判断“拿起”。SOC 唤醒后再结合 IMU 行为选择交互策略。
- TOF 低功耗唤醒在目标距离窗口内检测到物体后输出 INT，MCU 据此唤醒 SOC。
- 发布消息中的 IMU 与 TOF 时间戳统一为 Unix 微秒，取传感器读取开始前的近似采样时刻；不使用序列化或发布完成时间。该方案不是器件硬件时间戳，长时间调度停顿时仍存在近似误差。

## QMI8658B IMU

### 运行态配置

当前实现由 `qmi8658_config_reg(0)` 配置：

| 项目 | 当前值 | 说明 |
| --- | --- | --- |
| Accelerometer range | +/-8g | `Qmi8658AccRange_8g` |
| Gyroscope range | +/-1024 dps | `Qmi8658GyrRange_1024dps` |
| Accelerometer ODR | 250Hz | 为 100Hz 发布保留采样裕量 |
| Gyroscope ODR | 250Hz | 与 accelerometer 同步 |
| Accelerometer LPF | enable, mode 3 | CTRL5 的 accelerometer LPF enable 与 mode bits |
| Gyroscope LPF | enable, mode 3 | CTRL5 的 gyroscope LPF enable 与 mode bits |
| SyncSample | enable | CTRL7 bit7；运行态读取同步 accel/gyro 数据 |
| Sensors | ACC + GYR | CTRL7 同时使能 accel 与 gyro |
| Any-Motion | disable | 运行态 CTRL8 Any-Motion 位必须为 0 |

对应预期关键寄存器值：

- CTRL2：`0x25`，即 +/-8g 与 250Hz。
- CTRL3：`0x65`，即 +/-1024 dps 与 250Hz。
- CTRL5：`0x77`，即 accel/gyro LPF 均开启并选择 mode 3。
- CTRL7：必须同时包含 SyncSample、ACC enable、GYR enable；不要只按固定常量判断其他保留位。
- CTRL8：Any-Motion enable 位必须清零。

原厂规格核对结论：QMI8658B 的 LPF mode 3 带宽约为 ODR 的 13.37%；250Hz ODR 下约 33.4Hz，低于 100Hz 发布链路的 50Hz Nyquist 频率，可抑制混叠，同时比 125Hz ODR 留出更充足的数据就绪裕量。

### Active、Suspend、Resume 状态机

`_Qmi8658EnterActiveMode()` 是 init/resume 进入运行态的统一入口：

1. 先清 CTRL8 Any-Motion enable，避免初始化或恢复过程中留下低概率运行态中断窗口。
2. 开启 SyncSample。
3. 配置 250Hz、量程和 LPF。
4. 使能 ACC+GYR，读取状态清理旧事件。
5. 回读 CTRL7/CTRL8；SyncSample、ACC、GYR 或 Any-Motion 状态不符合预期时返回失败。

Suspend 的当前契约：

- 关闭 SyncSample。
- ACC 使用 low-power 128Hz、+/-8g；GYR 关闭。
- Any-Motion 开启并映射到 INT1。
- 回读确认 CTRL7 中 ACC 开、GYR 关、SyncSample 关，并确认 CTRL8 Any-Motion 已开启。
- MCU 收到 INT 后只唤醒 SOC；动作分类由 SOC 恢复后完成。

Resume 直接调用 `_Qmi8658EnterActiveMode()`，不得先在运行态临时开启 AMD。当前生产路径中不应出现 `qmi8658_enable_amd(1, qmi8658_Int1, 0)`；AMD 只在 suspend/低功耗唤醒路径使用 `low_power=1`。

历史依据：旧源码仓提交 `3576f9cb7f75f2d62ee8fbb557446e202ca315d3`（2026-03-09，`fix: update imu`）处理过“运行态 AMD 未完全关闭导致低概率中断”。旧提交只作为历史动机，当前事实以本仓 `_Qmi8658EnterActiveMode()` 和 suspend/resume 实现为准。

### 数据与接口语义

- `IMU_UPDATE_SUCCESS = VS_SUCCESS`，保证旧调用方用 `VS_SUCCESS == ret` 判断时兼容。
- 后续状态依次表达 `NOT_READY`、`IO_ERROR`、`THROTTLED`、`INVALID_STATE`；调用方不得把非零状态当成功。
- 只有 fresh read 成功时，HDI 才把 accel/gyro 数据复制给调用方并更新时间戳；失败或未就绪不得发布上一帧。
- I2C 连续失败触发有界退避，避免双核高负载或总线异常时形成无意义重试风暴。
- init 开始时先将 `g_stImuContext.pstDeviceOps = NULL`；任何打开 I2C、芯片 init 或 active-mode 校验失败都必须完整回滚 I2C、handle、state 和 ops 指针，避免后续接口误判为已初始化。
- deinit/release 的产品语义不是给传感器断电：先进入 suspend 低功耗唤醒态，再释放 SOC 侧 I2C 资源；传感器仍由保活电源工作。

### FIFO 决策

当前 `QMI8658_USE_FIFO` 关闭。现有原厂参考 FIFO 代码不能直接作为生产实现，主要缺口包括：

- 没有适配现有单样本 HDI 接口的批量返回契约。
- 每个 FIFO 样本没有可靠的硬件时间戳或按 ODR 重建的时间戳。
- 溢出、截断、I2C 错误和恢复策略不完整。
- 示例处理含调试输出和全局状态，不满足热路径与并发约束。

默认继续使用 250Hz ODR 加 100Hz fresh-sample 读取。如果匹配 BuildID 的最重负载板测仍证明因 20ms 以上调度停顿丢失关键物理样本，再单独设计 watermark 2-4 的 stream FIFO：采集层批量读取，按 250Hz 重建每个样本时刻；实时运控取批次最新样本，需要积分的消费者才处理完整批次。FIFO 用于样本连续性和批量 I2C，不用于快速补发历史数据，也不能替代系统减载。

## VL53L8CX TOF

### 运行态配置

| 项目 | 当前值 | 说明 |
| --- | --- | --- |
| Resolution | 8x8 | 64 zones |
| Targets per zone | 1 | 当前业务只取单目标 |
| Mode | continuous | 运行态连续测距 |
| Ranging frequency | 15Hz | `VL53L8CX_ACTIVE_RANGING_FREQUENCY_HZ` |
| Enabled result fields | distance_mm, target_status | 其他输出在 `platform.h` 中关闭 |

更新流程先调用 `vl53l8cx_check_data_ready()`。只有 data-ready 且 `vl53l8cx_get_ranging_data()` 成功才返回 fresh frame；未就绪返回 `TOF_UPDATE_NOT_READY`，I/O 失败返回 `TOF_UPDATE_IO_ERROR`。TOF 允许丢帧，因此上层应 latest-only，不积压、不补发，也不把旧缓存重新标为成功。

### 低功耗唤醒配置

Suspend 时先停止 continuous ranging，再配置：

- autonomous mode；
- 3Hz ranging frequency；
- 5ms integration time；
- 8x8 的 64 个 zone 全部配置 distance `IN_WINDOW`；
- 距离窗口 100-1000mm；
- zone 条件使用 OR，任一区域满足即可触发；
- detection threshold enable；
- threshold auto-stop enable，触发后停止并保持中断语义。

随后重新 start ranging。Resume 时 stop ranging，关闭 detection thresholds 与 auto-stop，恢复 15Hz continuous 并重新 start。

该配置表达“1 米内出现符合距离条件的目标”，不是完整的多帧移动轨迹算法；环境串扰、反射率、遮挡和目标状态仍需板测。若产品严格要求“距离变化/移动”而不是“目标进入窗口”，需要在器件 threshold 能力之上增加明确状态机并重新验证功耗和误唤醒率。

### 数据、内存与接口语义

- `TOF_UPDATE_SUCCESS = VS_SUCCESS`，兼容其他接口的统一成功判断。
- 后续状态表达 `NOT_READY`、`IO_ERROR`、`INVALID_DATA`、`INVALID_STATE`；只有新鲜且目标状态有效的数据可以发布。
- init 开始时先将 `g_stTofContext.pstDeviceOps = NULL`；失败时释放 configuration、清空 handle、关闭 I2C、恢复 NOT_INIT 并保持 ops 为空。
- configuration 在 init 时分配一次，release 时释放一次；这不是 15Hz 更新热路径分配。
- `VL53L8CX_Platform` 内含固定 1026-byte I2C transfer buffer，可容纳 2-byte register address 加最多 1024-byte payload。
- platform read/write 对长度做上界检查，热路径不再 malloc/free；共享 `VSHDII2C_WriteRead` 使用栈上 `i2c_msg`，也不做动态分配。
- deinit/release 与 IMU 一样，应先进入 autonomous wake 状态，再释放 SOC 侧 I2C 资源，传感器保留供电并通过 INT 唤醒 MCU。

## 周期调度与双核压力边界

- 业务目标：IMU 100Hz，TOF 15Hz。
- 周期线程使用 `steady_clock` 绝对 deadline 与 condition variable 等待；超期后跳过过期槽，不做追赶式连跑，避免 CPU 紧张时形成补跑风暴。
- `SENSOR_TIMING_STATS_ENABLE` 生产默认值为 0。`acquire_start`、serialize/publish 耗时和周期统计仅在宏开启时编译，诊断包可显式打开。
- 采样消息时间戳与调试耗时计时分离：业务时间戳用 Unix 微秒；周期与耗时测量用单调时钟。
- TOF 是可丢帧通道，优先 latest-only；IMU 是运控关键通道，应优先保证采集并把 serialize/publish 从采集热路径拆出。是否拆线程、使用 SPSC ring 或提升最低档实时优先级，必须结合匹配 BuildID 的板测，不应把包含 protobuf/ZMQ 的整条 worker 直接提升为高优先级 RT。
- 现场高负载分析表明，双核接近满载、RTC/3A 高优先级线程和 IRQ 集中可能导致几十毫秒 wall-time 尾延迟。详细证据见关联条目 `pcr02-imu-tof-high-load-scheduling-triage-20260721`。

## 已完成验证

当前源码改动阶段已取得以下证据：

- `rtk make modules/hdi_obj_all -j20 NC=1`：通过。
- `rtk git -C modules/hdi diff --check`：通过。
- 负向扫描：运行态生产路径不存在 `qmi8658_enable_amd(1, qmi8658_Int1, 0)`。
- 负向扫描：TOF platform/shared I2C 更新热路径不存在 malloc/free。
- 源码回读：IMU active-mode 与 suspend-mode 均包含 CTRL7/CTRL8 状态验证；TOF suspend/resume 均包含 stop、配置、start 的完整转换。

## 板级验证清单

以下项目尚未因源码构建通过而自动成立，必须在匹配当前源码 BuildID 的板端完成：

1. 冷启动、init 失败注入、重复 start/stop、suspend/resume/deinit 的状态机和资源回滚。
2. IMU active 寄存器回读：CTRL2 `0x25`、CTRL3 `0x65`、CTRL5 `0x77`，CTRL7/CTRL8 位满足运行态约束。
3. IMU suspend 中 ACC-only、128Hz low power、GYR off、SyncSample off、Any-Motion INT1；运行态静置与运动时均不得出现 AMD 低概率中断。
4. TOF autonomous 3Hz、5ms、100-1000mm、64-zone OR、auto-stop 的 INT 极性、保持/清除行为和重复唤醒。
5. 目标进入、离开、静止、反射率变化、遮挡和边界距离下的误唤醒率；确认产品所说“移动变化”是否可由当前 in-window 语义满足。
6. 轻载和 RTC/视频/显示/音频并发最重负载下，持续统计 IMU fresh publish 100Hz、TOF fresh publish 15Hz、deadline miss、I/O error、数据年龄和最坏尾延迟。
7. SOC 休眠后确认 MCU 不访问 I2C，仅由 INT 唤醒；SOC 恢复后先恢复 I2C 控制权，再切 active mode。

## 来源索引与删除边界

当前事实以以下源码为准：

- `modules/hdi/src/hdi_drv/hdi_imu/hdi_imu.c`
- `modules/hdi/src/hdi_drv/hdi_imu/qmi8658/qmi8658.c`
- `modules/hdi/src/hdi_drv/hdi_imu/qmi8658/qmi8658.h`
- `modules/hdi/include/hdi_imu.h`
- `modules/hdi/src/hdi_drv/hdi_tof/hdi_tof.c`
- `modules/hdi/src/hdi_drv/hdi_tof/vl53l8x/platform.c`
- `modules/hdi/src/hdi_drv/hdi_tof/vl53l8x/platform.h`
- `modules/hdi/src/hdi_drv/hdi_tof/vl53l8x/vl53l8cx_api.c`
- `modules/hdi/include/hdi_tof.h`
- `modules/sensor/common/sensordev_base.cpp`
- `modules/sensor/imu/imu.cpp`
- `modules/sensor/tof/tof.cpp`

曾用于规格核对、允许后续删除且不复制到 Knowledge Hub 的附件：

- `QMI8658B Datasheet Rev B.pdf`
- `QMI8658_QMI8A01_MCU driver V2.0` ZIP
- `qmi8658_qmi8a01 V1.7` ZIP/参考目录
- `vl53l8cx.pdf`
- `VL53L8` ZIP/参考目录

删除附件前应保留本归档、当前生产源码以及构建/板测证据。若未来更换器件 revision、升级 ULD 或改变 ODR、LPF、threshold、输出字段，应把本文视为待更新的基线，而不是永远正确的规格替代品。

## 归档边界

- 这是 AI 汇总的 reviewing 候选，不是 owner 已批准的 active 标准。
- 源码与本文冲突时，以已审查的当前源码和可复现板测为事实，并及时更新本文。
- 本文没有写入 Codex memory，也没有复制原始 PDF/ZIP 或现场日志。
- 本次归档不授权删除源仓附件、提交、推送、发布或关闭人工验证门禁。
