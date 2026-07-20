---
doc_type: plan
knowledge_type: decision
maturity: verified
created: 2026-05-08
last_updated: 2026-05-12
related: []
id: pcr02-irlight-optimization-plan-archive-20260508
title: IR 补光与光敏控制优化计划
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/plans/2026-05-08-irlight-optimization-plan.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: plans/2026-05-08-irlight-optimization-plan.md
  source_sha256: 521b951ead6298fc8bd19b057988b66f4951795b1c3a3d0d9de2eb5dec1ecd18
review_after: '2026-10-16'
review_status: archive-only-historical-provenance
promotion: none
promotion_decision: none; archived historical IR/light-sensor plan only, no active promotion and not current calibration policy
tags:
- pcr02
- archive-only
- historical-plan
- no-active-promotion
- irlight
- optimization
validation_refs:
- projects/xcrz-sigmastar-demo/archive/plans/2026-05-08-irlight-optimization-plan.md
- rtk bash tools/knowledge-check.sh --dry-run
created_at: '2026-06-16'
updated_at: '2026-07-11'
summary_zh: 归档 2026-05-08 IR 补光与光敏控制优化计划；仅作历史优化计划 provenance，不代表当前标定策略、当前硬件事实或 active 控制规则。
---

# IR 补光与光敏控制优化计划

> 归档说明：本文为历史计划，未勾选步骤不代表当前待办；重新执行前必须重新核对源码、构建脚本和验证命令。

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 修复 IR 补光控制的两个关键 Bug（线程阻塞、ColorToGray 缺失），并完成四项改进（ADC 迟滞、IQ 路径可配置、SW 阈值标定流程、充电切换状态同步）。

**架构：** 当前项目采用 `irlight.cpp`（上层控制）+ `hdi_vi.c`（SW光敏检测） + `sensor_serial.cpp`（充电状态路由）三层分工。SW光敏回调从 VENC 读帧线程调用 `setRelight()`（含 150ms 阻塞），需异步解耦。

**技术栈：** C++17、Sigmastar MI API（`MI_ISP_IQ_SetColorToGray`、`MI_ISP_AE_*`）、TOML 配置（待引入）

---

## 分析：当前实现 vs Sigmastar 官方方案

| 维度 | 当前实现 | 官方 sigmastar example | 差距 |
|------|----------|----------------------|------|
| IRCUT 驱动 | `VSHDIIRCUT_SetState()` → 内部已含 150ms delay + GPIO(0,0) KEEP | `Dev_Light_Misc_Device_Set_Ircut()` + 显式 100ms + KEEP | **已正确**，无需修改 |
| ColorToGray | SW光敏路径（hdi_vi.c 回调前）调用；**HW光敏路径未调用** | 两路均调用 | **BUG** |
| SW光敏回调线程安全 | 在 VENC 读帧线程内同步调用 `setRelight()`（含 DelayMs 1500ms） | 在独立线程中处理 | **BUG** |
| IQ 文件路径 | irlight.cpp 硬编码 sc5336P 路径 | 上层传入路径，不硬编码 | 改进 |
| ADC 光敏迟滞 | NIGHT=15, DAY=20，差值 5 | `u32DiffLux` 过滤微小变化 | 改进 |
| SW 光敏阈值 | 600/800/1200/1500（估算值） | 根据实际光感特性标定 | 改进 |
| 充电切换状态同步 | SW→HW 切换时 `g_eCurrentLight`（hdi_vi.c）与 `m_isNight`（irlight）可能不一致 | 单一状态源 | 改进 |

---

## 涉及文件

| 文件 | 职责变更 |
|------|---------|
| `modules/sensor/ir/irlight.h` | 增加 IQ 路径配置接口；调整 SW 阈值常量；添加 `m_pendingNight` 异步信号量 |
| `modules/sensor/ir/irlight.cpp` | Bug Fix：workerThread 处理 SW 回调信号；`setRelight()` 补充 ColorToGray；抽取 IQ 路径配置 |
| `modules/hdi/include/hdi_vi.h` | 新增 `VSHDIVI_IspSetColorToGray(VS_BOOL bGray)` 公开接口声明 |
| `modules/hdi/src/hdi_video/hdi_vi.c` | 实现 `VSHDIVI_IspSetColorToGray()`；无其他改动 |

---

## 任务 1：修复 Bug — SW 光敏回调在 VENC 线程中阻塞

**问题：** `_VI_IspSwLightSensor()` 在 VENC H26x 主码流读帧线程中运行（`hdi_vi.c:3606`）。日夜切换时触发 `onDayNightStateCallback` → `setRelight()` → `VSHDIIRCUT_SetState()` 内含 `DelayMs(150)`，加上速率限制最高再等 1500ms，共可能阻塞约 1.65 秒，导致视频帧积压和时序异常。

**解决方案：** `onDayNightStateCallback` 只写原子信号，唤醒 `workerThread`，由 workerThread 真正执行 `setRelight()`。

**文件：**
- 修改：`modules/sensor/ir/irlight.h`
- 修改：`modules/sensor/ir/irlight.cpp`

- [ ] **步骤 1：在 `irlight.h` 添加待处理夜间状态的原子信号量**

在 `// 环境光检测` 注释区域（约第 88 行）添加私有成员：

```cpp
    std::atomic<int>  m_pendingNight{-1};  // -1=无待处理, 0=待切白天, 1=待切夜间
```

- [ ] **步骤 2：修改 `onDayNightStateCallback` 只发信号，不直接调 `setRelight`**

```cpp
// irlight.cpp
VS_S32 IrLight::onDayNightStateCallback(VS_BOOL bIsNight) {
    IrLight &ir = IrLight::instance();
    ir.m_pendingNight.store(bIsNight == VS_TRUE ? 1 : 0, std::memory_order_relaxed);
    ir.m_cv.notify_one();
    return VS_SUCCESS;
}
```

- [ ] **步骤 3：修改 `workerThread` 处理 `m_pendingNight`**

在 `workerThread` 的循环体（约 `VSHDIOS_DelayMs(100)` 之前）添加：

```cpp
// 处理 SW 光敏日夜切换请求（来自 VENC 线程的异步信号）
int pending = m_pendingNight.exchange(-1, std::memory_order_relaxed);
if (pending >= 0) {
    setRelight(pending == 1);
}
```

完整的 workerThread 循环修改后结构：

```cpp
void IrLight::workerThread() {
    SetCurrentThreadName("sensor_ir0");
    auto        now       = std::chrono::steady_clock::now();
    static auto lastCheck = now;

    while (m_running) {
        {
            std::unique_lock<std::mutex> lock(m_mutex);
            if (!m_autoUpdate.load() && m_running) {
                updateLight(m_LightMode);
                m_cv.wait(lock, [this] {
                    return m_autoUpdate.load() || !m_running || m_pendingNight.load() >= 0;
                });
                lastCheck = std::chrono::steady_clock::now();
                continue;
            }
        }

        // 处理 SW 光敏异步信号
        int pending = m_pendingNight.exchange(-1, std::memory_order_relaxed);
        if (pending >= 0) {
            setRelight(pending == 1);
        }

        now = std::chrono::steady_clock::now();
        if (now - lastCheck > std::chrono::milliseconds(500)) {
            lastCheck = now;
            updateLight(getLightMode());
        }

        VSHDIOS_DelayMs(100);
    }

    setRelight(false);
}
```

- [ ] **步骤 4：验证非 AUTO 模式下 SW 回调也能唤醒 workerThread**

非 AUTO 模式（手动开/关）时 workerThread 阻塞在 `m_cv.wait()`，`notify_one()` 能正确唤醒并处理 pending，然后继续阻塞。验证方式：

```bash
# 设置手动夜间模式后，模拟一次从 SW 光敏触发的切换
# 观察 journalctl / logcat，确认 setRelight 不在 VENC 线程中执行
grep "sensor_ir0" /tmp/app.log | grep "setRelight\|IrLight"
```

- [ ] **步骤 5：Commit**

```bash
git add modules/sensor/ir/irlight.h modules/sensor/ir/irlight.cpp
git commit -m "fix(irlight): 解耦 SW 光敏回调，改为异步信号通知 workerThread，避免阻塞 VENC 读帧线程"
```

---

## 任务 2：修复 Bug — HW 光敏路径缺少 ColorToGray 切换

**问题：** `setRelight(isnight)` 被 ADC 硬光敏（HW路径）直接调用时，没有调用 `MI_ISP_IQ_SetColorToGray()`，导致夜间模式下画面仍为彩色，且 SW 光敏路径通过 hdi_vi.c 回调前已处理，两条路径行为不一致。

**解决方案：** 在 `hdi_vi.h/c` 暴露 `VSHDIVI_IspSetColorToGray()`，在 `setRelight()` 中统一调用。

**文件：**
- 修改：`modules/hdi/include/hdi_vi.h`
- 修改：`modules/hdi/src/hdi_video/hdi_vi.c`
- 修改：`modules/sensor/ir/irlight.cpp`

- [ ] **步骤 1：在 `hdi_vi.h` 声明新接口**

在 `VSHDIVI_IspSetSWLightSensor` 声明行之后添加：

```c
VS_S32 VSHDIVI_IspSetSWLightSensor(VS_BOOL bEnable);
VS_S32 VSHDIVI_IspSetColorToGray(VS_BOOL bGray);   // 新增
```

- [ ] **步骤 2：在 `hdi_vi.c` 实现该函数**

在 `VSHDIVI_IspSetSWLightSensor` 实现之后添加：

```c
VS_S32 VSHDIVI_IspSetColorToGray(VS_BOOL bGray)
{
    MI_ISP_IQ_ColorToGrayType_t stColorToGray;
    memset(&stColorToGray, 0x0, sizeof(MI_ISP_IQ_ColorToGrayType_t));
    stColorToGray.bEnable = bGray;
    return MI_ISP_IQ_SetColorToGray(ISP_DEV_ID, ISP_CHN_ID, &stColorToGray);
}
```

- [ ] **步骤 3：在 `irlight.cpp` 的 `setRelight()` 中调用**

在 `setRelight()` 中，修改夜间和白天两个分支，在 `VSHDIIRCUT_SetState` 之前添加 ColorToGray 切换：

```cpp
void IrLight::setRelight(bool isnight) {
    VS_CHAR acNightIqPath[] = "/config/iqfile/sc5336P_night_api.bin";
    VS_CHAR acDayIqPath[]   = "/config/iqfile/sc5336P_api.bin";
    const auto now = std::chrono::steady_clock::now();
    if (has_last_set_relight_time_) {
        const auto diff_ms =
            std::chrono::duration_cast<std::chrono::milliseconds>(now - m_last_set_relight_time_).count();
        if (diff_ms < RATE_LIMIT_PERIOD_MILLSEC) {
            const auto wait_ms = static_cast<VS_U32>(RATE_LIMIT_PERIOD_MILLSEC - diff_ms);
            VSHDIOS_DelayMs(wait_ms);
        }
    }

    if (isnight) {
        VSHDIVI_SetIqFilePath(acNightIqPath);
        VSHDIVI_IspSetColorToGray(VS_TRUE);     // 新增：夜间灰度模式
        (VS_VOID) VSHDIIRCUT_SetState(VS_FALSE);
        setLightBrightness(50);
    }
    else {
        (VS_VOID) VSHDIIRCUT_SetState(VS_TRUE);
        setLightBrightness(0);
        VSHDIVI_IspSetColorToGray(VS_FALSE);    // 新增：白天彩色模式
        VSHDIVI_SetIqFilePath(acDayIqPath);
    }

    m_isNight                 = isnight;
    m_last_set_relight_time_  = std::chrono::steady_clock::now();
    has_last_set_relight_time_ = true;

    if (m_useSwSensor.load()) {
        if (isnight) {
            VSHDIVI_IspSetDayNightThreshold(SW_D2N_IR_ON, SW_N2D_IR_ON);
        } else {
            VSHDIVI_IspSetDayNightThreshold(SW_D2N_IR_OFF, SW_N2D_IR_OFF);
        }
    }
}
```

**注意顺序：**
- 切夜间：先换 IQ bin → 灰度 → IRCUT OFF → 开灯（IQ bin 先换，避免 IRCUT 动作期间 ISP 用错参数）
- 切白天：先 IRCUT ON → 关灯 → 彩色 → 换 IQ bin（等 IRCUT 到位后再恢复彩色）

同时**移除 SW 光敏路径（hdi_vi.c）中多余的 ColorToGray 调用**（因为 `setRelight()` 现在统一处理）：

```c
// hdi_vi.c D2N block，删除这两行（setRelight 会处理）：
// stColorToGray.bEnable = TRUE;
// MI_ISP_IQ_SetColorToGray(u32IspDevId, u32IspChnId, &stColorToGray);
```

```c
// hdi_vi.c N2D block，删除这两行（setRelight 会处理）：
// stColorToGray.bEnable = FALSE;
// MI_ISP_IQ_SetColorToGray(u32IspDevId, u32IspChnId, &stColorToGray);
```

**同时删除已无用的局部变量 `stColorToGray`（避免编译告警）。**

- [ ] **步骤 4：验证**

```bash
# 在 setRelight 中添加临时日志，分别触发 HW 和 SW 路径
# 确认两路都打印了 ColorToGray 相关日志
# 白天室内：画面彩色 ✓
# 遮住镜头（黑暗）：画面应变灰度 ✓
grep "ColorToGray\|IspSetColorToGray" /tmp/app.log
```

- [ ] **步骤 5：Commit**

```bash
git add modules/hdi/include/hdi_vi.h \
        modules/hdi/src/hdi_video/hdi_vi.c \
        modules/sensor/ir/irlight.cpp
git commit -m "fix(irlight): 统一 ColorToGray 切换到 setRelight()，修复 HW 光敏路径夜间画面仍彩色的问题"
```

---

## 任务 3：改进 — IQ 文件路径从硬编码改为可配置

**问题：** `setRelight()` 中硬编码了 `sc5336P` 的 IQ bin 路径，更换 sensor 时必须修改代码。

**方案：** 通过 `applyPayload` 或初始化接口注入路径，存储在成员变量中。

**文件：**
- 修改：`modules/sensor/ir/irlight.h`
- 修改：`modules/sensor/ir/irlight.cpp`

- [ ] **步骤 1：在 `irlight.h` 添加路径成员和 `setIqPaths()` 接口**

```cpp
// irlight.h 中 public 接口区域
void setIqPaths(const std::string &dayPath, const std::string &nightPath);

// private 成员
std::string m_iqDayPath   = "/config/iqfile/sc5336P_api.bin";
std::string m_iqNightPath = "/config/iqfile/sc5336P_night_api.bin";
```

- [ ] **步骤 2：实现 `setIqPaths()`**

```cpp
// irlight.cpp
void IrLight::setIqPaths(const std::string &dayPath, const std::string &nightPath) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_iqDayPath   = dayPath;
    m_iqNightPath = nightPath;
}
```

- [ ] **步骤 3：修改 `setRelight()` 使用成员变量路径**

```cpp
// 替换 VS_CHAR acNightIqPath[] = ... 的两行硬编码
if (isnight) {
    VSHDIVI_SetIqFilePath(const_cast<VS_CHAR *>(m_iqNightPath.c_str()));
    // ...
} else {
    // ...
    VSHDIVI_SetIqFilePath(const_cast<VS_CHAR *>(m_iqDayPath.c_str()));
}
```

- [ ] **步骤 4：在初始化时调用 `setIqPaths()`**

找到 `IrLight::instance()` 的调用者（app 层），在调用 `applyPayload()` 之前添加：

```cpp
IrLight::instance().setIqPaths(
    "/config/iqfile/sc5336P_api.bin",
    "/config/iqfile/sc5336P_night_api.bin"
);
```

- [ ] **步骤 5：验证路径正确加载**

```bash
# 日志确认两个路径正确传入
grep "sc5336P\|iqfile" /tmp/app.log | head -5
```

- [ ] **步骤 6：Commit**

```bash
git add modules/sensor/ir/irlight.h modules/sensor/ir/irlight.cpp
git commit -m "refactor(irlight): IQ bin 路径从硬编码改为可通过 setIqPaths() 注入，支持不同 sensor 型号"
```

---

## 任务 4：改进 — ADC 光敏迟滞增强

**问题：** 当前 `NIGHT_THRESHOLD=15, DAY_THRESHOLD=20`，差值仅 5 个 ADC 单位，光线在临界值附近轻微抖动就会造成频繁切换，1500ms 速率限制只是亡羊补牢。

**方案：** 参考 sigmastar `u32DiffLux` 模式，用差值过滤滤除小幅度光线变化，只在光线差异超过阈值时才更新亮度判断。同时适当扩大日夜阈值差距。

**文件：**
- 修改：`modules/sensor/ir/irlight.h`
- 修改：`modules/sensor/ir/irlight.cpp`

- [ ] **步骤 1：修改 `irlight.h` 阈值常量，添加最小差值常量**

```cpp
static constexpr int NIGHT_THRESHOLD   = 10;  // 小于此值进入夜间（扩大迟滞区间）
static constexpr int DAY_THRESHOLD     = 25;  // 大于此值进入白天
static constexpr int ADC_MIN_DIFF      = 3;   // ADC 差值小于此值时忽略（噪声过滤）
```

- [ ] **步骤 2：在 `irlight.h` 添加 `m_lastAdcValue` 成员**

```cpp
std::atomic<int> m_lastAdcValue{-1};  // 上一次有效 ADC 读值（-1 表示未初始化）
```

- [ ] **步骤 3：修改 `updateLight()` 中 AUTO 的 HW 路径加入差值过滤**

```cpp
case LightMode::AUTO: {
    if (m_useSwSensor.load()) {
        break;
    }
    adclight = readAdc();
    if (adclight >= 0) {
        const int lastVal = m_lastAdcValue.load();
        if (lastVal >= 0 && std::abs(adclight - lastVal) < ADC_MIN_DIFF) {
            // 变化过小，忽略本次读值
            publishLight(adclight);
            break;
        }
        m_lastAdcValue.store(adclight);

        double light  = m_filter.comprehensiveFilter(static_cast<double>(adclight));
        adclight      = static_cast<int>(light);
        shouldBeNight = (adclight <= NIGHT_THRESHOLD);
        if (adclight >= DAY_THRESHOLD) {
            shouldBeNight = false;
        }
        publishLight(adclight);
    }
    break;
}
```

- [ ] **步骤 4：在 `init()` 中重置 `m_lastAdcValue`**

```cpp
// init() 中 m_initialized = true 之前添加：
m_lastAdcValue.store(-1);
```

- [ ] **步骤 5：验证阈值效果**

```bash
# 观察光敏发布数据，确认：
# 1. 光线值小幅抖动时不触发切换
# 2. 光线明显变化时正常切换
grep "light_value\|IrLight\|shouldBeNight" /tmp/app.log | tail -30
```

- [ ] **步骤 6：Commit**

```bash
git add modules/sensor/ir/irlight.h modules/sensor/ir/irlight.cpp
git commit -m "improve(irlight): 扩大 HW 光敏日夜迟滞区间，加入 ADC 差值噪声过滤，减少临界光线下的频繁切换"
```

---

## 任务 5：改进 — 充电切换时状态同步

**问题：** 从 SW→HW 切换时（`setChargeStatus(false)`），`g_eCurrentLight`（hdi_vi.c 内部）可能已是 `E_ST_LIGHT_DARK`，但 `m_isNight`（irlight.cpp）可能因历史 ADC 判断而为 `false`，导致 HW 路径一开始就以错误状态运行，直到下一次 ADC 读值才纠正。

**方案：** 在 `setChargeStatus(false)` 时，立即触发一次 ADC 读值，用当前读值重置 `m_lastAdcValue` 并立即执行一次 `updateLight()`。

**文件：**
- 修改：`modules/sensor/ir/irlight.cpp`

- [ ] **步骤 1：修改 `setChargeStatus()` 切回 HW 时立即执行一次 ADC 判断**

```cpp
void IrLight::setChargeStatus(bool isCharging) {
    const bool prev = m_useSwSensor.exchange(isCharging);
    if (prev == isCharging) {
        return;
    }

    if (isCharging) {
        SENSOR_LOG_INFO("IrLight: switch to SW light sensor (camera)");
        const VS_U32 d2n = m_isNight.load() ? SW_D2N_IR_ON : SW_D2N_IR_OFF;
        const VS_U32 n2d = m_isNight.load() ? SW_N2D_IR_ON : SW_N2D_IR_OFF;
        VSHDIVI_IspSetDayNightThreshold(d2n, n2d);
        VSHDIVI_IspSetSWLightSensor(VS_TRUE);
    } else {
        SENSOR_LOG_INFO("IrLight: switch to HW light sensor (ADC)");
        VSHDIVI_IspSetSWLightSensor(VS_FALSE);
        // 切回 HW 时立即重置历史 ADC，下次 workerThread 循环时强制更新
        m_lastAdcValue.store(-1);
        // 唤醒 workerThread 立即执行一次 ADC 判断（而不等 500ms 周期）
        m_cv.notify_one();
    }
}
```

- [ ] **步骤 2：验证切换后状态一致**

```bash
# 场景：夜间 SW 光敏模式（isNight=true），拔掉充电线 → HW 光敏接管
# 期望：HW 立即读 ADC，若读值确认是夜间则 m_isNight 维持 true，否则执行切换
grep "switch to HW\|switch to SW\|setRelight\|isNight" /tmp/app.log | tail -10
```

- [ ] **步骤 3：Commit**

```bash
git add modules/sensor/ir/irlight.cpp
git commit -m "fix(irlight): SW→HW 切换时重置 ADC 历史并立即触发一次状态同步，避免初期状态不一致"
```

---

## 任务 6：改进 — SW 光敏阈值标定流程文档（不改代码）

**问题：** SW 光敏阈值（`SW_D2N_IR_OFF=600` 等）是估算值，实际 `u32LumY` 范围因 sensor 型号、IQ bin 配置、镜头透光率而异，必须在硬件上实测。

**目标：** 输出一份可操作的阈值标定 SOP，让测试工程师按步骤操作即可得到合适阈值。

**文件：**
- 创建：`docs/irlight-sw-threshold-calibration.md`

- [ ] **步骤 1：创建标定文档**

文件路径：`docs/irlight-sw-threshold-calibration.md`

内容要点（按步骤编写，非模板——实际创建时需完整撰写）：

```markdown
# SW 光敏阈值标定流程

## 前置条件
- 设备连接充电器（u8Status=1，启用 SW 光敏）
- 访问 hdi_vi.c 的 debug 输出（g_bEnableDebugLog 或 DBG_INFO 已开启）
- 使用标准光源（色温 3200K，照度可调）

## 步骤 1：获取正常白天的 LumY 基准值
1. 光源设置到 500-1000 Lux（正常室内照明）
2. IR 灯关闭（白天状态）
3. 等待 ISP AE 稳定（bIsStable=TRUE，约 2-5 秒）
4. 记录 3 次 LumY 值，取平均 → 这是"白天基准 LumY"

## 步骤 2：确定 D2N（日转夜）阈值（IR 灯关时）
1. 逐步降低光源照度（500→200→100→50→20 Lux）
2. 每档等 AE 稳定后记录 LumY
3. 在人眼刚刚感觉到"偏暗，应该开灯"时的 LumY → SW_D2N_IR_OFF
4. 建议取该值再降低 10% 作为安全裕量

## 步骤 3：确定 N2D（夜转日）阈值（IR 灯开时）
1. 先开启 IR 灯（模拟夜间补光状态）
2. 逐步提高光源照度（5→20→50→100 Lux）
3. 每档等 AE 稳定后记录 LumY
4. 在"自然光明显足够，可以关闭 IR 灯"时的 LumY → SW_N2D_IR_ON
5. 建议 SW_N2D_IR_ON = SW_D2N_IR_OFF × 1.3~1.5（确保迟滞）

## 步骤 4：确定 IR 灯关时的 N2D 阈值
1. 关闭 IR 灯
2. 重复步骤 3，从夜间无补光恢复到白天
3. 记录 LumY → SW_N2D_IR_OFF

## 参考值填表
| 常量 | 含义 | 实测值 | 当前估算值 |
|------|------|--------|-----------|
| SW_D2N_IR_OFF | IR灯灭时日转夜阈值 | ___ | 600 |
| SW_N2D_IR_OFF | IR灯灭时夜转日阈值 | ___ | 800 |
| SW_D2N_IR_ON  | IR灯亮时日转夜阈值 | ___ | 1200 |
| SW_N2D_IR_ON  | IR灯亮时夜转日阈值 | ___ | 1500 |

## 更新代码
将实测值更新到 `modules/sensor/ir/irlight.h`:
static constexpr VS_U32 SW_D2N_IR_OFF = <实测值>;
static constexpr VS_U32 SW_N2D_IR_OFF = <实测值>;
static constexpr VS_U32 SW_D2N_IR_ON  = <实测值>;
static constexpr VS_U32 SW_N2D_IR_ON  = <实测值>;
```

- [ ] **步骤 2：Commit**

```bash
git add docs/irlight-sw-threshold-calibration.md
git commit -m "docs(irlight): 新增 SW 光敏阈值标定 SOP，指导测试工程师完成实测标定"
```

---

## 自检

### 规格覆盖度

| 问题 | 对应任务 |
|------|---------|
| VENC 线程被 setRelight 阻塞 | 任务 1 ✓ |
| HW 路径无 ColorToGray | 任务 2 ✓ |
| IQ 路径硬编码 | 任务 3 ✓ |
| ADC 迟滞不足 | 任务 4 ✓ |
| 充电切换状态不同步 | 任务 5 ✓ |
| SW 阈值未标定 | 任务 6 ✓ |
| IRCUT KEEP 状态 | 已确认 `VSHDIIRCUT_SetState()` 内部已实现（150ms delay + GPIO 0,0），无需修改 ✓ |

### 已知不在本计划范围内的项目

- FastAE：本项目不是 AOV 摄像机，不需要低功耗 1fps 模式
- MULTI_FRAME 补光：同上
- `/dev/light_misc` 驱动迁移：当前 HDI 层已封装足够，迁移成本高、收益低

### 类型一致性

- 任务 1 中 `m_pendingNight` 类型为 `std::atomic<int>`，在任务 5 中 `m_lastAdcValue` 类型也为 `std::atomic<int>`，一致 ✓
- 任务 2 的 `VSHDIVI_IspSetColorToGray(VS_BOOL)` 在任务 3 的 `setRelight()` 中调用，签名匹配 ✓
- 任务 3 的 `m_iqDayPath` 类型 `std::string`，传入 `VSHDIVI_SetIqFilePath()` 时需要 `const_cast<VS_CHAR *>(m_iqDayPath.c_str())`，已在步骤 3 中说明 ✓
