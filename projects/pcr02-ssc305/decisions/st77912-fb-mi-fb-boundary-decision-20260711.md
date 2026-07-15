---
id: pcr02-st77912-fb-mi-fb-boundary-decision-20260711
title: PCR02 ST77912 framebuffer 与 SigmaStar mi_fb 边界决策候选
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/st77912-fb-mi-fb-boundary-decision-20260711.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: Codex analysis of PCR02 framebuffer mapping between fb_st77912 and SigmaStar mi_fb
review_after: '2026-10-11'
created_at: 2026-07-11
updated_at: '2026-07-13'
promotion: none
promotion_decision: none; PCR02 framebuffer/mi_fb 边界项目本地决策候选，需要 owner review 和固件变更后的目标设备复核后才能提升 active
tags:
- pcr02
- st77912
- framebuffer
- fbdev
- fbtft
- mi_fb
- sstar-fb
- display
- decision-candidate
- manual-validation-pending
- no-active-promotion
related:
- pcr02-st77912-dual-screen-spi-clock-fps-decision-20260711
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
validation_refs:
- projects/pcr02-ssc305/decisions/st77912-fb-mi-fb-boundary-decision-20260711.md
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
summary_zh: PCR02 当前双小屏使用 `/dev/fb0` 和 `/dev/fb1`，二者在设备侧识别为 `fb_st77912`，由 Linux fbtft/ST77912 驱动管理；`/config/config.json`
  中的 `mi_fb` 配置属于 SigmaStar MI_FB/SStar FB 路径，不控制当前双小屏。当前运行态 `/proc/fb` 中 `/dev/fb2` 才是 `SStar FB0`。
review_status: human-reviewed-accepted
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
evidence_strength: source-code-plus-device-observation-pending-owner-review
evidence_refs:
- device:/proc/fb
- device:/sys/class/graphics/fb0/name
- device:/sys/class/graphics/fb1/name
- SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/sensor/display/display_provider.h
- SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/sensor/display/display_provider.cpp
- SourceCode/kernel/arch/arm/boot/dts/iford.dtsi
- SourceCode/kernel/drivers/staging/fbtft/fb_st77912.c
- SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c
- SourceCode/sdk/linux/init/fb/fb_init.c
- SourceCode/project/board/iford/SSC029A-S01A/config/config.json
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: 2026-07-11
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_owner: unassigned
decision_status: candidate
decision_date: 2026-07-11
aliases:
- PCR02 ST77912 framebuffer 与 SigmaStar mi_fb 边界决策候选
manual_validation_pending: true
review_scope: content-review-record-only-not-owner-approval
owner_roles_required:
- PCR02 product decision owner
- display/BSP owner
- application owner
- release owner
evidence_readiness:
  owner: pending-real-owner-assignment-and-decision
  source: pending-current-commit-and-artifact-identity
  device: pending-real-device-or-lab-evidence
  release: pending-release-and-rollback-evidence
  validation_path: artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
---

# PCR02 ST77912 framebuffer 与 SigmaStar mi_fb 边界决策候选

## 背景

PCR02 设备当前上报的 framebuffer 顺序为：

```text
0 fb_st77912
1 fb_st77912
2 SStar FB0
```

同时 `/sys/class/graphics/fb0/name` 与 `/sys/class/graphics/fb1/name` 均为 `fb_st77912`。这说明当前双小屏的用户态节点是 `/dev/fb0` 和 `/dev/fb1`，底层驱动是 Linux fbtft 框架下的 ST77912 驱动，而不是 SigmaStar MI_FB 驱动。

应用层也固定使用这两个节点：`DisplayProvider` 的 `fbPath_` 为 `"/dev/fb0"` 与 `"/dev/fb1"`，初始化时直接 `open(fbPath_[dspid], O_RDWR)`。

## 适用范围

- 适用：PCR02 当前双 ST77912 240x240 RGB565 小屏，使用 `/dev/fb0` 与 `/dev/fb1` 的显示链路。
- 适用：分析动画抖动、残影、局部刷新、双缓冲、SPI 刷屏带宽时的 framebuffer 边界判断。
- 不适用：`/dev/fb2` 的 SStar FB0 / SigmaStar MI_FB 图层调试。
- 不适用：未来硬件若改接 MI_DISP/MI_FB 扫描输出、TTL/RGB/MIPI DSI/MCU 并口屏后的方案。

## 决策结论

1. `/dev/fb0` 与 `/dev/fb1` 是两个 `fb_st77912` 节点，属于 fbtft/ST77912 SPI 小屏路径。
2. `/config/config.json` 中的 `mi_fb` 配置不控制当前双小屏的 `/dev/fb0` 与 `/dev/fb1`。
3. 当前运行态 `/proc/fb` 中的 `2 SStar FB0` 才对应 SigmaStar SStar FB/MI_FB 路径；若使用 `/config/config.json` 的 `mi_fb` 配置，应按 `/dev/fb2` 或对应 SStar FB 节点验证。
4. 对 `/dev/fb0` 与 `/dev/fb1` 使用 `FBIOSET_DISPLAYLAYER_ATTRIBUTES`、`MI_FB_PanDisplay` 或 MI_FB 的 buffer size/display layer 配置，不应预期能改变 ST77912 小屏的显存分配、双缓冲或刷新模型。
5. 当前双小屏优化应沿 fbtft/ST77912/SPI 路径处理，包括 SPI 时钟、fbtft deferred_io、应用层 back buffer/staging、dirty area 管理和双屏刷新调度。

## 证据

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `cat /proc/fb` | 0 | 设备侧显示 fb0/fb1 为 `fb_st77912`，fb2 为 `SStar FB0`。 | device shell output in current session | Device | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `cat /sys/class/graphics/fb0/name` and `cat /sys/class/graphics/fb1/name` | 0 | fb0/fb1 名称均为 `fb_st77912`。 | device shell output in current session | Device | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk rg -n "fbPath_|/dev/fb0|/dev/fb1" .../modules/sensor/display ...` | 0 | `display_provider.h` 固定 `fbPath_ = {"/dev/fb0", "/dev/fb1"}`，`display_provider.cpp` 按该路径 open。 | SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/sensor/display | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk rg -n "DRVNAME \"fb_st77912\"|FBTFT_REGISTER_DRIVER..." ...` | 0 | ST77912 驱动注册名为 `fb_st77912`，compatible 为 `sitronix,st77912`。 | SourceCode/kernel/drivers/staging/fbtft/fb_st77912.c | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk rg -n "vmem_size = display->width|info->fix.smem_len|info->var.yres_virtual" ...` | 0 | fbtft 按单屏尺寸分配 framebuffer，`yres_virtual = yres`，默认不是 MI_FB 式多 buffer 扫描模型。 | SourceCode/kernel/drivers/staging/fbtft/fbtft-core.c | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk rg -n "st77912@0|st77912@1|compatible = \"sitronix,st77912\"" .../iford.dtsi` | 0 | DTS 存在两个 `st77912` SPI 节点，对应两个 fbtft 小屏。 | SourceCode/kernel/arch/arm/boot/dts/iford.dtsi | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk sed -n '1,80p' .../config/config.json` | 0 | `mi_fb` 配置描述的是 `fb_hwlayer_id`、`fb_hwwin_id`、1024x600 等 SStar/MI_DISP 方向参数，不是 240x240 ST77912 小屏参数。 | SourceCode/project/board/iford/SSC029A-S01A/config/config.json | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |
| `rtk rg -n "MI_FB|FBIOSET_DISPLAYLAYER|fb_pan_display" .../sdk/linux/init/fb/fb_init.c` | 0 | SigmaStar fb_init 通过 MI_FB API 实现 display layer、pan display、mmap 等操作，属于 SStar FB 路径。 | SourceCode/sdk/linux/init/fb/fb_init.c | Source | pcr02-st77912-fb-mi-fb-boundary-decision-20260711 |

## 为什么 `mi_fb` 不控制 fb0/fb1

`/proc/fb` 是运行态事实，顺序已经把两个小屏和 SStar FB 区分开：

```text
/dev/fb0 -> fb_st77912
/dev/fb1 -> fb_st77912
/dev/fb2 -> SStar FB0
```

应用显示模块打开的正是 `/dev/fb0` 和 `/dev/fb1`，因此当前 sensor/display 小屏路径落在 fbtft/ST77912，而不是 SStar FB0。即使 `/config/config.json` 存在 `mi_fb` 段，它描述的也是 SigmaStar FB/MI_DISP 的硬件层窗口和 buffer 参数；这些参数不会被 fbtft 的 `fb_st77912` 驱动读取。

## 双缓冲判断

fbtft 初始化中按如下模式分配显存：

```text
vmem_size = display->width * display->height * bpp / 8
info->fix.smem_len = vmem_size
info->var.yres_virtual = info->var.yres
```

对 240x240 RGB565，小屏单 framebuffer 长度为：

```text
240 * 240 * 2 = 115200 bytes
```

因此设备上看到的 `virtual_size = 240,240`、`stride = 480`、`smem_len = 115200` 是 fbtft 单 buffer 模型的自然结果，不是应用层误判。除非修改 fbtft/ST77912 驱动分配逻辑并实现可靠的刷屏 staging，否则不能把 `mi_fb` 的双缓冲配置直接套到 fb0/fb1。

## 工程影响

- 动画抖动和残影应优先按 fbtft/SPI 刷新竞争排查，不应先调 `/config/config.json` 的 `mi_fb`。
- `FBIOPAN_DISPLAY` 对 `fb_st77912` 没有 MI_FB 扫描输出意义；即使 Linux fb core 有 pan ioctl，也需要具体驱动支持有效的 virtual buffer 和 pan operation。
- `FBIOSET_DISPLAYLAYER_ATTRIBUTES` 属于 SigmaStar FB ioctl 语义，不是 fbtft/ST77912 的控制面。
- 后续若要把两个小屏“适配到 MI_FB”，本质上不是改配置，而是重做显示链路：硬件连接、驱动模型、panel 输出接口和应用打开节点都要重新设计。

## 推荐后续

1. 保持 `/dev/fb0` 与 `/dev/fb1` 作为 ST77912 小屏路径的事实边界。
2. 将 `/config/config.json` 的 `mi_fb` 仅用于 SStar FB/MI_DISP 路径分析，不作为双小屏调参入口。
3. 双小屏优化聚焦：SPI MCLK/fps 分档、fbtft deferred_io、应用层 back buffer、dirty area、双屏交错刷新。
4. 如果固件后续改变 framebuffer 注册顺序，必须重新采集 `/proc/fb`、`/sys/class/graphics/fb*/name` 和应用打开节点，再复核本条目。

## Review 周期

- owner：leiwenjun
- review_after：2026-10-11
- 下一次复核内容：owner review、目标设备固件变更后的 `/proc/fb` 和 `/sys/class/graphics/fb*/name` 复核、是否需要把该候选提升为 active。

<!-- pcr02-owner-device-release-validation:start -->
## Owner、实机与发布验证门禁

> 本节定义真实验证路径，不表示任何命令已经执行，也不是 owner decision、active promotion 或 release 授权。

### 1. Owner 决策路径

- `decision_owner=unassigned`；既有内容复核记录只证明候选可读，不证明 framebuffer 边界已被产品 owner 接受。
- owner 必须确认适用硬件/固件版本，并对 `/dev/fb0`、`/dev/fb1`、`/dev/fb2` 的角色、应用依赖和未来失效条件作出明确决定。

### 2. Source 与运行态证据

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、kernel/DTS/config commit、应用 commit 和构建制品 SHA256。
- 在同一目标制品上保存 `/proc/fb`、`/sys/class/graphics/fb*/name`、geometry/stride/smem_len，以及应用进程实际打开节点的 `/proc/<pid>/fd` 或等价证据。
- 将 `DisplayProvider` 节点配置、两个 ST77912 DTS 节点、fbtft 驱动注册和 `mi_fb` 配置引用到确切 commit/line；目录存在或旧会话输出不能替代当前 source identity。

### 3. 端到端边界验证

- 分别向 `/dev/fb0`、`/dev/fb1` 和 `/dev/fb2` 写入可区分的确定性测试图，确认物理输出目标和日志链路。
- 覆盖冷启动、重启、模块/驱动初始化顺序变化和发布配置，确认 framebuffer 编号未漂移；若编号可能变化，应用必须改用稳定身份发现或显式失败。
- 验证 `mi_fb` 参数变化只影响 SStar FB 路径，不被误报为 ST77912 双屏优化；验证 fbtft/SPI 参数变化能在双小屏观察到预期效果。

### 4. Release 与回滚

- 发布说明必须列出 display provider、DTS/fbtft、SStar FB/MI_FB 的边界，并标明适用 commit 与设备版本。
- 回滚到上一制品后重复 `/proc/fb`、sysfs、应用打开节点和三路测试图检查；不能只证明系统启动。
- owner、source、目标设备和 release 证据未闭环时保持 `reviewing`，不得因当前一次 `/proc/fb` 观察自动提升 active。

### 证据落地契约

- 证据记录必须包含 `owner_identity`、`source_commit`、`artifact_sha256`、`device_identity`、`environment`、`commands`、`exit_codes`、`result_summary`、`rollback_result` 和可恢复引用。
- raw log、视频、截图和二进制只保存在受控外部制品位置；Hub 正文只保存脱敏摘要、hash 和引用。
- 最终复核命令：`rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13`。
<!-- pcr02-owner-device-release-validation:end -->
