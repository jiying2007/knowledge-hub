---
title: Sigmastar AOV 与光敏控制全面分析
doc_type: report
knowledge_type: decision
maturity: verified
status: archived
owner: team-core
created: 2026-05-08
last_updated: 2026-05-12
tags: [aov, lightsensor, analysis]
related: []
validation_refs: []
---

# Sigmastar AOV 与光敏控制全面分析

> 归档说明：本文为历史报告，只记录当时结论与验证；当前执行以 Knowledge Hub active 文档、本仓实际脚本、`~/knowledge-hub/domains/embedded/` 和 `~/knowledge-hub/projects/pcr02-ssc305/` 的当前入口为准。

> 分析范围：`examples/sigmastar/`  
> 日期：2026-05-08

---

## 一、整体架构

```
应用层 (st_common_aov.c)
    │
    ├─ 正常模式 FPS_HIGH (15fps)          ←→  AE自动收敛
    └─ AOV 模式  FPS_LOW  (1fps)          ←→  FastAE + 睡眠帧
         │
         ├─ 硬光敏 (HW Light Sensor)
         │     └─ /dev/light_misc  ←→  内核驱动 (light_misc_control_main.c)
         │              └─  I2C 光感芯片 → 读 Lux 值
         │
         └─ 软光敏 (SW Light Sensor)
               └─ ISP AE 亮度统计 (LumY) + QueryDayNightInfo
                         └─ 日夜阈值由上层设置

硬件控制（均通过 /dev/light_misc ioctl）
    ├─ IRCUT（两路 GPIO，步进电机）
    │     ON → 白天（截断红外）
    │     OFF → 夜晚（透过红外）
    │     KEEP → 两路 GPIO 均置 0，释放线圈（防烧毁）
    └─ IR LED（GPIO 或 PWM）
          LONG_TERM_ON   → 持续亮（高帧率夜间）
          LONG_TERM_OFF  → 持续灭（白天）
          MULTI_FRAME    → 单帧闪烁（AOV 低帧率，帧结束后自动关）
```

---

## 二、正常模式（FPS_HIGH = 15fps）

### 2.1 进入/退出

```c
ST_Common_AovSetHighFps(pstAovHandle)
  → eCurrentFps = E_ST_FPS_HIGH
  → 禁用 sensor 睡眠模式：
      MI_VIF_CustFunction(vifDevId, E_MI_VIF_CUSTCMD_SLEEPPARAM_SET,
                          bSleepEnable=FALSE)
  → SCL 输出端口深度设置为 (2, 4)
  → AWB 参数：period=3，speed=20（慢收敛，抗抖动）
```

### 2.2 光敏判断（高帧率下）

- **硬光敏高帧率路径**：读 ISP AE `s32BV`（亮度值）
  - `s32BV > -10000 (DAYNIGHT_BV_THRESHOLD)` → 白天
  - 否则 → 夜晚
- **软光敏高帧率路径**：与低帧率相同，用 `LumY` + `QueryDayNightInfo`

### 2.3 日夜切换动作（日间）

```
加载白天 IQ bin (au8IqApiBinBrightPath)
SetColorToGray(FALSE)          // 彩色模式
TurnOnIRCut()                  // IRCUT ON + 100ms延迟 + KEEP
TurnOffIRLed()                 // IR LED 长期关
SetHightFpsAWBParam()          // AWB period=3, speed=20
```

### 2.4 日夜切换动作（夜间，高帧率）

```
加载夜间 IQ bin (au8IqApiBinDarkPath)
SetColorToGray(TRUE)           // 灰度模式
TurnOffIRCut()                 // IRCUT OFF + 100ms延迟 + KEEP
TurnOnIRLed()                  // IR LED 长期开（LONG_TERM_ON）
SetHightFpsAWBParam()          // AWB period=3, speed=20
```

---

## 三、AOV 模式（FPS_LOW = 1fps）

### 3.1 进入/退出

```c
ST_Common_AovSetLowFps(pstAovHandle)
  → 停止 SCL 通道 → 丢弃 VENC 积压流
  → eCurrentFps = E_ST_FPS_LOW
  → 启用 sensor 睡眠模式：
      MI_VIF_CustFunction(vifDevId, E_MI_VIF_CUSTCMD_SLEEPPARAM_SET,
                          bSleepEnable=TRUE, u32FrameCntBeforeSleep=1)
  → SCL 输出端口深度设置为 (2, 2)
  → AWB 参数：period=1，speed=80（最快收敛）
  → 请求 IDR 帧
  → 重启 SCL 通道
```

### 3.2 Suspend/Resume 循环

```
运行中
  ↓ 无目标检测
ST_Common_AovEnterSuspend()
  → 重置 SW 光敏 AE 计数器
  → 写 /sys/power/state "mem"  → 系统进入 mem suspend
  ↓ 唤醒（定时器/PIR/预览）
ST_Common_AovWakeupCheck()  → 判断唤醒类型
  ↓
如果是 PIR 唤醒 → SetHighFps → 检测 → 有目标则录制
如果是 Timer 唤醒 → SetLowFps → 继续光敏判断
```

### 3.3 日夜切换动作（夜间，低帧率）

```
加载夜间 IQ bin
SetColorToGray(TRUE)
TurnOffIRCut()
TurnMultiFrameIRLed()          // MULTI_FRAME 模式（单帧闪烁）
```

`MULTI_FRAME` 的硬件逻辑（内核驱动）：
- Resume 通知到达时 → 延迟 `delayOpenTimeMs` → 开灯
- VIF 帧结束中断 `FrameDone_CallBack` → 关灯
- 因此每帧只亮一次，节省功耗

---

## 四、FastAE 机制

AOV 1fps 模式唤醒后，ISP AE 收敛慢（每帧间隔 1 秒），需要 FastAE 在几帧内收敛。

### 4.1 触发条件

```c
ST_Common_FastAE_Run()
  条件：bIsStable==FALSE && !bIsReachBoundary
         && |AvgY - SceneTarget| > u32RunThreshold
```

### 4.2 执行流程

```
1. 启用 sensor 睡眠模式（等 sensor 入睡）
2. 请求 IDR（清空 VENC 积压）
3. 切小图模式（小分辨率 + 高帧率）
   → MI_SNR_CustFunction(E_ST_CMDID_FAE_SWITCH_SENSOR_AE, AEswitch=1)
4. 等待小图 AE 完成（超时 800ms）
5. 将小图 AE 结果转换为全图 AE 参数（曝光时间/增益缩放）
6. 注入 ISP：MI_ISP_CUS3A_SetAeParam + 手动曝光模式
7. 切回全图模式
8. 等待 ISP 收敛到稳定
9. 再次等待 sensor 入睡
```

### 4.3 核心参数转换

```c
// 利用小图 AE 结果估算全图所需曝光
TH = IspGainMin * shutter_small * again_small * SceneTarget / ymean_small;
if TH >= maxShutter * SNRGainMin * IspGainMin:
    // 需要大增益：延长曝光时间到最大，再拉增益
    shutter_full = maxShutter
    again_full   = TH / (maxShutter * IspGainMax)
else:
    // 增益够用：最小增益，调快门
    again_full   = SNRGainMin
    shutter_full = TH / (SNRGainMin * IspGainMin)
```

---

## 五、硬件光敏（HW Light Sensor）

### 5.1 硬件层次

```
I2C 光感芯片（光敏二极管 + ADC）
    ↓ I2C（lightsensor-i2c 配置自 DTS）
内核模块 light_misc_control.ko
    ↓ ioctl
/dev/light_misc
    ↓ Dev_Light_Misc_Device_*()
st_common_aov.c：__UpdataLightParam()
```

### 5.2 光感寄存器操作

```c
// 上电初始化
reg[0x03] = 0x04  // power on
reg[0x04] = tig_mode_value  // TIG 积分时间

// 读 Lux
reg[0x20] → update 标志（bit0=1 表示新数据就绪）
reg[0x21~0x24] → chn0/chn1 的低/高字节（16bit）
reg[0x05] → 增益寄存器

lux = (chn0 * 15 * 25 / gain_l - chn1 * 15 * 25 / gain_h) / 1000
```

**TIG 积分时间（module 参数 `tig_mode`）：**

| tig_mode | 积分时间 | 对应光表 |
|----------|---------|---------|
| 0        | 100ms   | g_stLightTable[0] |
| 1        | 400ms   | g_stLightTable[1] |
| 2        | 688.5ms | （无对应光表） |

### 5.3 光感值到 ISP 参数的映射

```c
// 硬光敏低帧率模式下，根据 lux 查表设置 ISP 曝光
const ST_Common_AovLightTable_t g_stLightTable[2][10] = {
  // [TIG=100] { lux, shutter_us, sensor_gain, isp_gain }
  {  {1,  30000, 262144, 1024},   // 1 Lux
     {7,  30000,   4128, 1024},   // 7 Lux
     {30, 10000,   3040, 1024},   // 30 Lux
     ...                          // 最多 10 档
  },
  // [TIG=400] 类似
};

__UpdataLightParam():
  lux = Dev_Light_Misc_Device_Get_LightSensor_Value(fd)
  // 查表找最近的档位（线性插值）
  // 判断日夜：lux > 10 (DAYNIGHT_LUX_THRESHOLD) → 白天
```

### 5.4 差异门限过滤

```c
// 避免 lux 轻微抖动触发频繁切换
if |lux - lastLux| < u32DiffLux:
    bUpdateLight = FALSE  // 不更新
```

---

## 六、软件光敏（SW Light Sensor）

软光敏不依赖外部 ADC，利用摄像头 ISP 内部的 AE 亮度统计来判断日夜。

### 6.1 判断流程

```
1. 等待 AE 更新（轮询 MI_ISP_CUS3A_GetDoAeCount 计数变化）
2. 读 AE 曝光信息：MI_ISP_AE_QueryExposureInfo()
   → stHistWeightY.u32LumY（画面亮度）
   → bIsStable（AE 是否稳定）
3. AE 不稳定 → 重置稳定帧计数，维持当前 IR 状态
4. AE 稳定 → 稳定帧计数 +1
5. 稳定帧 >= STABLEFRAMESBEFORETURNIR (=2) → 查 DayNightInfo
   MI_ISP_IQ_QueryDayNightInfo() → bD2N / bN2D 标志
6. bD2N=TRUE → 切夜间；bN2D=TRUE → 切白天
7. 切换后 bFlagTurnIRLedCut=TRUE，等再稳定 STABLEFRAMESAFTERTURNIR(=6) 帧
   才允许下次切换
```

### 6.2 与硬光敏的区别

| 维度 | 硬光敏 | 软光敏 |
|------|--------|--------|
| 传感器 | 外部 I2C 光感芯片 | ISP 内部 AE 亮度统计 |
| 判断依据 | Lux 绝对值（物理光照度） | LumY 相对亮度 + ISP 内部 D/N 算法 |
| 响应速度 | 较慢（受 TIG 积分时间影响） | 每帧更新（受 AE 稳定时间影响） |
| 补光影响 | 不受红外补光影响 | 红外补光会抬高 LumY，需调整阈值 |
| 适用场景 | 充电中（稳定供电，ADC 精度高） | 未充电（省电，无额外硬件） |
| 阈值调整 | 固定（lux > 10 = 白天） | 可通过 SetDayNightThreshold() 动态调 |

### 6.3 在 hdi_vi.c 中的实现（本项目 `_VI_IspSwLightSensor`）

```c
// 与 sample 不同：直接比较 LumY 与自定义阈值，不完全依赖 ISP bD2N/bN2D
if (LumY < g_u32ThresholdD2N) → 日转夜
if (LumY >= g_u32ThresholdN2D) → 夜转日

// 阈值由 VSHDIVI_IspSetDayNightThreshold(D2N, N2D) 设置
// IR 灯开时：luma 被补光抬高，需用更高阈值
// IR 灯关时：用正常阈值
```

---

## 七、`light_misc_control` 内核驱动

### 7.1 目录结构（新增）

```
examples/sigmastar/aov/light_misc_control/driver/
├─ light_misc_control_main.c    // 主逻辑（ioctl 处理，帧结束回调）
├─ light_misc_control_hw.c      // 硬件操作（I2C 光感、GPIO IRCUT、IR LED）
├─ light_misc_control_i2c.c     // I2C 读写封装
├─ light_misc_control_main.h    // 数据结构定义（Device_State）
└─ module.mk
```

### 7.2 设备注册与初始化

```c
// DTS 配置项
"lightsensor-i2c": I2C 总线号
"ir-ctrlmode": 0=GPIO / 1=PWM
"ir-pad": GPIO 编号或 PWM 参数（channel/period/duty）
"ircut-pad": 两路 IRCUT GPIO 编号

// 用户空间 init
Dev_Light_Misc_Device_Init(fd, vifDevId)
  → ioctl(IOCTL_LIGHT_MISC_CONTROL_INIT)
      → 内核分配 pLightState，创建工作线程/hrtimer
      → 返回帧结束回调函数指针
  → MI_VIF_CustFunction(E_MI_VIF_CUSTCMD_FRAMEEND_NOTIFY, fun_ptr_addr)
      → 注册到 VIF 帧结束中断
```

### 7.3 MULTI_FRAME 模式的工作原理

```
系统从 suspend 唤醒
    ↓
platform resume 回调 SSTAR_Light_Misc_Control_Resume_Notify_Main()
    ↓ 延迟 delayOpenTimeMs
开灯（hrtimer 或 kthread）
    ↓
VIF 开始输出帧
    ↓
VIF 帧结束中断 → FrameDone_CallBack(bDoneFlag=TRUE)
    → 关灯（E_SWITCH_STATE_OFF）
    ↓
每帧只亮一次曝光，之后即关
```

**为什么 AOV 低帧率用 MULTI_FRAME：**  
1fps 下大部分时间系统处于 suspend，IR 长亮意味着持续耗电。  
MULTI_FRAME 只在帧曝光期间亮灯，其余时间 suspend 期间灯灭，大幅节省功耗。

### 7.4 IRCUT 控制细节

```c
// 两路 GPIO 控制步进电机（双极驱动）
ON  (截断红外/白天)：GPIO[0]=0, GPIO[1]=1  (ir_cut_select=0)
OFF (透过红外/夜间)：GPIO[0]=1, GPIO[1]=0  (ir_cut_select=0)
KEEP（保持并释放线圈）：GPIO[0]=0, GPIO[1]=0

// 为什么要 KEEP？
// 步进电机到达限位后持续通电会过热烧毁线圈
// ON/OFF 后 100ms 再调 KEEP，释放驱动电流
```

### 7.5 IR LED 控制

```c
// 控制模式 0：GPIO
camdriver_gpio_direction_output(gpio_id, 1/0)

// 控制模式 1：PWM（可调强度）
CamPwmConfig(ir_pwm_handle, ..., duty=lightIntensity)
// lightIntensity 可从 Set_Attr 传入，实现亮度调节
```

---

## 八、光感选择逻辑（本项目新增）

**需求**：充电时（`u8Status=1`）用软光敏，不充电（`u8Status=0`）用硬光敏。

```
onChargeCallback(u8Status)
    │
    ├─ u8Status == 1 → IrLight::setChargeStatus(true)
    │     → VSHDIVI_IspSetDayNightThreshold(D2N, N2D)  // 按当前 IR 灯状态选阈值
    │     → VSHDIVI_IspSetSWLightSensor(TRUE)           // 启用软光敏
    │
    └─ u8Status == 0 → IrLight::setChargeStatus(false)
          → VSHDIVI_IspSetSWLightSensor(FALSE)          // 禁用软光敏
          → IrLight workerThread 继续用 ADC 读硬光敏

IrLight::setRelight(isnight)     // 任何模式下切换 IR 灯时都会调用
    → 切换 IRCUT + IR LED + IQ 文件
    → 如果当前是软光敏模式：
          IR 灯亮（夜间）→ SetDayNightThreshold(D2N_IR_ON, N2D_IR_ON)
          IR 灯灭（白天）→ SetDayNightThreshold(D2N_IR_OFF, N2D_IR_OFF)
```

**阈值组选择原因：**  
红外补光打开后，摄像头画面 LumY 被人为抬高（红外光补充了可见光分量），  
如果仍用原始阈值，会在夜间误判为白天（LumY 看起来"足够亮"）。  
因此 IR 灯开时需要更高的阈值来避免假触发。

---

## 九、日夜切换完整状态机（参考 sigmastar example）

```
                    ┌─────────────────────────────┐
                    │      E_ST_LIGHT_BRIGHT       │
                    │   (白天：IRCUT=ON, IR灯灭)    │
                    └───────────────┬─────────────┘
                                    │
           LumY < D2N阈值 / Lux <= 10 / bD2N=TRUE
                                    ↓
                          ┌─────────────────┐
                          │  D2N 切换动作    │
                          │  1. 加载夜间IQ   │
                          │  2. ColorToGray │
                          │  3. IRCUT OFF   │
                          │  4. IR LED ON   │
                          │  5. 更新阈值     │
                          └────────┬────────┘
                                    ↓
                    ┌─────────────────────────────┐
                    │       E_ST_LIGHT_DARK        │
                    │  (夜间：IRCUT=OFF, IR灯亮)   │
                    └───────────────┬─────────────┘
                                    │
           LumY >= N2D阈值 / Lux > 10 / bN2D=TRUE
                                    ↓
                          ┌─────────────────┐
                          │  N2D 切换动作    │
                          │  1. 加载白天IQ   │
                          │  2. 彩色模式     │
                          │  3. IRCUT ON    │
                          │  4. IR LED OFF  │
                          │  5. 更新阈值     │
                          └────────┬────────┘
                                    │
                                    └── 回到 BRIGHT
```

---

## 十、文件与函数速查

| 文件 | 关键函数 | 职责 |
|------|---------|------|
| `internal/aov/st_common_aov.c` | `ST_Common_AovSetLowFps/HighFps` | 帧率切换 |
| `internal/aov/st_common_aov.c` | `ST_Common_AovISPAdjust_HWLightSensor` | 硬光敏日夜判断 |
| `internal/aov/st_common_aov.c` | `ST_Common_AovISPAdjust_SWLightSensor` | 软光敏日夜判断 |
| `internal/aov/st_common_aov.c` | `ST_Common_AovEnterSuspend` | 系统挂起 |
| `internal/fast_ae/fast_ae.c` | `ST_Common_FastAE_Run` | FastAE 入口 |
| `internal/fast_ae/fast_ae.c` | `ST_Common_DoFastAE` | FastAE 执行 |
| `internal/fast_ae/fast_ae.c` | `ST_Common_FastAE_CheckDNChange` | FastAE 后检测 D/N 变化 |
| `internal/light_misc_control/light_misc_control_api.c` | `Dev_Light_Misc_Device_*` | 用户态光控接口 |
| `aov/light_misc_control/driver/light_misc_control_main.c` | `SSTAR_Light_Misc_Control_IOCTL_*` | 内核 ioctl 处理 |
| `aov/light_misc_control/driver/light_misc_control_hw.c` | `Hw_Set_Ircut_State` / `Hw_Set_LEDIR_Status` / `Hw_GetLux` | 硬件操作 |
| `modules/sensor/ir/irlight.cpp` | `setRelight()` / `setChargeStatus()` | 本项目 IR 控制 |
| `modules/hdi/src/hdi_video/hdi_vi.c` | `_VI_IspSwLightSensor` | 本项目软光敏检测 |

---

## 十一、`light_misc_control` 内核驱动深度分析（新增）

### 11.1 整体文件架构

```
aov/light_misc_control/driver/
├─ st_light_misc_control_driver.c   ← 平台驱动注册、miscdevice、ioctl 分发、PM 钩子
├─ light_misc_control_main.c        ← 核心业务逻辑（Init/DeInit/SetAttr/帧回调）
├─ light_misc_control_hw.c          ← 硬件抽象（I2C 光感读写、GPIO/PWM 控灯、IRCUT 控制）
├─ light_misc_control_i2c.c         ← I2C 读写封装（A8D8 格式）
├─ light_misc_control_hw.h          ← 内核态数据结构定义
├─ light_misc_control_main.h        ← 模块内部接口声明
└─ module.mk                        ← 编译配置（默认启用 HRTIMER + MULTI_VIFDEVICE）

共享头文件（用户/内核两用）：
internal/light_misc_control/
├─ light_misc_control_datatype.h    ← ioctl cmd 定义、枚举、公共结构体
└─ light_misc_control_api.h         ← 用户态 API 声明
```

### 11.2 驱动注册与设备节点

```c
// platform driver：DTS compatible = "sstar,light_misc_control"
// 在 probe 时从 DTS 读取资源配置
sstar_light_misc_control_probe()
  → SSTAR_Light_Misc_Control_Resource_Config(pdev)
      → of_property_read: lightsensor-i2c, ir-ctrlmode, ir-pad, ircut-pad
      → SSTAR_Light_Misc_Control_Hw_SetResource()  // 保存到 gDeviceResource

// miscdevice：设备节点 /dev/light_misc（动态分配 minor）
misc_register(&light_misc_control_miscdev)
  → fops: open / release / ioctl / read(debug) / write(debug shell)
```

**模块初始化顺序：**

```
module_init
  → platform_driver_register()   // 触发 probe，读 DTS 配置
  → misc_register()              // 创建 /dev/light_misc
  → SSTAR_Light_Misc_Control_Init()
      → CamOsMemAlloc(pLightState)   // 全局状态分配
      → Hw_Resource_PowerOn()        // 上电光感 I2C，申请 GPIO/PWM
```

### 11.3 ioctl 接口完整映射

| ioctl cmd | 方向 | 参数类型 | 内核处理 |
|-----------|------|---------|---------|
| `IOCTL_LIGHT_MISC_CONTROL_INIT` | R/W | `SSTAR_Light_Misc_Callback_Param_t` | 初始化状态，返回 VIF framedone 回调指针 |
| `IOCTL_LIGHT_MISC_CONTROL_DEINIT` | - | - | 销毁线程/hrtimer，重置状态 |
| `IOCTL_LIGHT_MISC_CONTROL_SET_ATTR` | W | `SSTAR_Light_Ctl_Attr_t` | 设置灯光控制模式 |
| `IOCTL_LIGHT_MISC_CONTROL_GET_ATTR` | R | `SSTAR_Light_Ctl_Attr_t` | 读取当前灯光配置 |
| `IOCTL_LIGHT_MISC_CONTROL_SET_IRCUT` | W | `int (SSTAR_Switch_State_e)` | 设置 IRCUT 状态 |
| `IOCTL_LIGHT_MISC_CONTROL_GET_LIGHTSENSOR` | R | `int` | 读取光感 Lux 值 |
| `IOCTL_LIGHT_MISC_CONTROL_GET_TIGMODE` | R | `int` | 读取当前 TIG 积分时间模式 |

### 11.4 Init 回调注册机制（关键设计）

```
用户层调用 Dev_Light_Misc_Device_Init(fd, vifDevId)
    ↓ ioctl IOCTL_LIGHT_MISC_CONTROL_INIT
内核 SSTAR_Light_Misc_Control_IOCTL_Init()
    → 创建 hrtimer（或 kthread）
    → 调用 SSTAR_Light_Misc_Control_Get_Vif_EventPtr()
        → 返回 FrameDone_CallBack 函数指针地址
    ← 通过 copy_to_user 返回 fun_ptr_addr
用户层收到 fun_ptr_addr
    ↓
MI_VIF_CustFunction(vifDevId,
    E_MI_VIF_CUSTCMD_FRAMEEND_NOTIFY,
    sizeof(unsigned long), &fun_ptr_addr)
    → 将内核函数指针注册到 VIF 硬件中断链
```

**设计要点：** 函数指针从内核穿越到用户空间再传回内核，避免了内核模块直接依赖 MI_VIF，保持了驱动的独立性和可移植性。

### 11.5 MULTI_FRAME 帧控模式时序分析

```
系统从 suspend 唤醒（例如 PIR 触发）
        ↓
PM resume_noirq 回调（最早的恢复阶段，中断未完全恢复）
        ↓
SSTAR_Light_Misc_Control_Resume_Notify_Main()
  if controlType == MULTI_FRAME:
    hrtimer_start(delayOpenTimeMs)     ← 启动定时器，延迟开灯
        ↓ 等待 delayOpenTimeMs ms（建议 < 15ms）
hrtimer 回调 light_misc_control_resume_timer_fn()
    → Hw_Set_LEDIR_Status(ON, lightType, lightIntensity)   ← 开灯
        ↓
Sensor 开始曝光（此时灯已稳定）
        ↓
VIF 处理一帧完成，触发帧结束中断
        ↓
SSTAR_Light_Misc_Control_FrameDone_CallBack(bDoneFlag=TRUE)
    → Hw_Set_LEDIR_Status(OFF, lightType, 0)               ← 关灯
    → 如果另一类型灯也开着，一并关闭（同步关灯）
        ↓
系统再次进入 suspend（灯已关，省电）
```

**关键约束（来自 ReadMe）：**
- `resume_noirq` 到 `Sensor exposure` 之间经验值约 15ms
- 若灯光收敛时间 > 15ms，可能出现画面前几行过暗（曝光开始时灯还未稳定）
- 因此 `delayOpenTimeMs` 要足够小，且所用灯的物理响应时间也要足够快

### 11.6 多 VIF 设备支持（LIGHT_SUPPORT_MULTI_VIFDEVICE）

```c
// 场景：双目摄像头，两个 VIF 设备同时工作
// 问题：两个 VIF 帧结束时间不同步，先到达的不能关灯
// 方案：维护 vifDeviceStateQueue 列表，记录每个 vifDev 的完成状态
//       只有所有 vifDev 都回调 bDoneFlag=TRUE 才关灯

FrameDone_CallBack(vifDevId, bDoneFlag=TRUE)
  → VifDevIdList_Fun(COUNT_DOING_CNT, vifDevId)
      → 将此 vifDev 标记为完成
      → 统计还有几个 vifDev 未完成（doingCnt）
  → 若 doingCnt > 0：return  // 还有设备未完成，继续等待
  → 若 doingCnt == 0：关灯   // 所有设备都完成了
```

### 11.7 硬件资源数据结构

```c
// 全局内核状态（单例）
typedef struct SSTAR_Light_Device_State_s {
    bool                   bDeviceHasInited;    // 是否初始化
    SSTAR_Light_Ctl_Attr_t stLight_Ctl_Attr;    // 当前灯光控制参数
    SSTAR_Switch_State_e   eIRcutState;          // IRCUT 当前状态（含 KEEP 位）
    SSTAR_Switch_State_e   eIRState;             // IR LED 状态
    SSTAR_Switch_State_e   eLEDState;            // 白光 LED 状态
    int                    reciveVifEventCnt;    // VIF 帧回调计数
    int                    doneFlagCnt;          // 帧控关灯次数
    int                    openLightCnt;         // 帧控开灯次数
    CamOsSpinlock_t        switchStateSpinlock;  // 保护 IR/LED 状态的自旋锁
    struct hrtimer         hrTimer;              // 延迟开灯定时器
    unsigned int           u32LuxVaule;          // 最近一次 Lux 读值
    int                    pid;                  // 初始化进程 PID（用于 DeInit 鉴权）
} SSTAR_Light_Device_State_t;

// 硬件资源配置（来自 DTS）
typedef struct SSTAR_Light_Device_Resource_s {
    u32 u32I2cNum;           // I2C 总线号
    u32 u32IrCutGpioId[2];  // IRCUT 两路 GPIO
    SSTAR_Light_Device_Controller_t IrCtrl;   // IR LED 控制器（GPIO/PWM）
    SSTAR_Light_Device_Controller_t LedCtrl;  // 白光 LED 控制器
} SSTAR_Light_Device_Resource_t;
```

### 11.8 IRCUT 状态机与防烧毁机制

```c
// IRCUT 使用双极步进电机驱动，有三个有效状态：
E_SWITCH_STATE_ON    // 正转到 ON 位（白天：截断红外）
E_SWITCH_STATE_OFF   // 反转到 OFF 位（夜间：透过红外）
E_SWITCH_STATE_KEEP  // 两路 GPIO 均为 0，释放线圈电流

// 防烧毁逻辑：
if (当前 IRcutState == 目标 state) → 跳过（已在目标位置，不重复驱动）
// 原因：步进电机已到限位时若继续同方向通电 → 线圈持续发热 → 烧毁

// KEEP 状态特殊处理：
//   使用第 4 位（E_SWITCH_STATE_KEEP = 8）叠加记录当前 keep 之前的实际位置
//   eIRcutState = E_SWITCH_STATE_KEEP | 之前的 ON/OFF 状态
//   下次判断时用 eIRcutState & (~KEEP) 还原真实位置

// 标准操作序列（user 层）：
Set_Ircut(ON)              // 驱动电机正转
usleep(100ms)              // 等待电机到位
Set_Ircut(E_SWITCH_STATE_KEEP)  // 释放线圈
```

### 11.9 光感 I2C 寄存器操作

```c
// 光感芯片寄存器（8位地址，8位数据，A8D8 格式）
reg[0x03]: 0x04 = 上电；0x06 = 断电
reg[0x04]: TIG 积分时间
    0x25 = 100ms（tig_mode=0，默认）
    0x94 = 400ms（tig_mode=1）
    0xFF = 688.5ms（tig_mode=2，无对应光表）

reg[0x20]: bit0 = 数据就绪标志（1 = 可读）
reg[0x21~0x22]: chn0 低/高字节（可见光 + 红外）
reg[0x23~0x24]: chn1 低/高字节（红外）
reg[0x05]: 增益寄存器（低4位 = chn0增益，高4位 = chn1增益）

// Lux 计算公式：
lux = (chn0 * 375 / gain_l - chn1 * 375 / gain_h) / 1000
// 若 chn0 == 65535（饱和）：
lux = chn0 * 375 / gain_l / 1000
// 差分消除红外分量，得到可见光 Lux
```

### 11.10 编译配置选项（module.mk）

| 宏定义 | 默认 | 说明 |
|--------|------|------|
| `LIGHT_USE_HRTIMER` | **开启** | 用 hrtimer 触发开灯（精度高，在中断上下文）；否则用 kthread（精度低但可睡眠） |
| `LIGHT_SUPPORT_MULTI_VIFDEVICE` | **开启** | 支持多 VIF 设备同步关灯 |
| `LIGHT_SENSOR_ONLY` | 关闭 | 纯光感模式，屏蔽 IR LED / IRCUT 所有代码 |
| `LIGHT_USE_PM_NOTIFY` | 关闭 | 用 pm_notifier 替代 platform PM 钩子获取挂起/恢复事件 |
| `LIGHT_SUPPORT_LIGHTSENSOR_POWEROFF` | 关闭 | STR 期间对光感断电（省电但恢复需重新等 TIG 积分时间） |

### 11.11 调试接口（shell 命令）

```bash
# 读当前状态（cat）
cat /dev/light_misc
# 输出示例：
# controlType:2 lightType:0 delayOpenTimeMs:20 lightIntensity:0
# eIRcutState:0 eIRState:0 eLEDState:0 reciveVifEventCnt:5 doneFlagCnt:5 openLightCnt:5

# echo 命令（写）：
echo init > /dev/light_misc                    # 手动初始化（无 framedone 注册）
echo getlux > /dev/light_misc                  # 读 Lux（结果在 kmsg）
echo setircut on > /dev/light_misc             # IRCUT ON
echo setircut off > /dev/light_misc            # IRCUT OFF（之后需手动发 keep）
echo setlight ir on > /dev/light_misc          # IR LED 长期开
echo setlight ir off > /dev/light_misc         # IR LED 长期关
echo setlight ir multi 20 > /dev/light_misc    # 帧控模式，延迟 20ms 开灯
echo setlight led multi 0 > /dev/light_misc    # 白光帧控，无延迟
echo debuglog on > /dev/light_misc             # 开启帧控 debug 日志（默认关以免中断耗时）
```

**注意**：`echo init` 不注册 VIF framedone，帧控模式下无法自动关灯（灯会一直亮到断电）。

### 11.12 文件关闭时自动 DeInit

```c
light_misc_control_dev_release()
  → 读取 pstFileHandle->private（SSTAR_Light_Private_t）
  → 调用 ptrDeinitFun(false, pid)
      = SSTAR_Light_Misc_Control_IOCTL_DeInit(false, pid)
```

进程崩溃或异常退出时，内核会自动触发 release，确保灯光和 hrtimer 被正确释放，**不会因进程崩溃导致灯一直亮着**。
