---
related:
- xcrz-sigmastar-demo-st77912-dual-display-cpu-adb-triage-20260713
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: xcrz-display-partial-refresh-20260714
severity: visual-correctness-regression
affected_version: latest test firmware, prog_pcr02 sha256 7b1d46d903f22d3488da2d4fd67fecfd1afab773b01e2cebfafca4d0acc67794
implementation_status: source-implemented-static-verified-runtime-pending
id: xcrz-sigmastar-demo-st77912-partial-refresh-visual-regression-20260714
title: PCR02 ST77912 局部刷新图像割裂与残留 ADB 排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-14-st77912-partial-refresh-visual-regression.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 当前会话的只读 ADB 实机取证、本地源码核对及用户现场观察。
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-08-14'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- display
- st77912
- lvgl
- partial-refresh
- visual-regression
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-14-st77912-partial-refresh-visual-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- adb-read-only-runtime-capture-20260714
- source-timing-review-20260714
- userspace-refresh-cycle-implementation-build-20260714
- release-kernel-source-static-sync-20260714
artifact_refs:
- device:/customer/bin/prog_pcr02#sha256=7b1d46d903f22d3488da2d4fd67fecfd1afab773b01e2cebfafca4d0acc67794
evidence_strength: runtime-confirmed-with-source-mechanism-and-scoped-limitations
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-14-st77912-partial-refresh-visual-regression.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- runtime display init configuration
- framebuffer snapshot and hash sequence
- LVGL 8.3.10 flush state machine
- Linux 5.10 fb_defio and fbtft source
created_at: '2026-07-14'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-14'
manual_validation_pending: true
summary_zh: 最新 partial-refresh 部署在降低静态窗口显示线程负载的同时出现图像割裂和局部残留；ADB 抓取 framebuffer 多数完整，源码时序表明 LVGL area flush 与 fbtft deferred
  SPI 提交缺少逻辑帧边界及物理完成屏障。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 ST77912 局部刷新图像割裂与残留 ADB 排障记录

## 摘要

2026-07-14 对最新测试固件做只读 ADB 取证，确认当前部署已从安全的全屏刷新切换为 `full_refresh=0`、`partial_enabled=1`。现场观察到图像割裂和局部旧像残留；连续读取 `/dev/fb0`、`/dev/fb1` 时，应用 framebuffer 多数是完整、连续的动画帧，未发现相同形态的大块割裂，因此问题主要落在 framebuffer 之后的 fbtft deferred I/O 与 SPI 提交边界，而不是应用停止渲染或 LCD ESD 黑屏故障。

当前应用的 staging/queue 设计不能在正常 LVGL 8.3.10 路径中合并同一轮刷新产生的多个 dirty area。两个 draw buffer 都是整屏大小，LVGL 每提交一个 area 后会等待 `lv_disp_flush_ready()`；应用 worker 只把这个 area 写入 mmap framebuffer 就立即回报 ready，而内核约在 40 ms 后才读取共享 framebuffer 并经 SPI 发送。这样一个逻辑帧可能被拆成多个物理刷新，且下一帧可能在 SPI 读取期间改写同一 framebuffer，造成面板端的新旧区域混合。

另有一条独立且已确认的应用层显示瑕疵：眼睛对象超出 240×240 根 screen 的内容范围时，LVGL screen 默认 `SCROLLABLE` 且 scrollbar mode 为 `AUTO`，会在 framebuffer 中绘制一条靠右的灰色竖向滚动条。它会增加局部 dirty area，也可能在物理刷新丢失时成为残留，但不是大块图像割裂的唯一原因。

## 现象

- 最新固件可正常点亮 LCD，但动画过程中可见上下或局部图像不属于同一帧，表现为割裂。
- 部分旧区域未及时被新内容覆盖，形成短时或持续残留。
- framebuffer 快照中曾捕获靠右灰色圆角竖条；该条会在后续 framebuffer 帧中正常消失，但现场面板可能保留。
- 本次未发现 fbtft/SPI 超时、`write_vmem` 失败或应用 flush 错误日志。

## 影响范围

- 项目：`xcrz-sigmastar-demo`。
- 路径：`modules/sensor/display`、Linux fbdev deferred I/O、fbtft/ST77912、共享 SPI0。
- 影响：显示正确性不满足发布条件；当前 partial-refresh 版本只能作为实验版本，不能以 CPU 降低为由替代正确性基线。
- 不包含：此前 LCD 完全黑屏的 ESD 硬件问题。移除 ESD 后点亮正常，硬件侧另行修改。
- `0001-fix-display-ST77912.patch` 中的 dirty-line 边界保护、fps 除法保护、resume 分辨率修正不是本次割裂的直接证据；54 MHz/25 fps 会改变时序，但真正暴露一致性问题的是应用启用 partial refresh 后缺少逻辑帧提交和物理完成屏障。

## 环境

| 项目 | 取证值 |
| --- | --- |
| 内核 | Linux 5.10.117，ARMv7 双核，2026-07-13 构建 |
| 应用制品 | `/customer/bin/prog_pcr02`，SHA256 `7b1d46d903f22d3488da2d4fd67fecfd1afab773b01e2cebfafca4d0acc67794` |
| framebuffer | fb0/fb1 均为 `fb_st77912`，240×240，RGB565，stride 480 |
| 应用显示配置 | `double_buf=false`、`direct_mode=0`、`full_refresh=0`、`partial_enabled=1`、`vsync_supported=false` |
| 总线参数 | 两屏共享 SPI0，54 MHz；fbtft `fps=25`，deferred delay 约 40 ms |
| LVGL | 8.3.10 source snapshot |
| 取证边界 | ADB 只读；未重启、未改场景、未替换二进制、未写设备配置 |

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-07-14 | 核对应用初始化日志、framebuffer sysfs、线程名和内核日志 | 确认 latest 部署为 partial refresh；无明确 SPI/fbtft 错误 |
| 2026-07-14 | 连续读取两块 framebuffer 并做 hash/图像检查 | 应用缓冲持续更新且多数帧完整；割裂未稳定存在于 framebuffer |
| 2026-07-14 | 对照 `DisplayProvider`、LVGL 8.3.10、fb_defio、fbtft 源码 | 确认应用 ready 边界早于物理 SPI 完成，现有 batch 无法聚合同一 LVGL refresh cycle |
| 2026-07-14 | 对显示线程做短时 CPU tick 差分 | mostly-static/blink 窗口负载较低，但不是与旧版同场景的严格性能 A/B |

## 证据

### 运行时证据

- 两屏初始化日志均报告 `full_refresh=0`、`partial_enabled=1`，而同一日志历史行可见旧版本为 `full_refresh=1`、`partial_enabled=0`。
- `sensor_disp0` 仍是 LVGL/场景主线程，`sensor_disp1` 是共享 flush worker；未观察到无条件忙循环。
- 20 次、间隔约 500 ms 的 framebuffer hash 采样显示动画期间 hash 正常变化，静止时稳定；fb0/fb1 因顺序采样偶尔不同，不代表单屏内容损坏。
- 连续 framebuffer 图像多数为完整眼睛动画帧。靠右灰色竖条能在 framebuffer 内出现并在后续帧消失，符合 LVGL AUTO scrollbar，而非 SPI bit error。
- 内核日志没有匹配到 ST77912/fbtft/SPI timeout、`write_vmem failed` 或相关 warning。

### 源码证据

1. `DisplayProvider` 为每屏分配两个整屏 LVGL draw buffer 和一个 staging buffer，并设置 `full_refresh=0`。
2. `displayFlush()` 将 raw `color_p` 排队；worker 对当前已排队的同屏任务做 staging/area merge，拷入 mmap framebuffer 后逐个调用 `lv_disp_flush_ready()`。
3. LVGL 8.3.10 对整屏大小双 buffer 在下一次 area render 前等待 `draw_buf->flushing` 清零。因此正常情况下同一 display 同时只有一个未 ready 的任务，队列无法收集同一 refresh cycle 的多个 area。
4. `lv_disp_flush_is_last()` 已能提供逻辑刷新周期的最后 area 标志，但当前实现未使用。
5. fbdev page 首次写入后按 fbtft `fps=25` 调度 delayed work；fbtft 根据脏页折算成全宽行范围，再从共享 `screen_buffer` 分块换字节序并同步写 SPI。
6. 应用调用 `lv_disp_flush_ready()` 时只完成了用户态 memcpy，既没有等 deferred work 启动，也没有等 SPI 发送结束。Linux 5.10 当前 `fb_deferred_io_fsync()` 也只是取消延迟并重新调度立即 work，返回前不等待新 work 完成，不能当物理完成屏障。

### CPU 样本边界

约 15 秒 mostly-static/blink 窗口中：`sensor_disp0` 增加约 96 tick，`sensor_disp1` 增加约 9 tick，全局约 68.9% idle。该样本表明当前场景没有复现旧记录中的整机近满载，但场景和媒体负载不同，不能据此声明 partial refresh 已达到性能验收。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| LCD ESD 导致本次割裂/残留 | 对照硬件已知现象与当前点亮状态 | ESD 问题表现为完全不显示；移除后可点亮，和当前动画割裂不同 | 已排除为同一故障 |
| 应用停止渲染或 framebuffer 本身长期损坏 | 连续读取 framebuffer、hash 和图像 | framebuffer 持续产生完整动画帧，未复现相同大块割裂 | 已排除主要路径 |
| SPI bit error 或驱动写失败 | 检查 dmesg/应用日志和 framebuffer 图案 | 无 timeout/write error；灰条形态和 LVGL scrollbar 一致 | 未发现证据 |
| 当前 queue 能聚合同一 LVGL 逻辑帧的 dirty area | 对照整屏双 buffer 的 LVGL flushing 状态机 | LVGL 每个 area 等待 ready，正常队列深度不足以完成预期合并 | 已否定 |
| deferred framebuffer 与 SPI 提交边界造成面板端混帧 | 对照 mmap page dirty、40 ms delayed work、共享 buffer 分块 SPI 读取 | 完整解释“fb 完整但面板割裂/残留”，与现场现象一致 | 高置信；待 trace/逻辑分析仪最终确认 |
| LVGL 默认 scrollbar 造成右侧灰条 | framebuffer 图像与 LVGL 默认 flags/mode 对照 | screen 默认 scrollable、AUTO；眼睛子对象可越界 | 已确认 |

## 根因

根因分为两层：

1. **确定的软件设计缺陷**：当前 staging/queue 按“worker 当时能看到的任务”合并，而不是按 LVGL refresh cycle 合并；在整屏双 draw buffer 配置下，这个 batch 机制结构上无法聚合同一逻辑帧的多个 area。
2. **面板割裂与残留的高置信机制**：应用在每个 area 写入 mmap framebuffer 后过早 `flush_ready`，fbtft 约 40 ms 后才读取共享 framebuffer 并执行 SPI。逻辑帧被拆为多次物理发送，且缺少“SPI 已完成、buffer 可复用”的确认，面板可能同时保留前后帧的不同区域。
3. **独立的已确认瑕疵**：screen 根对象默认滚动属性导致 AUTO scrollbar 出现在应用 framebuffer。它应单独关闭，不能依赖刷新机制掩盖。

因没有 ftrace SPI 完成事件或逻辑分析仪波形，本记录不把第 2 点表述为硬件时序的最终唯一根因；但现有运行时与源码证据已经足以判定当前 partial-refresh 设计未通过显示正确性验收。

## 修复或规避

初次只读取证阶段未修改或部署代码；同日后续已按长期方案实现源码，但仍未生成或部署正式固件。方案分两阶段处理：

1. **立即恢复正确性基线**：仅对 `fb_st77912` 单 framebuffer 路径恢复 `disp_drv->full_refresh=1`；保留 54 MHz/25 fps、dirty-line 越界保护、resume 分辨率修正等已验证的内核安全改动。该动作会增加 LVGL 渲染和 SPI 带宽，但风险最低。
2. **清除明确应用瑕疵**：显示初始化后对两个 screen root 清除 `LV_OBJ_FLAG_SCROLLABLE`，并设置 `LV_SCROLLBAR_MODE_OFF`。该修复与 partial/full refresh 独立。
3. **长期 partial-refresh 设计**：`flush_cb` 先把每个 area 同步拷到 staging 并合并范围；使用 `lv_disp_flush_is_last()` 判断一个 LVGL refresh cycle 结束，只在最后 area 将本轮一致的 staging 状态提交给 framebuffer。随后仍需增加内核可等待的 fbtft commit/completion 或等价双缓冲屏障，避免下一帧覆盖 SPI 正在读取的共享 framebuffer。
4. **不建议**：继续依赖当前 queue 批处理、仅调低 fps、仅调用 `fsync()`，或把问题归因于 ESD。这些措施都没有补齐逻辑帧和物理完成边界。

### 同日后续实施状态（2026-07-14）

应用层已在开发工作树实现以下闭环：

- `flush_cb` 在返回 ready 前将每个 LVGL area 同步复制到应用 staging，确保 `color_p` 不会被复用后再读取。
- 使用 `lv_disp_flush_is_last()` 识别同一 refresh cycle 的最后 area；本轮 dirty area 合并后只排队一次 framebuffer commit。
- 共享 flush worker 先把 staging 的合并区域写入 mmap framebuffer，再调用阻塞式 `FBIO_FBTFT_COMMIT`；ioctl 返回后才调用最后一次 `lv_disp_flush_ready()`。
- 双屏共用一个 worker，物理提交天然串行，避免两屏同时抢占 SPI。
- 初始化时探测 commit ioctl；新应用运行在旧内核时收到 `ENOTTY`，自动切回 `full_refresh=1`、关闭 partial refresh。
- 两个 root screen 显式清除 `LV_OBJ_FLAG_SCROLLABLE` 并关闭 scrollbar。

该应用实现已完成一次开发工作树编译，`display_provider.cpp` 进入实际编译和链接且构建退出码为 0。之后用户将 release 工作树的验收边界收敛为静态检查，因此未在 release 工作树重复编译。

内核层已同步到 PCR02 SSC305 release 工作树，涉及四个文件：

1. UAPI `fb.h`：新增私有 `FBIO_FBTFT_COMMIT = _IO('F', 0x21)`。
2. 内核 `fb.h` 与 `fb_defio.c`：新增并导出 `fb_deferred_io_flush_sync()`，立即调度并等待 deferred work 完成。
3. `fbtft-core.c`：接入 commit ioctl，并把空 dirty 状态统一为 `start=yres, end=0`，防止无 dirty 的能力探测误刷第 0 行。

release 工作树四个目标文件与开发工作树逐字节一致；标准 `checkpatch` 为 0 error、0 warning，`git diff --check` 通过。目标配置中 `CONFIG_FB_DEFERRED_IO=y`、`CONFIG_FB_TFT=y`、`CONFIG_FB_TFT_ST77912=y`。未执行 release 固件编译、刷写或实机 HIL。

版本组合必须作为一个验收单元：

- **新应用 + 旧内核**：能力探测失败后自动回退全刷，显示正确性优先。
- **新应用 + 新内核**：进入长期 partial-refresh 路径，仍需固件和实机验证。
- **旧应用 + 新内核**：旧应用不会主动调用完成屏障；若它已经启用原有 partial refresh，割裂与残留风险仍在。因此 release 打包不能只换内核而继续携带旧显示应用。

## 验证

当前结论已通过设备运行配置、连续 framebuffer 取样、线程 CPU tick、应用日志和三层源码时序交叉核对。当前 partial-refresh 版本的验收结论为：**显示正确性失败，不可作为 release baseline**。

长期方案当前达到“源码实现并完成静态验证”，尚未达到“固件或实机通过”。旧内核上的独立 ioctl 探针返回 `ENOTTY`，构成兼容回退的负路径证据；新内核返回成功、应用初始化进入 `partial_enabled=1`、面板无割裂/残留以及 CPU A/B 均待后续 HIL 补齐。

后续修复至少需要固定同一动画脚本执行三组 A/B：

1. 旧基线：`full_refresh=1`。
2. 最小安全修复：`full_refresh=1` + 禁用 root scrollbar。
3. 新 partial 设计：refresh-cycle staging commit + 可等待的物理完成屏障。

每组记录双屏视频、framebuffer hash/图像、`sensor_disp0`/`sensor_disp1` tick、全局 user/system/idle、fbtft update 起止时间、SPI 完成时间和实际刷新率。通过判据是连续场景切换和动画压力测试无割裂、无旧区域残留、无右侧灰条，再比较 CPU 与带宽收益。

### 离线待验证（可选）

仅在现场或离线排障先记录、后补验证时保留此块；未验证内容必须留在假设、风险或后续动作中。

```yaml
manual_validation_pending: true
manual_validation_reason: 长期方案已实现源码并完成静态检查，但 release 固件尚未编译、部署及完成固定场景 A/B。
required_followup: 使用同时包含新显示应用和新内核的 release 制品，验证 commit ioctl、兼容回退、视觉正确性和 CPU 收益。
owner: leiwenjun
review_after: 2026-08-14
```

## 后续动作

- 本记录保持 `reviewing`，不自动提升为 runbook、validation、AGENTS 或 owner decision。
- release 构建必须确认新显示应用与新内核成套进入同一制品；构建后补充制品 hash。
- 先验证“新应用 + 旧内核”自动回退，再验证“新应用 + 新内核”固定场景 A/B；通过后补充视频证据和 CPU 指标。
- 长期 partial-refresh 方案通过视觉与性能门禁后，再决定是否 supersede 2026-07-13 的“待验证”条目；当前两条记录保留时间顺序和证据演进关系。

## 归档证据模板

- Source: 当前会话只读 ADB 取证、项目源码与用户现场观察。
- Topic: `st77912-partial-refresh-visual-regression`。
- Archive Candidate Path: 本文件。
- Sanitization: 未记录设备地址、凭据、原始 framebuffer、完整日志或二进制。
- Provenance: 2026-07-14 最新测试固件与同日工作区源码快照。
- Verification: release 内核四文件一致性、`git diff --check`、标准 `checkpatch` 和内核配置检查通过；`knowledge-check --dry-run --json --diagnostics` 通过，0 error、0 warning；固件与实机 A/B 仍 pending。
- Memory Candidate: no。
- Gate Result: archive governance pass；软件显示正确性 needs-fix，内容待人工 review。
