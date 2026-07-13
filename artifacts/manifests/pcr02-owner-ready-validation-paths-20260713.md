# PCR02 owner-ready validation paths 2026-07-13

## Scope

本记录只补齐 3 条 PCR02 owner-ready decision candidate 的真实 owner/实机/发布验证路径：

- `pcr02-camera-raw-preview-virtual-stream-architecture-20260711`
- `pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711`
- `pcr02-st77912-fb-mi-fb-boundary-decision-20260711`

本记录不是 owner decision，不关闭 owner gate，不提升 active，不声明 release，不修改源项目，不写 memory。

## Validation Matrix

| Candidate | Owner Gate | Device / Lab Validation | Release Gate | Active Promotion Condition |
|---|---|---|---|---|
| camera RAW_PREVIEW virtual stream | Owner 确认虚拟流 fan-out 架构、兼容影响、回滚路径和项目接受范围。 | 目标固件运行 RAW_PREVIEW、LCD_PREVIEW、QR_SCAN、VISION_RGB 并发场景；采集 CPU、内存、帧率、延迟和异常日志。 | 目标镜像构建、协议/ABI 兼容、关键应用路径 smoke、失败回滚命令可执行。 | owner 签收 + 实机并发验证 + release gate 通过后，才能考虑 active。 |
| ST77912 SPI clock/FPS | Owner 确认 54MHz/25fps 是候选档，不是默认安全发布档。 | 高温老化、SCLK 示波器验证、EMI 风险复核、双屏动画流畅度/撕裂/花屏统计、36/43/54MHz fallback 对比。 | kernel/DTB/uImage 构建通过；目标板刷机；冷启动/休眠恢复/长跑显示 smoke；失败时回退 36MHz 或 20fps。 | owner 签收 + 老化/SCLK/EMI/动画统计通过 + rollback 验证后，才能提升。 |
| ST77912 framebuffer vs mi_fb boundary | Owner 确认 `/dev/fb0`、`/dev/fb1` 属于 `fb_st77912`，`/dev/fb2` 属于 SStar FB0，`mi_fb` 不控制当前双小屏。 | 固件变更后复核 `/proc/fb`、`/sys/class/graphics/fb*/name`、应用打开的 fb 节点和显示路径日志。 | 目标镜像中 display provider、DTS、fbtft 与 config.json 边界一致；文档和发布说明不误导为 MI_FB 双屏。 | owner 签收 + 目标设备路径复核 + 发布说明边界正确后，才能提升。 |

## ST77912 Minimum Evidence

ST77912 相关候选至少需要以下真实证据后才能进入 active / release claim：

- 高温老化：记录温度、时长、样机编号、固件版本、异常次数、屏幕刷新状态和失败截图/日志引用。
- SCLK/信号完整性：记录测点、示波器截图引用、频率、占空比、抖动/毛刺判断和 36/43/54MHz 对比。
- EMI/可靠性：记录测试条件、风险结论和是否需要回退时钟档。
- 端到端显示：记录应用实际显示链路、双屏交错/局刷策略、帧率、撕裂/花屏/卡顿统计。
- 回滚：验证 DTS 降回 36MHz 或 fps 降档后仍可构建、启动和显示。

## Recommended Commands

以下命令是验证路径入口，不代表本记录已经执行源项目验证：

```bash
rtk ./build.sh kernel --profile ap6303bh_512m_v20_debug_customer --allow-dirty --no-clean --no-copy-nfs
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "pcr02 st77912" --domain projects/pcr02 --json
```

设备侧证据应通过人工记录或后续 validation report 登记，不把 raw logs、截图原件或二进制制品复制进正文层。

## Residual Risk

- 当前已有 implementation evidence 和候选边界，但没有本记录要求的完整实机/实验室验证证据。
- 任何 active promotion、owner decision 或 release claim 都必须另有 owner 签收、验证报告和回滚证据。
- 本记录只定义下一步验证路径，不能作为测试通过证明。
