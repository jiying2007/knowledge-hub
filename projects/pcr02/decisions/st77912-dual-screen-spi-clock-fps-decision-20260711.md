---
id: pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711
title: PCR02 ST77912 双屏 SPI 时钟与 FPS 取舍决策候选
kind: decision
domain: projects/pcr02
path: projects/pcr02/decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: Codex analysis of PCR02 ST77912 dual LCD SPI clock/FPS tradeoff
review_after: 2026-10-11
created_at: 2026-07-11
updated_at: 2026-07-11
promotion: none
promotion_decision: none; PCR02 ST77912 双 SPI 小屏项目本地决策候选，需要高温老化、示波器和实机动画验证后才能提升为 active
tags:
  - pcr02
  - st77912
  - lcd
  - spi
  - mspi
  - fbtft
  - fps
  - high-temperature-aging
related: []
validation_refs:
  - "manual_validation_pending: true"
  - "reason: requires board high-temperature aging, oscilloscope SCLK validation, and dual-screen animation validation"
summary_zh: "PCR02 双 ST77912 小屏走 fbtft/SPI，不受 mi_fb 控制。双屏 240x240 RGB565 满帧 30fps 需要 55.296Mbit/s 纯像素带宽，54MHz 理论上已不足以稳定支撑；若业务需要 20-25fps 观感，应优先采用 43-54MHz 分档验证、局部刷新/交错提交和驱动 staging，而不是继续按双屏满帧 30fps 设计。"
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
evidence_strength: source-code-plus-schematic-plus-device-observation-pending-aging-validation
evidence_refs:
  - ~/PCR02_MAIN_V2.0_20251211.pdf
  - SourceCode/kernel/arch/arm/boot/dts/iford.dtsi
  - SourceCode/kernel/drivers/sstar/mspi/drv_mspi.c
  - SourceCode/kernel/drivers/sstar/mspi/iford/hal_mspireg.h
  - SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: 2026-07-11
human_reviewed_by:
human_reviewed_at:
review_basis:
decision_owner: leiwenjun
decision_status: candidate
decision_date: 2026-07-11
---

# PCR02 ST77912 双屏 SPI 时钟与 FPS 取舍决策候选

## 背景

PCR02 当前两块小屏在设备侧表现为 `/dev/fb0` 和 `/dev/fb1`，`/proc/fb` 显示二者均为 `fb_st77912`，`/dev/fb2` 才是 `SStar FB0`。因此双小屏不受 `/config/config.json` 中 `mi_fb` 配置控制。

原理图 `PCR02_MAIN_V2.0_20251211.pdf` 中 LCD 相关信号为 `S-MSPI1_CK`、`S-MSPI1_DO`、`S-MSPI1_CS`、`S-MSPI0_CS`、`LCD_DC_1`、`LCD_DC_2`、`LCD_RST/M_RST`、`LCD_BL_PWM`，未发现与两块 LCD 直接相关的 TE/VSYNC/HSYNC/DCLK/DE 信号。该链路应按 SPI command panel 处理，不按 MI_DISP 扫描输出处理。

曾使用 `SPI MCLK 54MHz` 时高温老化有异常，后降为 `36MHz`。此前按单屏 30fps 估算带宽，未把双屏满帧带宽算入。

## 适用范围

- 适用：PCR02 当前硬件，双 ST77912 240x240 RGB565 小屏，Linux fbtft + SigmaStar MSPI 驱动。
- 不适用：未来改接 MI_DISP/TTL/RGB/MIPI DSI/MCU 并口显示链路后的屏幕方案。
- 不适用：`/dev/fb2` SStar FB0 / `mi_fb` 图形层。

## 权威来源

- source_id：manual
- source_path：当前 Codex 会话中的源码、SGSDocs、设备输出和原理图分析
- owner：leiwenjun
- source_status：manual-entry-pending-review

## 决策问题

在 54MHz 高温老化异常且业务希望达到 20-25fps 动画观感的前提下，双 ST77912 小屏应如何选择 SPI MCLK、fbtft `fps` 和刷新策略。

## 选项

| 选项 | 影响范围 | 成本 | 风险 |
| --- | --- | --- | --- |
| 36MHz + 12-15fps 满帧 | 量产稳态基线 | 低 | 动画观感不足，无法满足 20-25fps 诉求 |
| 40/43MHz + 18-20fps 目标 | 稳定优先的性能档 | 中 | 需要确认实际 SCLK 和高温稳定性 |
| 54MHz + 20-25fps 局部刷新 | 观感优先档 | 中高 | 已有高温异常历史，必须限制刷新面积并补硬件/老化验证 |
| 54MHz + 双屏满帧 30fps | 不建议 | 高 | 纯像素带宽已接近或超过理论上限，老化风险高 |

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `cat /proc/fb` | 0 | 设备侧显示 fb0/fb1 为 `fb_st77912`，fb2 为 `SStar FB0`。 | device shell output in current session | Device | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |
| `rtk sed -n '430,490p' SourceCode/kernel/arch/arm/boot/dts/iford.dtsi` | 0 | DTS 中两个 `st77912` 节点均配置 `spi-max-frequency=<36000000>`、`fps=<30>`、`buswidth=<8>`。 | SourceCode/kernel/arch/arm/boot/dts/iford.dtsi | Source | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |
| `rtk sed -n '760,790p' SourceCode/kernel/arch/arm/boot/dts/iford-clks.dtsi` | 0 | `CLK_mspi0` 父时钟包括 108MHz、144MHz、12MHz、SPI synth PLL。 | SourceCode/kernel/arch/arm/boot/dts/iford-clks.dtsi | Source | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |
| `rtk sed -n '88,105p' SourceCode/kernel/drivers/sstar/mspi/iford/hal_mspireg.h` | 0 | MSPI 分频表为 `{2,4,8,16,32,64,128,256}`。 | SourceCode/kernel/drivers/sstar/mspi/iford/hal_mspireg.h | Source | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |
| `rtk sed -n '140,258p' SourceCode/kernel/drivers/sstar/mspi/drv_mspi.c` | 0 | MSPI 驱动选择不超过 `spi-max-frequency` 的最高实际时钟档。 | SourceCode/kernel/drivers/sstar/mspi/drv_mspi.c | Source | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |
| `rtk sed -n '560,610p' SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c` and `rtk rg -n "fbdefio->delay"` | 0 | fbtft 的 `fps` 影响 deferred_io 延迟 `HZ / fps`，不等于真实链路可达帧率。 | SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c | Source | pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711 |

## 关键计算

单屏 240x240 RGB565 一帧：

```text
240 * 240 * 16bit = 921600 bit = 115200 byte
```

双屏满帧：

```text
921600 * 2 = 1843200 bit = 230400 byte
```

双屏满帧 30fps 纯像素带宽：

```text
1843200 * 30 = 55.296 Mbit/s
```

这尚未计入 ST77912 命令、地址窗口、DC/CS 切换、SPI 控制器间隙、deferred_io 调度、用户态 memcpy 和两块屏共用 MSPI 总线的排队成本。因此 54MHz 理论上也不适合承诺双屏满帧 30fps。

按纯像素流估算，双屏满帧上限如下：

| 实际 SCLK | 双屏满帧理论 fps | 工程可用估计 70%-80% |
| ---: | ---: | ---: |
| 54MHz | 29.3fps | 20.5-23.4fps |
| 43MHz | 23.5fps | 16.4-18.8fps |
| 40MHz | 21.7fps | 15.2-17.4fps |
| 36MHz | 19.5fps | 13.7-15.6fps |
| 33.25MHz | 18.0fps | 12.6-14.4fps |
| 27MHz | 14.6fps | 10.3-11.7fps |

## 当前结论

1. 36MHz 是稳态基础档，但只能合理承诺双屏满帧约 12-15fps，不满足 20-25fps 业务诉求。
2. 若业务要求 20-25fps，应优先定义为“动画观感 20-25fps”，不要定义为“双屏全画面满帧 20-25fps”。
3. 满足 20-25fps 观感的推荐路径是：提高 SPI 时钟到经过验证的最高稳定档，同时限制刷新面积、使用 back buffer/staging，避免用户态写 framebuffer 与 fbtft 刷屏竞争。
4. 54MHz 已有高温老化异常历史，不能作为默认无条件量产档。若要重新启用，只能作为“观感优先验证档”，必须配套刷新面积限制、驱动/应用改造和高温老化验证。

## 推荐组合

### 稳定优先基线

```text
spi-max-frequency = 36000000
fbtft fps = 15
应用动画目标 = 12-15fps
刷新策略 = 双屏交错 full frame 或严格 dirty bounding box
```

### 20fps 候选档

```text
spi-max-frequency = 43000000 或 40000000
fbtft fps = 20
应用动画目标 = 20fps
刷新策略 = 局部刷新优先；双屏满帧只允许短时出现
```

该档需要确认 MSPI 实际 SCLK 是否落在 40/43MHz，而不是回落到 36MHz。若无法稳定得到 40/43MHz，则只能在 36MHz 下通过局部刷新实现 20fps 观感。

### 25fps 观感候选档

```text
spi-max-frequency = 54000000
fbtft fps = 25
应用动画目标 = 25fps
刷新策略 = 禁止长期双屏满帧；每帧刷新面积建议控制在双屏总面积的 70%-80% 以下，优先只刷新眼睛变化区域
```

该档不是默认量产建议。启用条件：

- 示波器确认 SCLK、CS、DC、MOSI 波形在常温、高温、低压下满足裕量。
- 高温老化覆盖目标温度、整机电源、Wi-Fi/录像/AI 高负载组合。
- 驱动或应用已引入 back buffer/staging，避免刷新过程中用户态继续改同一块 mmap framebuffer。
- 出现白屏、花屏、残影、SPI timeout、ST77912 初始化异常时自动降级到 43MHz 或 36MHz。

## 生效条件

该候选成为 active 前至少需要：

1. 示波器测得实际 SCLK 档位和波形质量。
2. 36MHz、40/43MHz、54MHz 三档 A/B 老化记录。
3. 20fps 和 25fps 动画实机视频或自动化统计记录。
4. `dmesg` 中无 `st77912`、`fbtft`、`mspi`、`xcrzreset` 异常。
5. 明确是否已修复 shared reset GPIO 和 framebuffer 写刷竞争。

## 回滚条件

满足任一条件应回滚到低一档：

- 高温老化出现 LCD 花屏、白屏、残影异常率上升。
- SPI 波形在高温/低压下无足够裕量。
- 双屏动画期间出现连续帧丢失、刷新耗时超过目标帧周期。
- `dmesg` 出现 MSPI 或 ST77912 传输异常。

## 风险与限制

- 当前没有 TE/VSYNC 硬件同步，SPI 小屏无法承诺严格 tear-free。
- fbtft 的 `fps` 是调度节奏，不是实际可达帧率保证。
- 54MHz 已有高温老化异常历史，重新使用必须有验证闭环。
- 20-25fps 若按双屏满帧定义，风险和带宽压力显著高于按局部刷新定义。

## Review 周期

- owner：leiwenjun
- review_after：2026-10-11
- 下一次复核内容：补充三档时钟高温老化、示波器实测、实机动画统计和最终量产时钟选择。
