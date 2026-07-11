---
id: pcr02-camera-whiteout-ae-exposure-analysis-20260703
title: PCR02 摄像头老化后白屏的 AE/ISP 初步分析
kind: debug-record
domain: projects/pcr02
status: reviewing
owner: team-core
created_at: 2026-07-03
updated_at: 2026-07-03
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
---

# PCR02 摄像头老化后白屏的 AE/ISP 初步分析

## Source

- 来源：2026-07-03 Codex 会话中的现场排障摘要。
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

## Current Assessment

当前首要怀疑应从 IQ 频繁切换调整为 AE/ISP 曝光控制异常。

最符合现象的链路是：

1. 暗场、遮挡或长时间扫码预览过程中，AE 将 exposure、analog gain、digital gain 拉高。
2. 画面重新变亮后，AE 没有及时或正确把曝光和增益降下来。
3. sensor 或 ISP 输出进入饱和状态，表现为整幅画面发白。
4. 重启 camera 后，AE/ISP/sensor runtime 状态被重置，因此恢复正常。

手指遮挡偏红可以由红外响应、AWB 被极端画面带偏、IR/IR-CUT 状态参与或 sensor 光谱响应解释；但整屏白的第一优先级仍是 AE 曝光或增益异常。

## Hypothesis Matrix

| Priority | Hypothesis | Rationale | Next Evidence |
| --- | --- | --- | --- |
| P0 | AE 收敛失败或卡在异常曝光/增益 | 白屏、重启恢复、供应商反馈均指向亮暗切换后曝光控制异常 | 失败态 AE exposure、again、dgain、LumY、SceneTarget、stable、reach-boundary |
| P0 | sensor 曝光/增益寄存器未跟随 AE 恢复 | ISP 可能已算出正确值，但 sensor register 仍停在高曝光/高增益 | 对比 ISP AE 查询值与 sensor register dump |
| P1 | AWB 被极端画面带偏 | 可解释偏红，但单独不太会导致全白 | 失败态 Rgain、Ggain、Bgain、色温、AWB stable |
| P1 | IR 灯、IR-CUT、IQ 或 ColorToGray 状态错配 | 手指偏红和夜间链路可能相关；但无 H26x 拉流时 hdi_vi SW 光敏不应默认触发 | IR PWM duty、IR-CUT 最近目标状态、IQ path、SW light sensor enable |
| P2 | hdi_vi SW 光敏导致频繁 IQ 切换 | 代码存在 IQ load 超时误成功风险，但老化条件称无配网、无 H264/H265 拉流，概率下降 | 是否有内部 H26x reader active、是否启动 `hdi_vi_sw_lightsensor` |
| P2 | 热失效 | 降温不恢复，不优先 | 温度曲线与重启前后对照 |
| P2 | 显示或解码端异常 | 摄像头仍随遮挡变化，且重启 camera 恢复，不优先 | 同时抓 ISP 后帧和显示端帧 |

## Code Observations

### hdi_vi SW 光敏和 IQ 切换不是当前第一怀疑

`hdi_vi` 的 SW 光敏监控任务在 `VSHDIVI_H26xReaderCreate()` 中创建；`VSHDIVI_H26xReaderDestroy()` 会关闭该任务。因此，如果老化期间确实没有任何内部或外部 H26x reader 被创建，则 `hdi_vi.c` 的 SW 光敏日夜检测链路理论上不会运行，也不应由它触发频繁 IQ 切换。

需要注意：没有外部拉流不等于没有内部 H26x reader。DVR、RTSP、测试命令、AI/媒体预览或 video pipe 仍可能调用 `VSAPIVIDEO_ViReaderOpen(VIDEO_CHANNEL_VENC_H26X, ...)`，间接创建 H26x reader。

### IQ 加载路径存在次要风险

`SSPLAT_ISP_SetIqBin()` 会等待 AE/AWB/IQ ready 后调用 `MI_ISP_ApiCmdLoadBinFile()`。若等待超时，当前实现只打印超时日志，返回值仍可能保持成功。上层 `irlight.cpp::setRelight()` 对 `VSHDIVI_SetIqFilePath()`、`VSHDIVI_IspSetColorToGray()` 等返回值检查不足，存在软件状态与 ISP 实际状态不一致的风险。

该风险仍需修复，但结合当前“长时间扫码预览后白屏、重启 camera 恢复、供应商反馈 AE 参数”证据，优先级低于 AE/sensor 寄存器方向。

## Evidence Needed On Next Reproduction

下次复现时，不要先重启 camera。必须先抓失败态，再重启 camera 恢复后抓同样数据做对照。

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

优先增加一个现场诊断命令，例如：

```text
diag.hdi.vi.isp.state.dump.run
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

另加一个失败态抓图命令，例如：

```text
diag.hdi.vi.snapshot.dump.run
```

保存失败态帧到 `/tmp`，只在归档中记录路径、大小、hash 和摘要，不复制大段 raw 数据。

## Temporary Mitigation Strategy

调试阶段不要先做自动重启 camera，否则会破坏失败现场。推荐分两级：

1. 调试版本：检测白屏只 dump，不恢复。
2. 量产兜底：连续 N 秒亮度均值接近满值，同时 AE exposure/gain 异常偏高时，先强制 AE reset/auto，再失败才重载 ISP/IQ 或重启 camera pipe。

恢复前必须先保存一份最小 dump。

## Open Questions

1. 老化期间扫码预览是否创建了内部 H26x reader，还是只走 YUV/preview path。
2. 白屏时 AE 查询值是否仍为高曝光/高增益。
3. 白屏时 sensor 曝光/增益寄存器是否与 AE 查询值一致。
4. 白屏时 IR 灯、IR-CUT、ColorToGray 是否处于预期白天状态。
5. 供应商是否能给出 SC5336P 推荐 AE 参数、最大曝光/最大增益限制、亮暗切换收敛配置和已知问题说明。

## Next Action

下一轮复现的第一目标是证明：

- 白屏时 AE 认为自己是多少曝光和增益。
- sensor 实际寄存器又是多少曝光和增益。

这两组数据一对比，即可把根因收敛到 ISP AE 算法参数、sensor driver/I2C 写入链路，或 ISP 后处理链路。

## Verification Status

- 已完成：源码只读分析和现场现象链整理。
- 未完成：失败态 AE/AWB/sensor register dump。当前失败现场已因机器重启丢失，不能给最终根因结论。
- Gate result：`needs-fix`，等待下一次复现证据。
