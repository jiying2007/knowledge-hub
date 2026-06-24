# app_product_test 技术设计

## 1. 设计目标

- 用同一产测进程覆盖 `PCBA`、`SEMI_FINISHED`、`AGING`、`CALIBRATION`、`ACOUSTIC` 阶段。
- 将配置、阶段切换、消息路由和生命周期编排集中在 `pt_common.c`，具体硬件测试留在 `pt_hw_*.c`。
- 将手动录像控制与 2 小时老化计时拆分，避免 `pt_hw_record.c` 同时承担录像和老化状态职责。
- 老化阶段要求“连续 2 小时无异常”才放行复位键进入标定，并把通过态和异常态可观测地持久化。
- 标定阶段聚合 TOF、IMU、摄像头外参流程，完成后执行 TF 清理和重启收尾。

## 2. 顶层启动流程

`pt_main.c` 是进程入口：

1. 初始化 `VSHDIOS`。
2. 启动 `ProductTestDiag` diag command node。
3. 初始化 ringframe、tick、msg、event、video、audio、wifi、uart。
4. 关闭 AI 算法、开启 stereo。
5. 调用 `VSPT_CommonStart()`。
6. 主循环等待 `SIGINT/SIGTERM`。
7. 退出时调用 `VSPT_CommonStop()` 并反初始化各 API。

`pt_common.c` 负责：

- 从 `/var/run/media/mmcblk0p1/vstrong/product_test.ini` 加载配置。
- 解析 `Stage/Station/Operator/StrictIsolation`。
- 按 `PROFILE_<Stage>_<Station>` 装载 feature mask。
- 订阅上位机控制 topic，并发布 `bridge/pcba/*` 状态。
- 启停各 `VSPT_*Test` 模块。
- 处理老化复位门禁和标定完成收尾。

## 3. 阶段与 profile

| Stage | 解析结果 | 绑定类型 | 说明 |
| --- | --- | --- | --- |
| `PCBA` | `PT_STAGE_PCBA` | `PCBA` | 基础硬件测试，接受上位机控制 |
| `SEMI_FINISHED` | `PT_STAGE_SEMI_FINISHED` | `SEMI_FINISHED` | 半成品测试，可允许部分标定类型 |
| `AGING` | `PT_STAGE_AGING` | 无普通控制绑定 | 连续老化，隔离控制命令，保留状态类交互 |
| `CALIBRATE` / `CALIBRATION` | `PT_STAGE_CALIBRATION` | `CALIBRATION` | 标定流程 |
| `ACOUSTIC` | `PT_STAGE_ACOUSTIC` | 无专用绑定类型 | 声学专项 |

当前主线 feature mask：

| INI 开关 | bit | 启动模块 |
| --- | --- | --- |
| `EnableAdc` | `PT_FEATURE_ADC` | `VSPT_AdcTest` |
| `EnableAvRtsp` | `PT_FEATURE_AV_RTSP` | `VSPT_AvRtspTest` |
| `EnableBattery` | `PT_FEATURE_BATTERY` | `VSPT_BatteryTest` |
| `EnableFactory` | `PT_FEATURE_FACTORY` | `VSPT_FactoryTest` |
| `EnableImu` | `PT_FEATURE_IMU` | `VSPT_ImuTest`，`CALIBRATION` 阶段跳过通用 IMU 测试 |
| `EnableIrLight` | `PT_FEATURE_IR_LIGHT` | `VSPT_IrTest` |
| `EnableIrCut` | `PT_FEATURE_IR_CUT` | `VSPT_IrCutTest` 或 AGING 自动模式 |
| `EnableIrRecv` | `PT_FEATURE_IR_RECV` | `VSPT_IrRecvTest` |
| `EnableIrDistance` | `PT_FEATURE_IR_DISTANCE` | `VSPT_IrDistanceTest` |
| `EnableLaser` | `PT_FEATURE_LASER` | `VSPT_LaserTest` |
| `EnableLcd` | `PT_FEATURE_LCD` | `VSPT_LcdTest` |
| `EnableMic` | `PT_FEATURE_MIC` | `VSPT_MicTest` |
| `EnableMotor` | `PT_FEATURE_MOTOR` | `VSPT_MotorTest` 或 AGING 自动模式 |
| `EnableShutdown` | `PT_FEATURE_SHUTDOWN` | `VSPT_ShutdownTest` |
| `EnableSpeaker` | `PT_FEATURE_SPEAKER` | `VSPT_SpkTest` |
| `EnableTof` | `PT_FEATURE_TOF` | `VSPT_TofTest`，`CALIBRATION` 阶段跳过通用 TOF 测试 |
| `EnableRecord` | `PT_FEATURE_RECORD` | AGING 阶段启动 `VSPT_RecordTest` |

蓝牙扫描相关代码当前未进入主线 feature mask。`pt_bt.patch` 与 `pt_hw_bt.backup` 是待合入材料，不应作为当前可用能力描述。

## 4. PCBA 与半成品流程

### 4.1 共同行为

PCBA 和半成品阶段都按 `PROFILE_<Stage>_<Station>` 启动 profile 中启用的硬件测试，并允许上位机绑定后执行组件控制。

共用启动行为：

- `EnableAdc=1`：启动 `VSPT_AdcTest(VS_TRUE)`。
- `EnableAvRtsp=1`：启动 `VSPT_AvRtspTest(VS_TRUE)`。
- `EnableBattery=1`：启动 `VSPT_BatteryTest(VS_TRUE)`。
- `EnableFactory=1`：启动 `VSPT_FactoryTest(VS_TRUE)`。
- `EnableImu=1`：启动 `VSPT_ImuTest(VS_TRUE)`。
- `EnableIrLight=1`：IR 仲裁先进入全关，再由控制请求打开。
- `EnableIrCut=1`：启动 `VSPT_IrCutTest(VS_FALSE)`，等待手动控制。
- `EnableIrRecv=1`：启动 `VSPT_IrRecvTest(VS_TRUE)`。
- `EnableIrDistance=1`：启动 `VSPT_IrDistanceTest(VS_TRUE)`。
- `EnableLaser=1`：启动 `VSPT_LaserTest(VS_TRUE)`。
- `EnableLcd=1`：启动 `VSPT_LcdTest(VS_TRUE)`。
- `EnableMic=1`：启动 `VSPT_MicTest(VS_TRUE)`。
- `EnableMotor=1`：启动 `VSPT_MotorTest(VS_FALSE, 0, 0)`，等待上位机控制。
- `EnableShutdown=1`：启动 `VSPT_ShutdownTest(VS_TRUE)`。
- `EnableSpeaker=1`：非 AGING 阶段默认不循环播放，等待上位机控制。
- `EnableTof=1`：启动 `VSPT_TofTest(VS_TRUE)`。
- `EnableRecord=0`：PCBA/半成品不会启动 AGING 录像。

### 4.2 上位机绑定

绑定条件：

| Stage | bind type | id |
| --- | --- | --- |
| `PCBA` | `PCBA` | 必须等于 `Operator` |
| `SEMI_FINISHED` | `SEMI_FINISHED` | 必须等于 `Operator` |

绑定成功后，设备周期发布版本和测试项状态。WiFi 扫描与状态发布只在非 `CALIBRATION`、非 `AGING` 阶段执行，因此 PCBA/半成品会发布连接态、2.4G 扫描和 5G 扫描结果。

### 4.3 组件控制边界

PCBA/半成品可按 profile 控制：

| 组件 | 依赖 profile | 行为 |
| --- | --- | --- |
| `IR_CUT` | `EnableIrCut=1` | 调用 `VSPT_IrCutTest` |
| `SPEAKER` | `EnableSpeaker=1` | 调用 `VSPT_SpkTest` |
| `LCD` | `EnableLcd=1` | 调用 `VSPT_LcdTest` |
| `LASER` | `EnableLaser=1` | 调用 `VSPT_LaserTest` |
| `IR_LIGHT` | `EnableIrLight=1` | 调用 `VSPT_IrTest` |
| `WHEELS` | `EnableMotor=1` | 调用 `VSPT_MotorTest` |
| `LOG_LEVEL` | 无 feature 依赖 | 当前直接返回成功 |

`QR_CODE_SN` 只允许在 `CALIBRATION` 阶段写入；PCBA/半成品阶段会拒绝。

### 4.4 半成品特有边界

`_PT_IsCalibrateTypeAllowedInStage()` 当前允许 `WHEELS` 标定在 `SEMI_FINISHED` 或 `CALIBRATION` 阶段执行。其它标定类型必须在 `CALIBRATION` 阶段执行。

## 5. 老化模块

### 5.1 模块边界

`pt_hw_record.c`：

- API：`VSPT_RecordTest(VS_BOOL bOnOff)`、`VSPT_RecordTestState(VS_VOID)`。
- 只负责手动录像启停流程：`RecordInit/Mount/Start/Stop/Unmount/DeInit`。
- 不承担 2 小时计时、LCD 文案和老化状态持久化。

`pt_hw_aging.c`：

- API：`VSPT_AgingTimerTest`、`VSPT_AgingTimerCompleted`、`VSPT_AgingTimerReachedTarget`、`VSPT_AgingResetGateReady`、`VSPT_AgingFailSet`、`VSPT_AgingFailClear`、`VSPT_AgingFailBitmapGet`、`VSPT_AgingStateClear`。
- 用 `VSHDIOS_TaskStartMonitor` 执行周期 tick。
- 读取 `[AGING_CTRL] DurationMs`，默认 2 小时。
- 维护 `fail_bitmap`、`qualified_latch` 和 LCD 状态文案。
- 周期检查 TF 挂载/可写性，存储恢复后尝试恢复录像链路。

### 5.2 持久化

状态文件：

```text
/var/run/media/mmcblk0p1/vstrong/aging_state.ini
```

字段：

- `state_version`
- `stage`
- `session_id`
- `continuous_elapsed_ms`
- `fail_bitmap`
- `qualified_latch`
- `qualified_time`
- `last_update_time`

写入策略为临时文件加 `rename` 原子替换。持久化失败会累计失败计数，首次和周期性失败输出日志，恢复后输出恢复日志。

### 5.3 门禁状态机

| 状态 | 条件 | 行为 |
| --- | --- | --- |
| `RUNNING` | `qualified_latch=0` | 继续计时；未达标重启清零，防止跨重启拼接时长 |
| `QUALIFIED` | `elapsed >= DurationMs && fail_bitmap == 0` | 写入 `qualified_latch=1`，允许跨重启保留通过态 |
| `INVALIDATED` | 已通过后出现任意失败位 | 清除 `qualified_latch`，重新收紧门禁 |

复位键放行条件：

```text
Stage=AGING && VSPT_AgingResetGateReady() == VS_TRUE && fail_bitmap == 0
```

放行后 `VSPT_CommonHandleResetGate()` 将 `product_test.ini:[INFO] Stage` 持久化为 `CALIBRATION`，清理老化状态，并由 monitor task 触发重载切换。

`fail_bitmap` 是 sticky 状态，不因暂时恢复自动清零。当前主线定义了 `PT_AGING_FAIL_ITEM_STORAGE`，清除路径为人工调用清除接口或流程切换。

### 5.4 AGING 生命周期

启动：

- 启动 profile 启用的常规 feature。
- `IR-cut` 使用 `VSPT_IrCutAgingAuto(VS_TRUE)`。
- `Motor` 使用 `VSPT_MotorAgingAuto(VS_TRUE)`。
- `Speaker` 使用循环播放。
- `Record` 仅在 `EnableRecord=1 && Stage=AGING` 时启动。
- 最后启动 `VSPT_AgingTimerTest(VS_TRUE)`。

停止：

- 统一关闭 `VSPT_*Test(VS_FALSE)`。
- 关闭 AGING auto API。
- 关闭录像与老化计时。
- 释放 IR 仲裁状态。

## 6. LCD 老化文案

左屏显示状态、时间和 IP：

| 状态 | 条件 | 文案 |
| --- | --- | --- |
| 运行中 | `fail_bitmap == 0 && completed == 0` | `STATUS RUN`、`TIME hh:mm:ss`、`IP x.x.x.x` |
| 完成态 | `fail_bitmap == 0 && completed == 1` | `STATUS DONE`、`STATION <station>`、`TIME 02:00:00`、`IP x.x.x.x` |
| 异常态 | `fail_bitmap != 0` | `STATUS ERROR`、`ERR <fail_text>`、`TIME hh:mm:ss`、`IP x.x.x.x` |

右屏固定两行实时数据：

- `BATTERY xxx% xxxxmA xxC`
- `MOTOR xxxx/yyyyrpm xx/xxC`

`fail_text`：

- 仅存储异常：`STORAGE`
- 存储加其他异常：`STORAGE|0xXXXXXXXX`
- 非存储异常：`0xXXXXXXXX`

## 7. AGING 测试项映射

| 项目 | 当前实现 |
| --- | --- |
| 出货 TF 卡 | 依赖挂载/可写探针和录像链路，需板端验证 |
| LCD 眼睛屏 | `VSPT_LcdTest` 颜色循环加老化三态 overlay |
| 摄像头录像 | `VSPT_RecordTest(VS_TRUE)` |
| IR-cut | `VSPT_IrCutAgingAuto`，按 `[AGING_CTRL] IrOnMs/IrOffMs` |
| IR 补光 | AGING 下由 IR 仲裁进入强制常亮模式 |
| IR 测距 | `VSPT_IrDistanceTest(VS_TRUE)` |
| TOF | `VSPT_TofTest(VS_TRUE)` |
| 激光 | `VSPT_LaserTest(VS_TRUE)` |
| 电机 | `VSPT_MotorAgingAuto`，按正转/反转/休息参数 |
| 喇叭 | `VSPT_SpkTest(VS_TRUE, ...)` 循环播放 |
| MIC | `VSPT_MicTest(VS_TRUE)` |
| 光感 | `VSPT_AdcTest(VS_TRUE)` |
| 电源/充电 | `VSPT_BatteryTest(VS_TRUE)`，提供电量/电流/温度 snapshot |
| WiFi | 由主进程初始化和 monitor 检查 |
| IMU | `VSPT_ImuTest(VS_TRUE)` |
| 复位进标定 | 满足老化门禁后持久化切换到 `CALIBRATION` |

## 8. 标定模块

标定入口由 `pt_calibration_mgr.c` 聚合，公共类型在 `pt_calibration.h`。

| 项目 | 文件 | 说明 |
| --- | --- | --- |
| TOF 标定 | `pt_calibration_tof.c` | 地面样本采集、Z bias、pitch/roll offset、行 RMS 和行间距验证 |
| IMU 标定 | `pt_calibration_imu.cpp` | 两阶段 `AT_180 -> AT_0`，计算 gyro bias、scale、安装角 |
| 摄像头外参 | `pt_calibration_camera.cpp` | 抓图、棋盘格检测、外参求解 |
| 异步调度 | `pt_calibration_async.c` | 避免控制线程阻塞 |

`VSPT_CommonHandleCalibrationComplete()` 默认执行：

1. LCD 显示 `CALIBRATION DONE / FORMATTING TF CARD`。
2. 执行 `VSHDIDISK_Format`。
3. 调用 `VSPT_AgingStateClear()`。
4. LCD 显示 `FORMAT TF OK / REBOOTING`。
5. 调用 `VSHDIOS_Reboot()`。

调试构建若关闭 `PT_CALIBRATION_COMPLETE_AUTO_FORMAT_REBOOT`，则不会格式化和重启。

## 9. MIC 判定

`bridge/pcba/mic_speaker` 中 `mic_valid` 仍按布尔发布。细分状态码通过 `header.sequence` 透传：

| sequence | 状态 |
| --- | --- |
| `0` | `OK` |
| `1` | `WARMUP` |
| `2` | `LOW_ENERGY` |
| `3` | `CHANNEL_IDENTICAL` |
| `4` | `CHANNEL_CLONE` |
| `5` | `CHANNEL_CLONE_FAST_FAIL` |

相关阈值来自 `[THRESHOLD]`：

- `Mic`
- `MicIdenticalSampleDiffMax`
- `MicIdenticalRatioPermille`
- `MicExactIdenticalSampleDiffMax`
- `MicExactIdenticalRatioPermille`
- `MicFastFailFrames`
- `MicNearCloneRatioPermille`
- `MicNearCloneAvgDiffMax`
- `MicNearCloneEnergyDiffMax`

快速失败：完全一致连续帧数达到 `MicFastFailFrames` 后，直接进入 `CHANNEL_CLONE_FAST_FAIL`。

## 10. Diag perf 桥接

`pt_diag_bridge.c` 支持把 `bridge/diag/perf/run` 请求转成本地 perf provider：

| perf case | provider |
| --- | --- |
| `cpu` / `diag.perf.cpu.run` | `VSAPPDIAG_PerfProviderRunCpu` |
| `mem` / `diag.perf.mem.run` | `VSAPPDIAG_PerfProviderRunMem` |
| `sd` / `diag.perf.sd.run` | `VSAPPDIAG_PerfProviderRunSd` |
| `flash` / `diag.perf.flash.run` | `VSAPPDIAG_PerfProviderRunFlash` |

输出 JSON 通过 `bridge/pcba/diag_perf` 发布，ack 通过 `bridge/diag/perf/ack` 返回。

## 11. 当前边界

- `EnableBt` 不是当前主线 profile 开关；蓝牙扫描需要先合入 `pt_bt.patch` 并补齐构建验证。
- 老化 LCD 文案使用 ASCII，避免依赖额外字体。
- 本仓直接构建依赖外层 SDK，不具备完全自包含构建环境。
- `AGING` 的 2 小时连续运行、重启恢复和异常锁存必须在板端验证；本地静态检查不能替代。
