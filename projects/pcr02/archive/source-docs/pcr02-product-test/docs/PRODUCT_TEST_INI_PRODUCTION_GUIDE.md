# product_test.ini 产线使用规则

## 1. 适用范围

本文用于指导生产、测试和现场维护人员维护 TF 卡内的产测配置：

```text
/var/run/media/mmcblk0p1/vstrong/product_test.ini
```

适用阶段：

- `PCBA`
- `SEMI_FINISHED`
- `AGING`
- `CALIBRATION`
- `ACOUSTIC`

本仓根目录的 `product_test.ini` 是开发模板。现场必须以设备 TF 卡中的实际文件为准。

## 2. 核心规则

- `Stage` 决定当前运行阶段。
- `Station` 决定读取哪个 `PROFILE_<Stage>_<Station>` 段。
- `Operator` 必须与上位机绑定请求中的 `id` 一致。
- `StrictIsolation` 建议固定为 `1`。
- `SEMI_FINISHED` 必须使用下划线，不能写成 `SEMI-FINISHED`。
- 老化阶段由设备自动控制，默认不接受上位机测试控制指令。
- 老化达标并且无失败后，才能通过复位键自动切换到标定。
- 标定完成后，默认会格式化 TF 卡并重启。

## 3. INFO 段

字段：

| 字段 | 类型 | 规则 |
| --- | --- | --- |
| `Stage` | 字符串 | 阶段名，见下表 |
| `Station` | 正整数 | 当前工位号 |
| `Operator` | 正整数 | 工位绑定 ID，必须与上位机绑定 ID 一致 |
| `StrictIsolation` | `0/1` | 建议 `1`，控制阶段隔离策略 |

可用 `Stage`：

| Stage | 使用场景 | 备注 |
| --- | --- | --- |
| `PCBA` | PCBA 工位 | 支持上位机绑定和控制 |
| `SEMI_FINISHED` | 半成品工位 | 支持上位机绑定和部分标定类型 |
| `AGING` | 整机老化 | 走设备自动老化和复位门禁 |
| `CALIBRATION` | 标定工位 | 推荐由 AGING 达标后自动切换 |
| `ACOUSTIC` | 声学专项 | 仅专项测试使用 |

示例：

```ini
[INFO]
Stage=AGING
Station=1
Operator=100
StrictIsolation=1
```

## 4. 工位配置

### 4.1 PCBA

```ini
[INFO]
Stage=PCBA
Station=1
Operator=100
StrictIsolation=1
```

要求存在：

```ini
[PROFILE_PCBA_1]
```

### 4.2 半成品

```ini
[INFO]
Stage=SEMI_FINISHED
Station=1
Operator=100
StrictIsolation=1
```

要求存在：

```ini
[PROFILE_SEMI_FINISHED_1]
```

半成品阶段与 PCBA 阶段的基础 profile 默认一致，但半成品阶段允许 `WHEELS` 标定请求进入；其它标定请求仍应在 `CALIBRATION` 阶段执行。

### 4.3 整机老化

```ini
[INFO]
Stage=AGING
Station=1
Operator=100
StrictIsolation=1
```

要求存在：

```ini
[PROFILE_AGING_1]
[AGING_CTRL]
```

老化状态由设备写入：

```text
/var/run/media/mmcblk0p1/vstrong/aging_state.ini
```

不要人工拼接老化时长。未达标重启会清零连续时长；达标后会锁存通过态；出现失败后会清除通过锁存。

### 4.4 标定

标准流程不是人工改 `Stage=CALIBRATION`，而是：

1. `AGING` 连续运行达标。
2. `fail_bitmap == 0`。
3. 按复位键。
4. 设备自动把 `Stage` 持久化为 `CALIBRATION`。
5. monitor task 重载配置并进入标定。

特殊调试时可人工设置：

```ini
[INFO]
Stage=CALIBRATION
Station=1
Operator=100
StrictIsolation=1
```

要求存在：

```ini
[PROFILE_CALIBRATION_1]
[TOF_CALIBRATION]
[IMU_CALIBRATION]
```

## 5. 上位机绑定规则

上位机 `bind` 请求必须同时满足：

| 请求字段 | 必须匹配 |
| --- | --- |
| `id` | `product_test.ini:[INFO] Operator` |
| `type` | 当前 `Stage` 对应类型 |

映射：

| Stage | bind type |
| --- | --- |
| `PCBA` | `PCBA` |
| `SEMI_FINISHED` | `SEMI_FINISHED` |
| `CALIBRATION` | `CALIBRATION` |

AGING 阶段按老化隔离策略处理，不建议发送控制类命令。

## 6. PROFILE 段

程序按以下规则查找 profile：

```text
PROFILE_<Stage>_<Station>
```

例如：

```ini
[INFO]
Stage=AGING
Station=1
```

会读取：

```ini
[PROFILE_AGING_1]
```

当前主线支持的 profile 开关：

| 开关 | 功能 |
| --- | --- |
| `EnableAdc` | 光感/ADC |
| `EnableAvRtsp` | AV/RTSP |
| `EnableBattery` | 电池/充电状态 |
| `EnableFactory` | 工厂键/复位键 |
| `EnableImu` | IMU |
| `EnableIrLight` | IR 补光 |
| `EnableIrCut` | IR-cut |
| `EnableIrRecv` | 红外接收 |
| `EnableIrDistance` | IR 测距 |
| `EnableLaser` | 激光 |
| `EnableLcd` | LCD |
| `EnableMic` | MIC |
| `EnableMotor` | 电机 |
| `EnableShutdown` | 关机阶段通知 |
| `EnableSpeaker` | 喇叭 |
| `EnableTof` | TOF |
| `EnableRecord` | AGING 录像 |

新增 `Station` 时必须复制并维护对应 profile 段。缺少 profile 段会导致 feature mask 加载失败或测试项缺失。

### 6.1 蓝牙说明

当前主线代码尚未支持 `EnableBt`。蓝牙扫描接入只存在于 `pt_bt.patch` 和 `pt_hw_bt.backup`：

- `pt_bt.patch` 计划增加 `PT_FEATURE_BT`、`VSPT_CommonPubBt`、`VSPT_BtTest` 和 `EnableBt`。
- 未合入前，不要在正式产线配置中依赖 `EnableBt=1`。
- `[BLE] ScanName` 可作为预留字段保留，但当前主线不会启动蓝牙扫描。

## 7. AGING_CTRL

| 字段 | 单位 | 默认/建议 | 说明 |
| --- | --- | --- | --- |
| `DurationMs` | ms | `7200000` | 老化总时长，2 小时 |
| `IrOnMs` | ms | `600000` | IR/IR-cut 自动阶段开时长 |
| `IrOffMs` | ms | `1200000` | IR/IR-cut 自动阶段关时长 |
| `MotorForwardRpm` | rpm | `3000` | 正转速度 |
| `MotorForwardMs` | ms | `1800000` | 正转时长 |
| `MotorReverseRpm` | rpm | `-3000` | 反转速度 |
| `MotorReverseMs` | ms | `1800000` | 反转时长 |
| `MotorRestRpm` | rpm | `0` | 休息速度 |
| `MotorRestMs` | ms | `600000` | 休息时长 |
| `LcdFontId` | enum | `0` | `0=8x16`、`1=16x16`、`2=16x28` |

推荐模板：

```ini
[AGING_CTRL]
DurationMs=7200000
IrOnMs=600000
IrOffMs=1200000
MotorForwardRpm=3000
MotorForwardMs=1800000
MotorReverseRpm=-3000
MotorReverseMs=1800000
MotorRestRpm=0
MotorRestMs=600000
LcdFontId=0
```

## 8. PCBA/半成品测试项

### 8.1 当前默认开关

`PROFILE_PCBA_1` 与 `PROFILE_SEMI_FINISHED_1` 当前默认一致：

| 开关 | PCBA | 半成品 | 验收重点 |
| --- | --- | --- | --- |
| `EnableAdc` | `1` | `1` | 光感/ADC 数据上报 |
| `EnableAvRtsp` | `1` | `1` | 视频/RTSP 链路可用 |
| `EnableBattery` | `1` | `1` | 电量、电流、温度状态 |
| `EnableFactory` | `1` | `1` | 工厂键/复位键事件 |
| `EnableImu` | `1` | `1` | IMU 数据持续上报 |
| `EnableIrLight` | `1` | `1` | IR 补光可控 |
| `EnableIrCut` | `1` | `1` | IR-cut 可控 |
| `EnableIrRecv` | `1` | `1` | 红外接收可用 |
| `EnableIrDistance` | `1` | `1` | IR 测距数据 |
| `EnableLaser` | `1` | `1` | 激光可控 |
| `EnableLcd` | `1` | `1` | LCD 可显示/切换 |
| `EnableMic` | `1` | `1` | MIC 判定状态 |
| `EnableMotor` | `1` | `1` | 电机/轮子控制 |
| `EnableShutdown` | `1` | `1` | 关机阶段通知 |
| `EnableSpeaker` | `1` | `1` | 喇叭播放 |
| `EnableTof` | `1` | `1` | TOF 数据 |
| `EnableRecord` | `0` | `0` | 不启动 AGING 录像 |

### 8.2 PCBA 操作检查

- `Stage=PCBA`。
- `Station` 与 `PROFILE_PCBA_<Station>` 对应。
- 上位机 bind：`type=PCBA`，`id=Operator`。
- 观察日志 `Loaded config: Stage=PCBA`。
- 确认 `bridge/pcba/version`、WiFi、硬件测试 topic 按上位机预期上报。
- 组件控制失败时，先检查对应 `Enable*` 是否为 `1`。

### 8.3 半成品操作检查

- `Stage=SEMI_FINISHED`。
- `Station` 与 `PROFILE_SEMI_FINISHED_<Station>` 对应。
- 上位机 bind：`type=SEMI_FINISHED`，`id=Operator`。
- 观察日志 `Loaded config: Stage=SEMI_FINISHED`。
- 普通硬件测试项按 PCBA 同口径检查。
- 半成品允许 `WHEELS` 标定请求；TOF、IMU、Camera 等其它标定仍需切到 `CALIBRATION`。

## 9. 阈值段

### 9.1 MIC

| 字段 | 含义 |
| --- | --- |
| `Mic` | 双通道能量阈值 |
| `MicIdenticalSampleDiffMax` | 近似相同判定的单采样最大差值 |
| `MicIdenticalRatioPermille` | 近似相同样本占比阈值，0 到 1000 |
| `MicExactIdenticalSampleDiffMax` | 完全相同判定的单采样最大差值 |
| `MicExactIdenticalRatioPermille` | 完全相同样本占比阈值，0 到 1000 |
| `MicFastFailFrames` | 连续完全相同多少帧后快速失败，0 表示关闭 |
| `MicNearCloneRatioPermille` | 近克隆占比阈值 |
| `MicNearCloneAvgDiffMax` | 近克隆平均差值阈值 |
| `MicNearCloneEnergyDiffMax` | 近克隆能量差阈值 |

推荐值：

```ini
[THRESHOLD]
Mic=0
MicIdenticalSampleDiffMax=2
MicIdenticalRatioPermille=995
MicExactIdenticalSampleDiffMax=0
MicExactIdenticalRatioPermille=995
MicFastFailFrames=5
MicNearCloneRatioPermille=800
MicNearCloneAvgDiffMax=1
MicNearCloneEnergyDiffMax=2
```

### 9.2 标定

TOF：

```ini
[TOF_CALIBRATION]
MaxPitchAngleDeg=8.0
MaxRollAngleDeg=5.0
MaxRowLineRms=0.100
MaxRowXDev=0.100
MaxRowXRefDev=0.100
MinRowXGap=0.100
RowXRef0=0.39
RowXRef1=0.29
RowXRef2=0.23
```

IMU：

```ini
[IMU_CALIBRATION]
MaxGyroBias=0.05
MaxScaleErr=0.05
MaxMountAngle=0.087
AccelScaleMin=0.95
AccelScaleMax=1.05
```

## 10. 产线检查清单

### 10.1 上电前

- TF 卡存在 `vstrong/product_test.ini`。
- `Stage/Station/Operator/StrictIsolation` 填写正确。
- 存在对应 `PROFILE_<Stage>_<Station>` 段。
- 老化工位存在 `[AGING_CTRL]`。
- 标定工位存在 `[TOF_CALIBRATION]` 和 `[IMU_CALIBRATION]`。
- 声学/MIC 相关工位确认 `[THRESHOLD]` 参数符合当前判定口径。

### 10.2 测试中

- 设备日志出现 `Loaded config`。
- 日志中的 `Stage/Station/Operator/FeatureMask` 与配置一致。
- AGING 阶段无持续 `aging_state.ini` 写入失败。
- AGING 阶段 LCD 左屏显示状态，右屏保持电池/电机实时数据。
- 标定阶段上位机进度与 `BridgeCalibrateInfo` 状态一致。

### 10.3 工位切换

- PCBA/半成品切换：更新 `Stage/Station/Operator` 和对应 profile。
- AGING 到 CALIBRATION：必须优先通过复位键门禁自动切换。
- CALIBRATION 完成：设备默认格式化 TF 卡并重启，这是预期行为。

## 11. 常见错误

| 错误 | 影响 | 处理 |
| --- | --- | --- |
| `Stage` 拼错 | 阶段解析失败，测试不启动 | 改为合法 Stage |
| `SEMI-FINISHED` | 无法匹配半成品阶段 | 改为 `SEMI_FINISHED` |
| `Operator` 与上位机不一致 | 绑定失败 | 同步工位绑定 ID |
| 缺少 profile 段 | feature mask 缺失 | 补 `PROFILE_<Stage>_<Station>` |
| 老化未达标人工改 `CALIBRATION` | 绕过门禁，影响追溯 | 恢复标准流程 |
| 配置 `EnableBt=1` | 当前主线不生效 | 先合入并验证蓝牙补丁 |
