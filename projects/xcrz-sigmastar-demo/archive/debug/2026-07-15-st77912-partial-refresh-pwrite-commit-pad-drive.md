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
summary_zh: 局部刷新候选已改为一次 pwrite 完整脏行带并在复制后精确标脏。最新固件实机确认 partial、同步 commit 与 SPI0_CK 2mA/MSPI_CK 12mA 均生效；剩余割裂集中在 RobotWaitingAction 大面积动画，证据优先指向无 TE/VSYNC 的面板扫描撕裂，旧区域漏刷仍待单变量验证。
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

## 2026-07-15 最新固件实机复核

最新固件已由外部流程完成编译和安装；本轮仅通过 ADB 做只读取证，没有刷机、重启、替换二进制或写 framebuffer。

- 运行内核为 Linux 5.10.117，构建时间 `2026-07-15 12:26:47 HKT`；应用日志版本为 `6b1f13d-dirty`。
- 两块屏均识别为 `fb_st77912`、240×240、RGB565、`line_length=480`、`smem_len=115200`。
- 当前应用初始化参数同时满足：`full_refresh=0`、`partial_enabled=1`、`fbtft_commit_supported=1`、`fbtft_row_write_compatible=1`、`vsync_supported=0`。
- `sensor_disp1` 线程在 `/proc/<pid>/task/<tid>/syscall` 中实际进入请求号 `0x4621`（`FBIO_FBTFT_COMMIT`），目标 fd 交替对应 `/dev/fb0` 与 `/dev/fb1`；内核等待点可见 `__flush_work`。这证明 pwrite 后同步 commit 不是仅存在于源码或日志，而是运行时真实生效。
- 运行时 DT 读回两屏均为 54MHz、25fps、rotate 180；PAD 寄存器读回 `PAD_MSPI_CK` level 2（12mA）和 `PAD_SPI0_CK` 编码 000（2mA），与 owner 配置一致。
- 应用日志和 dmesg 未发现 pwrite、commit、SPI timeout、`write_vmem` 或 ST77912 错误。
- 连续采集 16 组 `/dev/fb0`、`/dev/fb1` framebuffer，稳定帧及动作帧的几何内容整体连贯，没有复现照片中长期保留的多条水平分段。抓取过程本身与应用写入并发，因此个别过渡帧只作为低置信瞬时证据，不据此宣称 framebuffer 原子快照。

`display_error/1.jpg` 至 `5.jpg` 的 EXIF 与场景日志对齐后，问题范围进一步收敛：

- 1、2 拍摄于 `BlinkAction_nor`，画面基本正常。
- 3、4、5 分别拍摄于 `RobotWaitingAction` 切入约 7.4s、9.4s、10.4s 后，均处于 phase 2 的睁眼/水平移动过程。
- 3–5 的曝光时间为 1/50s；条带沿相机水平方向分段，并在两块 LCD 上呈近似同一相机扫描线位置。结合 framebuffer 未保留同形态条带，这是“面板 GRAM 写入与 LCD/相机扫描不同步”的强支持证据，但还不能替代动作停止后的肉眼观察。

当前局部刷新仍是“脏行带”而不是真正二维矩形传输。Robot 资源中 sclera 为 184×184，eyelid 图片画布为 240×240；fbtft 对任意 dirty y 范围都发送 240 像素整行。因此：

- 眼皮图片切换会使本轮接近整屏传输，单屏 115200 bytes。
- 仅水平移动 sclera 时也至少覆盖约 184 行，单屏约 88320 bytes，即整屏 payload 的 76.7%。
- 双屏共用一个 MSPI 控制器并由单 worker 串行 commit，配置的 25fps 不是该场景下可保证的双屏有效帧率；长行带持续传输会扩大无 TE/VSYNC 时的可见撕裂窗口。

LVGL 8.3.10 官方实现同时确认：单 draw buffer 会在下一次绘制前等待 `lv_disp_flush_ready()`。结合当前 last-area commit 的运行时证据，下一帧直接覆盖正在发送的 staging/framebuffer 已降为低概率，不再列为首要根因。

### 当前假设排序

1. **高概率：无 TE/VSYNC 的物理扫描撕裂。** 当前 `vsync_supported=0`，commit 只保证 SPI transport 完成，不保证面板在 blanking 区间原子显示新帧；大面积连续动画最容易触发。
2. **中概率：RobotWaitingAction 的旧/新区 dirty coverage 不完整。** 若动作停止后条带仍持续存在，或把 framebuffer 中相同完整帧重新全屏发送一次即可清除，则该项上升为首要根因。
3. **低概率：54MHz 信号完整性。** PAD 配置正确，未见随机像素噪声、SPI 错误或 timeout，且故障是规则水平分段；仍可用固定其他变量的 36MHz A/B 最终排除。
4. **已基本排除：commit 未运行、旧应用/新内核不匹配、下一帧覆盖 staging、随机 SPI 写失败。** 均有运行时反证。

### 下一步判定门

首选在条带可见时执行一次“读取当前 framebuffer，再把完全相同内容整屏写回对应 fb”的单变量试验。该试验不改像素内容和配置，但会触发一次完整 SPI 更新：

- 若静止残留立即消失，证明 dirty coverage 漏刷，应继续修复应用 invalidation/合并范围。
- 若只在运动中出现且停止后自然消失，或相同内容全刷不能改变现象，优先转向 TE 硬件同步、二维矩形传输和按场景限制动画更新面积/帧率。

执行该试验属于设备状态写入，必须取得 owner 明确授权；后续已获授权并按下述记录执行。

### 同内容整屏重发实验

2026-07-15 获得 owner 明确授权后，保持应用进程、显示配置和场景不变，只把每块 framebuffer 当时的 115200 字节内容保存后原样写回同一设备节点。

- `15:03:21` 和 `15:09:11` 两次样本捕获到 fb0/fb1 相同的稳定帧，SHA256 均为 `f453e445...a2baeb1`。两屏读写均为 115200 字节且返回成功；第二次紧邻观测到 MSPI IRQ 增加 68。由于样本处于静止段，不能用于判断运动割裂，作为负样本保留，后续不再靠人工时点盲试。
- `15:11:05` 通过连续 framebuffer hash 变化自动确认进入运动段。检测时 fb0/fb1 hash 分别为 `3ad0b3e8...46799` 与 `e405024f...58657`；5ms 后保存的完整快照分别为 `ac7b11b9...aa2a` 与 `5409c2aa...c708`，两份文件均精确为 115200 字节。
- 两份运动快照随后分别一次写回 `/dev/fb0`、`/dev/fb1`，所有 `dd` 均为 `1+0 records` 且无错误。MSPI IRQ 从 4,785,564 增至 4,786,002，增加 438，证明重发触发了实际 SPI 传输，不是仅修改内存文件。
- 实验后应用 PID 保持不变，sensor log 与 dmesg 未出现 display、pwrite、commit、SPI timeout 或 `write_vmem` 新错误。

实验边界：应用在运动期间仍正常运行，外部重发没有暂停应用，也不与应用内部 flush mutex 共享锁。因此该实验适合判定“完整内容重发是否能清除面板上的残留”，但不构成应用逻辑帧的原子抓拍证明。

后续在 owner 明确观察到条带仍存在的窗口，于 `15:21:08` 再次执行同内容整屏重发。两屏各读写 115200 字节成功，MSPI IRQ 从 5,093,572 增至 5,093,782，增加 210。owner 现场结论为：条带会随着动画刷新重新出现，进入非运动阶段后的刷新会把此前残留覆盖掉；眼球横向移动时最容易出现异常。

该结果把 persistent dirty coverage 降为低概率，把无 TE/VSYNC 的动态扫描撕裂提升为首要根因：横向移动会让相邻逻辑帧在 x 方向差异最大，ST77912 按 y 行顺序写 GRAM 时，上下行若分别属于新旧 x 位置，就会形成最醒目的水平断层；后续刷新又能自然覆盖该断层。随机 SPI 位错误、永久旧区漏刷和 staging 生命周期问题均不符合这一“仅运动中增强、后续刷新清除”的时间特征。

根因状态更新为高置信 `known`，修复状态仍为 `needs-fix`。优先修复方向是为每块 LCD 引入 TE/VSYNC 同步；若现有硬件未路由 TE，只能先通过二维矩形 dirty、裁剪 240×240 透明 eyelid 画布和按场景限帧缩短暴露窗口，不能把扩大 `full_refresh` 当作无撕裂方案。

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
- PAD 配置：源码已落地，静态检查和运行时寄存器读回均符合 2mA/12mA 目标。
- 构建/刷机：未执行。
- `0001-fix-display-ST77912.patch`：已更新为当前 release 显示相关 10 文件的可 `git am` 邮件补丁；明确排除生成文件、二进制、调试脚本及独立的 sensor `display.patch`。

## 归档证据

- Source: 2026-07-15 用户 owner direction、release/source 静态核对与本次候选实现。
- Topic: `st77912-partial-refresh-pwrite-commit-pad-drive`。
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/archive/debug/2026-07-15-st77912-partial-refresh-pwrite-commit-pad-drive.md`。
- Sanitization: 未保存设备地址、凭据、原始日志、二进制或 framebuffer。
- Provenance: xcrz sensor 回退基线、release kernel 工作树、本次静态修改，以及 2026-07-15 最新固件 ADB/照片时间轴只读取证。
- Verification: `git diff --check`、kernel `checkpatch`、`git apply --check`、干净基线 `git am`、10 文件逐项比对、运行时 display init、commit syscall、DT/PAD 寄存器和 framebuffer 抓帧；物理视觉 HIL 仍需单变量闭环。
- Memory Candidate: no。
- Gate Result: needs-fix；软件候选静态通过，视觉正确性和寄存器读回待实机闭环。
