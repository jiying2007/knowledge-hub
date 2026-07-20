---
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: accepted-boundary-evidence-pending
decision_date: '2026-07-16'
aliases:
- PCR02 ST77912 双屏 SPI 时钟与 FPS 取舍决策候选
review_scope: owner-attested-boundary-only-no-active-release-or-evidence-ready
owner_roles_required:
- PCR02 product decision owner
- display/BSP owner
- hardware/EMC owner
- release owner
evidence_readiness:
  owner: accepted-boundary-evidence-pending
  source: pending-current-commit-and-artifact-identity
  device: pending-real-device-or-lab-evidence
  release: pending-release-and-rollback-evidence
  validation_path: artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
owner_attestation_ref: artifacts/manifests/knowledge-hub-pcr02-specialized-owner-attestation-20260716.md
owner_decision: accept-36mhz-stable-baseline-higher-clocks-validation-only-remain-reviewing
id: pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711
title: PCR02 ST77912 双屏 SPI 时钟与 FPS 取舍决策候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: Codex analysis of PCR02 ST77912 dual LCD SPI clock/FPS tradeoff
review_after: '2026-10-11'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; owner accepted 36MHz stable baseline and higher clocks as validation-only; high-temperature, SCLK/EMI,
  device, release and rollback evidence remain pending
tags:
- pcr02
- st77912
- lcd
- spi
- mspi
- fbtft
- fps
- high-temperature-aging
- decision-candidate
- manual-validation-pending
- no-active-promotion
validation_refs:
- projects/pcr02-ssc305/decisions/st77912-dual-screen-spi-clock-fps-decision-20260711.md
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
evidence_strength: source-code-plus-schematic-plus-device-observation-pending-aging-validation
evidence_refs:
- ~/PCR02_MAIN_V2.0_20251211.pdf
- SourceCode/kernel/arch/arm/boot/dts/iford.dtsi
- SourceCode/kernel/drivers/sstar/mspi/drv_mspi.c
- SourceCode/kernel/drivers/sstar/mspi/iford/hal_mspireg.h
- SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c
created_at: '2026-07-11'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-11'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: PCR02 双 ST77912 小屏走 fbtft/SPI，不受 mi_fb 控制。双屏 240x240 RGB565 满帧 30fps 需要 55.296Mbit/s 纯像素带宽，54MHz 理论上已不足以稳定支撑；若业务需要
  20-25fps 观感，应优先采用 43-54MHz 分档验证、局部刷新/交错提交和驱动 staging，而不是继续按双屏满帧 30fps 设计。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
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

<!-- pcr02-owner-device-release-validation:start -->
## Owner、实机与发布验证门禁

> 本节定义真实验证路径，不表示任何命令已经执行，也不是 owner decision、active promotion 或 release 授权。

### 1. Owner 决策路径

- `decision_owner=leiwenjun`，并已通过 `knowledge-hub-pcr02-specialized-owner-attestation-20260716` 接受 36MHz 稳态默认、40/43MHz 与 54MHz 仅作验证档的边界。
- 该 owner 决定不证明任何高温、SCLK/EMI、设备、发布或回滚验证已通过；候选继续保持 `reviewing`。
- display/BSP owner 负责 DTS、fbtft、MSPI 实际时钟和应用刷新策略；hardware/EMC owner 负责信号完整性及 EMI 风险；release owner 负责制品和回滚。角色可由同一真人承担，但每个责任必须显式记录。

### 2. Source 与制品身份

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、分支、dirty 状态，以及实际使用的 kernel/DTS/config commit。
- 记录可复现构建入口、返回码、构建环境版本和 `uImage`/DTB/rootfs 或目标升级包 SHA256；不得只引用工作区目录或会话结论。
- 将 36MHz、40/43MHz、54MHz 三档配置 diff 与制品一一对应；无法从当前 commit 重建的制品不得进入设备矩阵。

### 3. 高温老化矩阵

owner 在执行前填写产品规范中的温度、供电、样机数和时长，不由 Hub 猜测规格。每个时钟档至少记录：

| 维度 | 必填证据 |
|---|---|
| 样机与版本 | 脱敏设备编号、PCB/屏模组批次、固件版本、制品 hash |
| 环境 | 箱体设定温度、板上实测温度、供电标称/下限、起止时间、累计 display-hours |
| 负载 | 双屏动画刷新面积、Wi-Fi/录像/AI/CPU 负载组合、亮度与休眠/唤醒循环 |
| 结果 | 白屏、花屏、残影、SPI timeout、初始化失败、重启次数及每 display-hour 失败率 |
| 证据 | 关键日志摘要、异常截图/视频引用、`dmesg` 时间窗口、复现步骤和处置 |

任何异常都必须关联时钟档、设备、温度和制品；只写“老化通过”不构成证据。

### 4. SCLK、信号完整性与 EMI

- 在两路 LCD 的 SCLK、CS、DC、MOSI 及电源/地参考上记录测点、探头、带宽、采样率和负载条件。
- 对 36MHz、40/43MHz、54MHz 分别保存实际频率、占空比、上升/下降时间、过冲/下冲、振铃、毛刺、CS/DC setup/hold 和帧间隙判断。
- 常温、高温和供电下限均需复核；驱动配置值不能替代示波器实测值。
- EMI 由 hardware/EMC owner 按产品适用标准确定预扫或正式测试条件，记录频段、天线/探头、最差档和裕量；“无明显干扰”不能替代测量。
- 若 54MHz 缺少信号或 EMI 裕量，release 必须锁定低一档并验证降档制品。

### 5. 端到端双屏显示验证

- 固定链路：应用测试图/动画 -> `/dev/fb0`、`/dev/fb1` 用户态 buffer -> fbtft deferred I/O -> MSPI -> 两块 ST77912 面板。
- 使用带帧号、颜色块、边界线和交替眼图案的确定性序列，记录应用提交时间、驱动刷新时间、实际帧率、丢帧、撕裂、花屏、残影和卡顿。
- 分别覆盖单屏、双屏交错、双屏同时、局部刷新、短时满帧、冷启动、热启动、休眠唤醒和长跑；视频或仪器证据必须能关联设备、制品和时钟档。
- 应用 buffer CRC 只能证明提交内容；必须同时有面板端观察或仪器证据，才能证明端到端显示正确。

### 6. Release 与回滚

- release owner 记录候选制品、设备矩阵结果、已知限制、发布说明和目标版本；缺少任一高温/SCLK/EMI/端到端证据时状态保持 `reviewing`。
- 在目标板实际验证 54 -> 43/40 -> 36MHz 以及 fps 降档的回滚制品可启动、双屏可显示、配置与版本可识别。
- promotion 只能在真实 owner 签收、所有必需证据引用可恢复且 product gate 无技术 blocker 后另行授权执行；本节不提供 promotion 授权。

### 证据落地契约

- 证据记录必须包含 `owner_identity`、`source_commit`、`artifact_sha256`、`device_identity`、`environment`、`commands`、`exit_codes`、`result_summary`、`rollback_result` 和可恢复引用。
- raw log、视频、截图和二进制只保存在受控外部制品位置；Hub 正文只保存脱敏摘要、hash 和引用。
- 最终复核命令：`rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13`。
<!-- pcr02-owner-device-release-validation:end -->
