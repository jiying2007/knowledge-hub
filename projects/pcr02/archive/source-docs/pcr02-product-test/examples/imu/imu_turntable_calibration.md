# IMU 转台标定方案

## 1. 背景与目标

本文是 `app_product_test` 的 IMU 转台标定参考方案，用于解释 `CALIBRATION` 阶段 IMU 标定算法、转台信号、合格判定和结果保存格式。

**标定目标**：利用 180° 转台单次旋转，标定 gyro bias、gyro Z scale factor、accel scale factor 和 roll/pitch 安装角，写入 `sensor_calibration.toml`。

## 2. 与本仓实现关系

| 项目 | 本仓位置 |
|------|----------|
| 标定公共类型 | `pt_calibration.h` |
| IMU 标定实现 | `pt_calibration_imu.cpp` |
| 标定聚合管理 | `pt_calibration_mgr.c` |
| 异步调度 | `pt_calibration_async.c` |
| INI 阈值 | `product_test.ini:[IMU_CALIBRATION]` |

`product_test.ini` 当前相关阈值：

```ini
[IMU_CALIBRATION]
MaxGyroBias=0.05
MaxScaleErr=0.05
MaxMountAngle=0.087
AccelScaleMin=0.95
AccelScaleMax=1.05
```

这些阈值与本文“合格判定”对应。`MaxMountAngle=0.087` 约等于 5°。

---

## 3. 硬件与信号

- **IMU**：QMI8658，6 轴，250 Hz
- **转台**：单轴，精度 ≤ 0.1°
- **坐标系**：标定在 FLU 机体坐标系下（`diag(-1,-1,1)` 变换后）

### 信号定义

只有两个信号：

| 信号 | 含义 |
|------|------|
| 转台位于 180° | 机器人就位，程序开始静态采集 |
| 转台到达 0° | 旋转结束，程序开始后静态采集 |

### 时序

```
  程序                              转台
  ────                            ────
    │                               │
    │◄── 转台位于 180° ─────────────│
    │                               │
    │  [静态采集 5s]                │  转台静止
    │                               │
    │──  开始标定（触发旋转）──────▶│
    │                               │
    │  [旋转中，持续采集 gyro]      │  180° → 0°
    │                               │
    │◄── 转台到达 0° ───────────────│
    │                               │
    │  [静态采集 5s]                │  转台静止
    │                               │
    │  [计算 + 保存]                │
    │                               │
    │──  标定完成  ────────────────▶│
    │                               │
```

---

## 4. 标定原理

### 4.1 Gyro bias

静止时陀螺仪输出 = bias + 噪声，长时间平均得到 bias：

```
b_hat = (1/N) × Σ ω_i
```

取旋转前后两段静止期的平均值，进一步消除温漂：

```
bias_final = (bias_before + bias_after) / 2
```

### 4.2 Gyro scale factor

转台精确旋转 180°（π rad），积分陀螺仪输出与真值对比：

```
θ_meas = Σ (gyro_z[i] - bias) × dt[i]     # 旋转期间积分
sf_z   = |θ_meas| / π
```

用前后静止段平均 bias 减少误差。5s 静态采集的 bias 精度约 ±0.001 rad/s，5s 旋转的 bias 误差贡献约 0.005 rad，相对 π = 3.14 rad，scale factor 误差 < 0.2%。

### 4.3 Accel scale factor

静止时加速度范数等于重力：

```
sf_acc = 9.80665 / sqrt(ax² + ay² + az²)
```

### 4.4 Roll/Pitch 安装角

静止时重力在 FLU 坐标系的投影：

```
pitch_mount = atan2(ax, sqrt(ay² + az²))
roll_mount  = atan2(-ay, az)
```

---

## 5. 标定流程

### 状态机

```
  转台位于 180°
       │
       ▼
  ┌──────────┐
  │ STATIC_1 │  静止采集 5s → gyro bias / accel / 安装角
  └────┬─────┘
       │ 触发旋转
       ▼
  ┌──────────┐
  │ ROTATING │  持续采集 gyro_z，积分角度
  └────┬─────┘
       │ 收到 到达 0°
       ▼
  ┌──────────┐
  │ STATIC_2 │  静止采集 5s → 后 bias
  └────┬─────┘
       │
       ▼
  ┌──────────┐
  │ COMPUTE  │  计算 sf_z，合格判定，写文件
  └────┬─────┘
       │
       ▼
  标定完成
```

### Step 1: 前静态采集（STATIC_1）

收到"转台位于 180°"信号后开始，采集 5 秒：

```python
data = collect_imu(5.0)
d = data[125:]                  # 丢弃前 0.5s

bias_gx_before = mean(d.gyro_x)
bias_gy_before = mean(d.gyro_y)
bias_gz_before = mean(d.gyro_z)

mean_ax = mean(d.acc_x)
mean_ay = mean(d.acc_y)
mean_az = mean(d.acc_z)

accel_scale = 9.80665 / sqrt(mean_ax**2 + mean_ay**2 + mean_az**2)
pitch_mount = atan2(mean_ax, sqrt(mean_ay**2 + mean_az**2))
roll_mount  = atan2(-mean_ay, mean_az)
```

### Step 2: 旋转采集（ROTATING）

触发转台旋转，开始持续采集 gyro_z，直到收到"到达 0°"信号：

```python
send(START_ROTATE)
rot_data = collect_imu_until(ARRIVED_AT_0)
```

> 收到到位信号后等待 0.2s 再进入 STATIC_2，让转台振动衰减。

### Step 3: 后静态采集（STATIC_2）

采集 5 秒：

```python
data = collect_imu(5.0)
d = data[125:]

bias_gx_after = mean(d.gyro_x)
bias_gy_after = mean(d.gyro_y)
bias_gz_after = mean(d.gyro_z)
```

### Step 4: 计算

```python
# Gyro bias：前后平均
bias_gx = (bias_gx_before + bias_gx_after) / 2.0
bias_gy = (bias_gy_before + bias_gy_after) / 2.0
bias_gz = (bias_gz_before + bias_gz_after) / 2.0

# Gyro z scale factor：积分 / π
theta = 0
for i in range(len(rot_data)):
    theta += (rot_data[i].gyro_z - bias_gz) * dt[i]

sf_z = abs(theta) / pi
```

### Step 5: 合格判定

| 指标 | 范围 | 不通过处理 |
|------|------|-----------|
| \|bias_gx\|, \|bias_gy\|, \|bias_gz\| | < 0.05 rad/s | 报错 |
| \|sf_z - 1.0\| | < 5% | 报错 |
| \|roll_mount\|, \|pitch_mount\| | < 5° | 报错 |
| accel_scale | 0.95 ~ 1.05 | 报错 |
| \|bias_before - bias_after\| | < 0.005 rad/s | 温漂过大，报警 |

### Step 6: 保存

```toml
[imu]
gyro_bias_x = -0.000312      # rad/s
gyro_bias_y = 0.000158        # rad/s
gyro_bias_z = 0.000203        # rad/s
gyro_scale_z = 1.0023         # 无量纲
accel_scale = 0.9987          # 无量纲
roll_mount  = 0.0032          # rad
pitch_mount = -0.0018         # rad
calibration_date = "2026-05-14"
```

---

## 6. 标定参数使用方式

在 `ImuProcessor::process()` 中的应用顺序：

```
Raw IMU Data
    │
    ▼
[1] 坐标变换 diag(-1,-1,1)          (已有)
    │
    ▼
[2] acc *= accel_scale               (新增)
    │
    ▼
[3] gyro -= gyro_bias                (改为加载标定值)
    │
    ▼
[4] gyro_z *= gyro_scale_z           (新增)
    │
    ▼
[5] R(roll_mount, pitch_mount)       (新增，旋转补偿)
    acc  = R × acc
    gyro = R × gyro
    │
    ▼
[6] Dead zone 过滤                   (已有)
    │
    ▼
[7] Mahony AHRS                     (已有)
    │
    ▼
[8] Butterworth 滤波                 (已有)
```

`[imu]` 节不存在时保持当前行为，向后兼容。

---

## 7. 异常处理

| 异常 | 原因 | 处理 |
|------|------|------|
| bias > 0.05 rad/s | IMU 异常 / 温度不稳定 | 报错 |
| sf_z 偏差 > 5% | 转台精度 / IMU 故障 | 报错 |
| 前后 bias 差 > 0.005 rad/s | 温漂严重 | 报警，结果仍保存 |
| 到位信号超时 > 30s | 转台通信故障 | 中止 |
| roll/pitch > 5° | 转台未放平 | 报错 |

## 8. 验证建议

- 上位机按 `AT_180 -> AT_0` 两阶段触发，确认 `VSPT_CalibImuStartAt180` 和 `VSPT_CalibImuFinishAt0` 均返回成功。
- 观察标定状态进度是否从前静止段、旋转段推进到后静止段。
- 检查输出结果中的 `gyro_bias_*`、`gyro_scale_z`、`accel_scale`、`roll_mount`、`pitch_mount` 是否落在 `[IMU_CALIBRATION]` 阈值内。
- 异常验证至少覆盖转台超时、安装角超限和 gyro scale 超限。

---

## 7. 总结

| 项目 | 值 |
|------|------|
| 总耗时 | ~15s（5s静止 + ~5s旋转 + 5s静止） |
| 人工操作 | 放上机器人，等待完成 |
| 标定参数 | gyro bias ×3, gyro_scale_z, accel_scale, roll/pitch mount |
| 精度 | bias ±0.001 rad/s, scale factor ±0.2%, 安装角 ±0.5° |
