---
id: pcr02-camera-whiteout-ae-exposure-analysis-20260703
title: PCR02 摄像头老化后白屏的 AE/ISP 初步分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
status: reviewing
owner: team-core
created_at: 2026-07-03
updated_at: 2026-07-15
review_after: 2026-10-03
tags:
  - pcr02
  - camera
  - isp
  - ae
  - awb
  - sensor
  - whiteout
  - aging
  - sw-light-sensor
  - manual-exposure
  - charging-auto
---

# PCR02 摄像头老化后白屏的 AE/ISP 初步分析

## Source

- 来源：2026-07-03 Codex 会话中的现场排障摘要。
- 补充来源：2026-07-15 现场确认、应用源码 Git 时间线和本地制品只读检查。
- 相关仓库：`xcrz_sigmastar_demo`
- 相关模块：
  - `modules/hdi/src/hdi_video/hdi_vi.c`
  - `modules/hdi/src/hdi_plat_ss/ssplat_isp.c`
  - `modules/sensor/ir/irlight.cpp`
- 现场材料边界：本记录只保存脱敏分析和下次采集计划，不复制原始日志、设备私有地址、客户材料或二进制制品。

## Symptom

老化过程中摄像头从正常显示变为白色画面。摄像头仍在出图，不是完全掉线。降温后不恢复，说明不像单纯热失效。重启 camera 后画面恢复正常，说明更像运行态 ISP/AE/sensor 状态异常，而不是硬件永久故障或 IQ 文件损坏。

现场补充现象：

- 手指遮住摄像头时画面偏红。
- 移开手指后画面又变成一片白。
- 问题曾在周一出现，昨晚复现；复现后因测试过程碰到其它信号导致机器重启，失败现场状态丢失。
- 模组供应商反馈其它项目客户也遇到类似问题，方向指向 ISP AE 曝光没有调好，在画面亮暗切换时容易出现。

### 2026-07-15 现场版本与触发条件补证

- 白屏现场固件内核版本为 `Linux 5.10.117 #10 SMP PREEMPT Thu Jun 25 15:37:23 HKT 2026 armv7l`。
- 设备没有单独更新过 app；app 与 2026-06-25 固件属于同一批次。
- 白屏复现时设备确实处于“充电中 + 补光模式 AUTO”。
- 失败状态下，关灯或降低环境光后图像恢复正常；重新开灯后再次变白。
- 这一过程没有发生 IQ、IR-Cut 或 IR 补光切换。

上述事实把问题从“通用 AE/ISP 或 Sensor 寄存器异常”进一步收敛到 2026-06-25 应用的软件光感稳定态 AE 锁定路径。

## Current Assessment

截至 2026-07-15，首要根因已更新为：旧应用在“充电中 + 补光 AUTO”时启用软件光感，并在暗场 AE 稳定后把当前长曝光/高增益复制为手动曝光，再把 AE 切到 manual；环境重新变亮后曝光不能回落，Sensor/ISP 持续饱和而表现为白屏。

根因状态：`high-confidence / source-confirmed + trigger-confirmed`。修复状态：`needs-verification`。在新固件完成板端 A/B 前，仍不得标记为 `fixed`。

最符合现象的链路是：

1. 设备充电且补光模式为 AUTO，`irlight.cpp` 启用 camera software light sensor。
2. 暗场中 AE 将 exposure、SensorGain 和 ISPGain 拉高，并在约 90 个稳定帧后进入软件定义的稳定状态。
3. 2026-06-25 批次 `hdi_vi.c::_VI_IspSetAEManualMode()` 调用 `MI_ISP_AE_SetManualExpo()`，复制当前暗场曝光，再调用 `MI_ISP_AE_SetExpoMode(..., E_SS_AE_MODE_M)`。
4. 开灯后 AE 仍处于 manual，曝光和增益无法按新亮度自动回落，Sensor/ISP 饱和而白屏。
5. 再次关灯后，同一组高曝光参数重新适合暗场，因此图像表面恢复正常。
6. 该链路不要求 IQ、IR-Cut、IR 补光或 ColorToGray 实际切换。
7. 重启 camera 会重新初始化 AE 状态，因此可恢复。

手指遮挡偏红可以由红外响应、AWB 被极端画面带偏、IR/IR-CUT 状态参与或 sensor 光谱响应解释；但整屏白的第一优先级仍是 AE 曝光或增益异常。

若后续严格 A/B 证伪软件光感 AE 锁定路径，再回退到 ISP AE 通用收敛、SC5336P I2C 写失败和 ISP OBC/Gain 同步方向。

## Hypothesis Matrix

| Priority | Hypothesis | Rationale | Next Evidence |
| --- | --- | --- | --- |
| P0 | 旧版软件光感稳定态把暗场曝光锁成 AE manual | 现场版本、app 同批、充电 + AUTO 和暗正常/亮白均已确认；2026-06-25 代码确实执行 `SetManualExpo` 和 manual mode | 用仅包含 AE 解锁修复的新 app 做同板同条件 A/B；记录 software light sensor 与 H26x reader 状态 |
| P1 | 修复应用后 ISP AE 仍无法从暗场向亮场收敛 | 新 SDK 含 AE 边界收敛、Sensor AE 时序、IQ/ISP Gain 同帧和 OBC/Gain 同步修复 | 新 app 仍复现时采集 AE exposure、SensorGain、ISPGain、LumY、SceneTarget、stable、reach-boundary |
| P1 | sensor 曝光/增益寄存器未跟随 AE 恢复 | 当前 SC5336P 驱动不检查 exposure/gain/VTS 的 I2C 写返回值，却无条件清 `reg_dirty` | 对比 ISP AE 查询值与 sensor register dump |
| P1 | AWB 被极端画面带偏 | 可解释偏红，但单独不太会导致全白 | 失败态 Rgain、Ggain、Bgain、色温、AWB stable |
| P2 | IR 灯、IR-CUT、IQ 或 ColorToGray 状态错配 | 现场已确认失败过程中未发生这些切换，因此不足以解释本次白屏 | IR PWM duty、IR-CUT 最近目标状态、IQ path、ColorToGray，仅作回归观测 |
| P2 | 热失效 | 降温不恢复，不优先 | 温度曲线与重启前后对照 |
| P2 | 显示或解码端异常 | 摄像头仍随遮挡变化，且重启 camera 恢复，不优先 | 同时抓 ISP 后帧和显示端帧 |

## Code Observations

### 软件光感 AE manual 锁定的代码时间线

- `modules/sensor` 提交 `5e2a68c8`（2026-05-09）加入 software light sensor；设备充电且补光 AUTO 时调用 `VSHDIVI_IspSetSWLightSensor(VS_TRUE)`。
- `modules/hdi` 在 2026-06-25 固件之前的基线（例如 `a0fd6f95`，2026-06-04）中，`_VI_IspSetAEManualMode()` 无条件调用 `MI_ISP_AE_SetManualExpo()`，再把 AE 模式设为 `E_SS_AE_MODE_M`。
- `modules/hdi` 提交 `56f270d7`（2026-07-06）才新增 `HDI_VI_SW_LIGHT_SENSOR_LOCK_AE=0`，把稳定态行为改为保持或恢复 `AE auto + fast`。
- `modules/app` 提交 `09eafe98`（2026-07-06）才加入 `diag.hdi.vi.isp.dump.run`；因此 2026-06-25 现场 app 不应被假定具备该命令。
- 当前 2026-07 应用源码和 `pcr02_ssc305_release` 中现成 `libhdi.so` 均不再导入 `MI_ISP_AE_SetManualExpo`，说明修复代码已存在；最终风险在于制品是否确实打包了新 `libhdi`。

软件光感监控任务仍依赖 H26x reader 生命周期。现场已确认启用软件光感的业务条件，但尚未保存失败态 H26x reader/monitor 直接日志；这一点作为最终运行态证据缺口保留，不影响把该路径列为当前 P0。

### IQ 加载路径存在次要风险

`SSPLAT_ISP_SetIqBin()` 会等待 AE/AWB/IQ ready 后调用 `MI_ISP_ApiCmdLoadBinFile()`。若等待超时，当前实现只打印超时日志，返回值仍可能保持成功。上层 `irlight.cpp::setRelight()` 对 `VSHDIVI_SetIqFilePath()`、`VSHDIVI_IspSetColorToGray()` 等返回值检查不足，存在软件状态与 ISP 实际状态不一致的风险。

该风险仍需修复，但结合当前“长时间扫码预览后白屏、重启 camera 恢复、供应商反馈 AE 参数”证据，优先级低于 AE/sensor 寄存器方向。

## Evidence Needed On Next Reproduction

2026-06-25 现场 app 缺少 2026-07-06 才加入的 ISP dump 命令，因此第一轮验证应采用单变量 A/B，而不是要求旧固件提供不存在的诊断接口。新固件复验时，不要先重启 camera；必须先抓失败态，再重启 camera 恢复后抓同样数据做对照。

### AE

- AE mode：auto/manual
- exposure time
- analog gain
- digital gain
- ISP digital gain
- LumY 或亮度均值
- SceneTarget
- AE stable
- reach boundary
- AE 更新计数或 frame count

判断方式：

- 如果白屏时 AE 查询值仍是高曝光/高增益，优先修 AE 参数、收敛速度、最大曝光/最大增益限制。
- 如果 AE 查询值已经正常，但 sensor 曝光/增益寄存器仍高，优先查 sensor driver、I2C 写入链路或寄存器 latch 行为。

### AWB

- Rgain
- Ggain
- Bgain
- color temperature
- AWB stable 或收敛状态

AWB 主要用于解释偏红和色偏，不作为整屏白的第一根因。

### Sensor Register Dump

需要模组供应商提供 SC5336P 的关键寄存器表。至少覆盖：

- 曝光寄存器
- analog gain / digital gain 寄存器
- VTS/HTS/frame length
- streaming 状态
- sensor mode 相关寄存器

常见 SmartSens SC 系列中，`0x3e00/0x3e01/0x3e02` 常见为曝光相关，`0x3e08/0x3e09` 常见为模拟增益相关；但本项必须以供应商 SC5336P 文档为准，不能作为硬编码事实。

### Frame Evidence

- 失败态 ISP 后 YUV/JPEG/BMP 一张。
- 恢复态同样抓一张。
- 如工具允许，抓 raw/bayer 更好。

如果 YUV/JPEG 本身白，说明问题在 VI/ISP/sensor 前端。若 YUV/JPEG 正常而显示白，再转查显示、解码或渲染链路。

### Auxiliary State

- 当前是否有 H26x reader active。
- 当前是否启用 SW light sensor。
- 当前 IQ path 或最近 IQ load 结果。
- IR PWM duty。
- IR-CUT 最近目标状态。
- ColorToGray 状态。

## Recommended Diagnostic Work

当前 2026-07 应用已经提供现场诊断命令：

```text
diag run diag.hdi.vi.isp.dump.run '{}'
```

建议输出 JSON：

```json
{
  "ae": {
    "mode": "auto_or_manual",
    "exposure": 0,
    "again": 0,
    "dgain": 0,
    "isp_dgain": 0,
    "lum_y": 0,
    "scene_target": 0,
    "stable": 0,
    "reach_boundary": 0
  },
  "awb": {
    "rgain": 0,
    "ggain": 0,
    "bgain": 0,
    "color_temp": 0,
    "stable": 0
  },
  "sensor": {
    "register_dump": {}
  },
  "vi": {
    "h26x_active": 0,
    "sw_light_sensor": 0,
    "iq_path": "",
    "ir_pwm": 0,
    "ircut_target": "unknown",
    "color_to_gray": 0
  }
}
```

当前应用也提供失败态抓图命令：

```text
diag run diag.hdi.vi.bmp.snap.run '{"width":640,"height":480,"path":"/tmp/camera_white.bmp"}'
```

保存失败态帧到 `/tmp`，只在归档中记录路径、大小、hash 和摘要，不复制大段 raw 数据。

## Temporary Mitigation Strategy

调试阶段不要先做自动重启 camera，否则会破坏失败现场。推荐分两级：

1. 旧固件临时规避：避免“充电中 + 补光 AUTO”组合；改变充电或模式后必须重启 camera，因为旧版关闭 software light sensor 只修改 enable 标志，不会解除已经进入的 AE manual。
2. 正式修复：打包 `HDI_VI_SW_LIGHT_SENSOR_LOCK_AE=0` 的新 `libhdi`，并确保 software light sensor enable/disable 时主动恢复 `AE auto + fast`。
3. 调试版本：检测白屏只 dump，不立即恢复。
4. 量产兜底：连续 N 秒亮度均值接近满值，同时 AE exposure/gain 异常偏高时，先强制 AE reset/auto，再失败才重载 ISP/IQ 或重启 camera pipe。

恢复前必须先保存一份最小 dump。

## Open Questions

1. 失败现场是否有内部 H26x reader/软件光感 monitor 直接运行日志。
2. 仅移植 AE 解锁修复后，同板“充电中 + 补光 AUTO + 暗场保持后开灯”的 A/B 是否不再白屏。
3. 新固件若仍白屏，AE 查询值是否仍为高曝光/高增益。
4. 新固件若仍白屏，SC5336P 实际曝光/增益寄存器是否与 AE 查询值一致。
5. 最终固件中的 `libhdi.so` 是否通过“不导入 `MI_ISP_AE_SetManualExpo`”的静态门禁。

## Next Action

下一步先做最小修复 A/B：

1. 保持同一块板、同一 SDK/驱动/IQ 和同一光照，仅替换包含 2026-07-06 AE 解锁逻辑的 app/`libhdi`。
2. 在充电中、补光 AUTO 下执行“关灯保持 5～10 秒，再开灯”循环；补充 30 秒和 60 秒暗场保持。
3. 至少执行 100 次暗→亮循环，记录白屏复现率和曝光恢复时间。
4. 静态检查最终 `libhdi.so`：`nm -D <libhdi.so> | grep MI_ISP_AE_SetManualExpo` 应无输出。
5. 如果新 app 仍复现，再采集 AE dump 和 SC5336P 寄存器读回，转查 ISP AE、Sensor I2C 或 OBC/Gain 同步。

## Repair Note

- `failed_scope`：2026-06-25 同批 kernel/app，设备充电中、补光 AUTO，暗场稳定后转亮出现白屏。
- `passing_scope_to_preserve`：Sensor/MIPI/VIF/ISP/显示链仍持续出图；暗场图像正常；不改图像采集数据流和当前 SC5336P/IQ 基线。
- `minimal_rerun`：同板旧 app 与仅含 AE 解锁修复的新 app 做暗→亮 A/B；新 app 至少 100 次循环。
- `rollback_anchor`：`Linux 5.10.117 #10 SMP PREEMPT Thu Jun 25 15:37:23 HKT 2026` 同批固件/app。
- `root_cause_status`：`high-confidence`；source 和业务触发条件已确认，板端修复 A/B 待完成。
- `repair_action`：禁止软件光感稳定态锁 AE manual；切换 software light sensor 时恢复 `AE auto + fast`；确保最终制品没有混入旧 `libhdi`。
- `semantic_verification`：暗场正常、开灯后曝光和增益回落、画面不持续饱和；新固件循环不复现。
- `do_not_repeat`：不要先以新 ISP SDK、MCLK 或 IQ 切换作为首修复；不要在未抓证据前自动重启 camera。

## Verification Status

- 已完成：现场内核版本、app 同批未单独更新、充电 + AUTO 触发条件、暗正常/亮白、无 IQ/IR-Cut/补光切换均已确认。
- 已完成：2026-05 至 2026-07 应用代码时间线、旧版 AE manual 路径和 2026-07-06 AE 解锁修复的源码核对。
- 未完成：失败态 H26x reader/monitor 直接日志，以及包含修复的新固件板端 A/B。
- 未完成：仅当新 app 仍复现时需要补 AE/AWB 和 SC5336P register dump。
- Gate result：`needs-fix`；当前为高置信根因，不得在 A/B 前标记 `fixed`。
