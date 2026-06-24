# Bug Report：日志 Prune 导致 motionLoop / taskLoop 长时间阻塞

**模块**：`modules/common/log/logger.cpp`
**发现版本**：navigation_20260609_174128
**严重等级**：高（机器失控）
**状态**：已修复

---

## 现象

机器在执行 `pet_follow` 任务时，突然停止响应 ToF 避障检测，以 0.8 m/s 速度径直撞上障碍物。

日志中出现两条相邻的极端 overrun：

```
[2026-06-09 17:40:35.235770] [W] motionLoop overrun: 6527ms
[2026-06-09 17:40:35.237627] [W] taskLoop  overrun: 6431ms
```

overrun 期间机器没有停止运动——电机保持最后一次速度指令（0.8 m/s），且 ToF PATH_BLOCKED 检测未被执行，最终碰撞。

---

## 根本原因

### 调用链

```
任意线程调用 NLOG_INFO / NLOG_WARN
  → spdlog sink::log()
    → BudgetedRotatingFileSink::log()          [logger.cpp:289]
      → std::lock_guard lock(LogFileOperationMutex())   ← 获取全局锁
        → sink_->log(msg)                               ← 写文件
        → budget_->MaybePrune(payload_size + 128)       ← 在锁内调用 ← 问题所在
          → PruneLocked()
            → filesystem::recursive_directory_iterator  ← 全目录扫描
            → filesystem::remove(...)                   ← 删除旧日志文件
```

### 为什么会阻塞 6 秒

`MaybePrune` 每积累写入 1 MB 触发一次 `PruneLocked()`，后者执行：

1. `std::filesystem::recursive_directory_iterator` 遍历 `/data/log` 全目录
2. 对超出预算的旧文件调用 `filesystem::remove()`

在嵌入式 Linux（SigmaStar SSC305）的 flash 文件系统上，此操作实测可阻塞数秒。

### 为什么所有线程都卡住

`LogFileOperationMutex()` 是进程内全局单例 mutex。`MaybePrune` 在持有该锁期间执行，所有后续调用 `BudgetedRotatingFileSink::log()` 的线程（包括 `motionLoop`、`taskLoop`）都会阻塞在锁竞争上，直到 prune 完成。

---

## 影响

| 线程 | 周期 | overrun 后果 |
|---|---|---|
| `motionLoop` (nav.motion) | 30 ms | 停止调用 `execute()`，电机保持最后速度指令 |
| `taskLoop` (nav.task) | 100 ms | 停止调用 `tick()`，ToF PATH_BLOCKED 检测不执行 |
| `emergencyLoop` (nav.emergency) | 50 ms | 同样依赖日志输出，也受影响 |

结果：机器在无控制的状态下运动 6.5 秒，最终碰撞。

---

## 修复

**文件**：`modules/common/log/logger.cpp`，`BudgetedRotatingFileSink::log()`

**修改前**：

```cpp
void log(const spdlog::details::log_msg &msg) override {
    std::lock_guard<std::mutex> lock(LogFileOperationMutex());
    sink_->log(msg);
    if (budget_) {
        budget_->MaybePrune(msg.payload.size() + 128);  // 在全局锁内执行目录扫描
    }
}
```

**修改后**：

```cpp
void log(const spdlog::details::log_msg &msg) override {
    size_t payload_size = msg.payload.size();
    {
        std::lock_guard<std::mutex> lock(LogFileOperationMutex());
        sink_->log(msg);   // 写文件后立即释放全局锁
    }
    // MaybePrune 有自己的内部 mutex_，无需 LogFileOperationMutex 保护
    if (budget_) {
        budget_->MaybePrune(payload_size + 128);
    }
}
```

`MaybePrune` 内部使用 `LogBudgetEnforcer::mutex_`（独立 per-instance 锁），线程安全不依赖 `LogFileOperationMutex`。将其移至全局锁外，目录扫描即使耗时 6 秒也不会阻塞任何其他线程的写日志操作。

---

## 验证建议

1. **压力测试**：以较高日志输出频率（info 级，navigation + perception 全开）持续运行 10 分钟，观察 `/data/log` 超过 12 MB 预算时是否再出现 motionLoop overrun。
2. **Prune 计时**：在 `PruneLocked()` 入口处加 tic/toc，确认嵌入式设备上实际耗时。
3. **线程检查**：用 `strace -p <pid> -e trace=file` 在 prune 期间确认不再有其他线程在 `openat/write`。

---

## 附：触发时刻日志片段

```
[17:40:28.679] publishPath navi/lookahead: [0.51,20.54][-0.68,20.35]   ← 最后一条正常日志
[17:40:35.235] !!! motionLoop overrun: 6527ms                           ← 卡住 6.556 秒后恢复
[17:40:35.237] !!! taskLoop  overrun: 6431ms
[17:40:41.085] pet_follow: TOF obstacle 0.143m < 0.30m, PATH_BLOCKED   ← 恢复后才检测到障碍
```

距离碰撞已来不及刹停。
