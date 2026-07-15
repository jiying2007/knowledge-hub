---
id: xcrz-sigmastar-demo-st77912-partial-refresh-pwrite-commit-pad-drive-20260715
title: PCR02 ST77912 局部刷新 pwrite 提交与 SPI 时钟驱动配置
kind: debug-record
domain: projects/xcrz-sigmastar-demo
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-08-15'
review_status: manual-entry-pending-review
promotion: none
tags:
- pcr02
- display
- st77912
- lvgl
- partial-refresh
- fbtft
- pwrite
- pad-drive
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: true
summary_zh: 局部刷新候选存在 mmap 复制期间 deferred work 可提前启动的半帧窗口；候选改为一次 pwrite 完整脏行带并在复制后精确标脏，同时在 release 配置 SPI0_CK 2mA 与 MSPI_CK
  12mA。静态检查通过，实机视觉与寄存器读回待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
---

# PCR02 ST77912 局部刷新 pwrite 提交与 SPI 时钟驱动配置

## 摘要

2026-07-15 在应用 display 源码已回退、release 内核局部刷新改动仍保留的状态下继续做静态排查。确认旧应用不会调用新增的 `FBIO_FBTFT_COMMIT`，因此当前运行时若确实使用回退后的应用二进制，commit ioctl 本身不是割裂或抖动的直接触发点；但设备离线，尚未核对实际部署二进制。

长期局部刷新候选中发现一个此前未封闭的时序窗口：应用通过 `mmap` 逐行复制 staging 到 framebuffer 时，第一页写入即由 `fb_defio` 安排 delayed work，复制全部完成后才调用同步 commit。若高负载下用户线程在复制中被抢占超过 deferred 周期，fbtft 可能先发送尚未完整写入的逻辑帧。后置 commit 只能等待或补刷，无法撤销已经发生的中途刷新。

候选方案改为一次 `pwrite()` 提交完整的脏行带；内核 `fbtft_fb_write()` 在 `fb_sys_write()` 完整复制后才标记精确脏行，随后同步 commit。该方案消除了 deferred work 在用户数据复制中途启动的窗口，但没有新增 LCD TE/VSYNC 同步，因此面板扫描相位造成的物理 tearing 仍需实机验证，不能仅凭静态检查宣称解决。

## 当前基线

- `modules/sensor/display` 三个源码文件无工作树 diff，保持正确性回退基线。
- 长期候选仅保存在未跟踪的 `modules/sensor/display.patch`；更新后 SHA256 为 `eb7ede0d522f04660d3aaca7022f0a6fa2cf5989147f3054265811e9a3fe446b`。
- release 内核继续保留 `FBIO_FBTFT_COMMIT`、同步 deferred-I/O flush、dirty line 边界和 54MHz/25fps 改动。
- `0001-fix-display-ST77912.patch` 已按当前 release 的 10 个显示相关源码文件重新生成，SHA256 为 `b56b1531874f57e23643313ef6f431d749dbd5d774456ca12ff257e04a4a68ab`；涵盖 54MHz/25fps、SPI0_CK 2mA、MSPI_CK 12mA、fbtft 精确脏行与同步 commit。sensor 侧 pwrite 候选仍单独保存在 `modules/sensor/display.patch`，不在该 release 补丁范围内。
- 设备未连接；旧 ADB 地址连接超时。本轮未刷机、未重启、未替换二进制。

## 根因细化

原候选路径为：

```text
LVGL refresh cycle
-> area 同步复制到 userspace staging
-> 最后 area 排队
-> mmap memcpy staging -> framebuffer
-> FBIO_FBTFT_COMMIT
-> cancel/schedule/flush deferred work
-> SPI 完成后 flush_ready
```

问题发生在 `mmap memcpy` 与 commit 之间：

1. mmap 页面首次写入触发 `page_mkwrite`，页面加入 `fbdefio->pagelist` 并按约 40ms 延迟安排 work。
2. 应用继续逐行复制剩余数据；正常情况下很快完成，但高负载抢占没有硬上限。
3. delayed work 一旦在复制完成前开始，fbtft 会从共享 framebuffer 读取当时可见的数据并发送 SPI。
4. 之后调用的 commit 只能同步当前或下一次 work，不能让已经发送的半帧恢复原子性。

这是一条源码可证明的竞态窗口，能够解释负载相关的偶发割裂。它不是面板物理 tearing 的唯一可能根因；ST77912 当前驱动没有 TE/VSYNC 完成事件，面板扫描与 SPI 写 GRAM 的相位仍可能造成可见撕裂。

## 本次实现

### 应用候选补丁

`modules/sensor/display.patch` 保持不直接应用到回退源码，候选实现调整为：

- 最后一个 LVGL area 仍以 `lv_disp_flush_is_last()` 封闭逻辑 refresh cycle。
- staging 提交从逐行 mmap `memcpy` 改为一次 `pwrite()` 完整脏行带。
- 因 fbtft 最终按完整行传输，应用提交 `y1..y2` 的全宽连续行；这与物理 SPI payload 一致。
- 仅在 `xoffset=0`、`yoffset=0`、RGB565 且 `line_length == xres * sizeof(lv_color_t)` 时启用该路径；不兼容格式保持 `full_refresh=1`。
- commit 返回后才对最后 area 调用 `lv_disp_flush_ready()`，确保 staging 与 SPI 消费边界不被下一帧复用。

### release 内核

- `fbtft_fb_write()` 根据写入起始 offset 与成功写入长度计算精确 dirty 行，不再把任意 write 无条件标成整屏。
- dirty 标记发生在 `fb_sys_write()` 完成之后；单次 `pwrite()` 期间不会提前安排 deferred update。
- `FBIO_FBTFT_COMMIT` 继续负责取消延迟、立即调度并等待 deferred work 完成。

### SPI 时钟 PAD 驱动

- SPI NAND Flash `PAD_SPI0_CK`：U-Boot 与 kernel boot-storage FSP 初始化均清除 `BIT7 | BIT8 | BIT10`，编码 `000=2mA`。
- SPI LCD `PAD_MSPI_CK`：`iford.dtsi` 的 MSPI0 节点显式配置 `sstar,clk-drive-level = <2>`；iford 的 2-bit 映射为 `0/1/2/3 = 4/8/12/16mA`，因此 level 2 为 12mA。
- MSPI driver 仅在 DTS 显式声明该属性时设置 drive level；未声明的其他目标保持原行为。非法 group/level 或 GPIO 写入失败会终止 probe，避免静默使用错误电气参数。

## 静态验证

- release 全工作树 `git diff --check`：通过。
- release 核心驱动差异（MSPI、fbtft、fb_defio、fb headers）执行 `checkpatch.pl --no-tree --terse`：0 error，0 warning。
- 将 DTS、vendor FSP/GPIO 一并纳入同一检查时为 7 error、10 warning，均对应这些文件沿用的空格缩进风格；`git diff --check` 仍通过。本轮不为补丁归档改写 vendor 局部风格，该项作为已知静态风格负项保留。
- 更新后的 `0001-fix-display-ST77912.patch` 已在从 release `HEAD` 提取的干净基线上通过 `git apply --check --whitespace=error-all` 与 `git am`；应用后的 10 个文件与 release 当前工作树逐文件一致。
- `display.patch`：`git apply --check` 与 `--whitespace=error-all` 均通过。
- `display.patch` 仍是唯一 sensor repo 变更，三个 display 源文件未直接修改。
- 目标 `.config` 包含 `CONFIG_SSTAR_MSPI=y`、`CONFIG_SSTAR_GPIO=y`、`CONFIG_FB_TFT_ST77912=y`。
- 按用户边界未编译 release 固件，未生成或刷写新制品。

## 下一轮单变量验证

1. 先用回退应用 + 当前 release 内核验证 54MHz/25fps 与 PAD 配置，读取：
   - `riu_r 0x103E 0x22`：`PAD_MSPI_CK` bits 8:7 应为 `10`，即 12mA。
   - `riu_r 0x103E 0x28`：`PAD_SPI0_CK` bits 10/8/7 应为 `000`，即 2mA。
2. 固定应用和 drive，只把 LCD 从 54MHz 降到 36MHz 做视觉 A/B；若割裂明显随频率消失，优先归因信号完整性或控制器时序。
3. 正确性基线稳定后再成套启用新 release 内核与更新后的 `display.patch`；初始化日志必须同时满足 `fbtft_commit_supported=1`、`fbtft_row_write_compatible=1`、`partial_enabled=1`。
4. 固定动画脚本记录双屏视频、framebuffer hash、commit 耗时、dirty 高度、`sensor_disp0`/`sensor_disp1` CPU 和全局 idle。
5. 若 framebuffer 始终完整且 pwrite/commit 边界无中途刷新，但面板仍出现固定扫描线撕裂，软件方案需要转向 TE 硬件同步或接受按场景降低刷新率/缩小 dirty 行带；不能继续把 completion barrier 等同于面板 VSYNC。

## 状态与边界

- 显示正确性：`needs-fix`，实机验证待补。
- PAD 配置：源码已落地、静态通过，运行时寄存器读回待补。
- 构建/刷机：未执行。
- `0001-fix-display-ST77912.patch`：已更新为当前 release 显示相关 10 文件的可 `git am` 邮件补丁；明确排除生成文件、二进制、调试脚本及独立的 sensor `display.patch`。

## 归档证据

- Source: 2026-07-15 用户 owner direction、release/source 静态核对与本次候选实现。
- Topic: `st77912-partial-refresh-pwrite-commit-pad-drive`。
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-15-st77912-partial-refresh-pwrite-commit-pad-drive.md`。
- Sanitization: 未保存设备地址、凭据、原始日志、二进制或 framebuffer。
- Provenance: xcrz sensor 回退基线、release kernel 工作树与本次静态修改。
- Verification: `git diff --check`、kernel `checkpatch`、`git apply --check`、干净基线 `git am` 与 10 文件逐项比对；固件和实机 HIL pending。
- Memory Candidate: no。
- Gate Result: needs-fix；软件候选静态通过，视觉正确性和寄存器读回待实机闭环。
