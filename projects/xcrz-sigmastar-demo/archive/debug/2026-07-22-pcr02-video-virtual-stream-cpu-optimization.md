---
related:
- pcr02-camera-raw-preview-virtual-stream-architecture-20260711
- pcr02-dual-a32-system-cpu-optimization-plan-20260721
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-video-virtual-stream-cpu-optimization-20260722
title: PCR02 视频虚拟流降频与 LCD libyuv NEON 优化记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-22-pcr02-video-virtual-stream-cpu-optimization.md
scope: project-specific
visibility: team-internal
status: draft
owner: leiwenjun
source:
  type: manual
  from: 当前源码差异、定向构建证据及用户提供的板端显示与 CPU 定性验证结论
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-10-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- camera
- raw-preview
- virtual-stream
- lcd-preview
- qr-scan
- libyuv
- neon
- cpu-optimization
- device-validated
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-22-pcr02-video-virtual-stream-cpu-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-22-pcr02-video-virtual-stream-cpu-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-22'
updated_at: '2026-07-22'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-22'
manual_validation_pending: true
summary_zh: 固化单路 RAW_PREVIEW 20fps 架构下 QR_SCAN 10fps 转换前丢帧，以及 LCD_PREVIEW 使用 libyuv NEON 替代标量 NV12 到 BGR565 转换的实现和验证；板端显示正常且
  CPU 定性改善，量化基线仍待补充。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 视频虚拟流降频与 LCD libyuv NEON 优化记录

## 结论与边界

在不改变单路物理 RAW Preview、多路虚拟流 fan-out 架构的前提下，完成两项 CPU 减载：

- 物理 `RAW_PREVIEW` 保持 640×360 NV12、20fps。
- `VISION_RGB` 和 `LCD_PREVIEW` 保持20fps。
- `QR_SCAN` 在格式转换前按2:1门控到10fps，跳过的帧不执行 crop/scale。
- `LCD_PREVIEW` 将标量逐像素 NV12→BGR565 循环替换为 libyuv NEON 路径。

板端人工验证结果为“显示正常，CPU有改善”。该结论属于设备侧定性证据；由于未保留 BuildID、固定负载矩阵、优化前后 CPU 数值和采样窗口，不能据此声明具体下降比例，也不能自动提升为 active 规则或发布结论。

## 影响范围

- 项目：PCR02 SigmaStar SSC305 应用。
- 模块：`modules/api/src/api_video_pipe/api_video.c`。
- 硬件：双核 Cortex-A32。
- 接口：RAW Preview、LCD Preview、QR Scan、Vision RGB 的帧频与像素格式契约。
- 非目标：不改变 HDI 物理通道、SHM channel、reader/provider、RefCount、init/deinit 或消费者架构。

## 优化前热点

`VISION_RGB` 已使用 libyuv `NV12ToRGB24()`；`QR_SCAN` 已使用 libyuv `ScalePlane()`。主要未优化热点是 `LCD_PREVIEW`：每帧对 240×240 像素执行双层 C 循环，包含坐标整数除法、YUV 索引、定点颜色乘法、分支裁剪和 BGR565 打包。

在20fps下，该路径每秒执行约115.2万次标量像素转换。线程调度或 affinity 不能减少这些计算，因此优先做转换前丢帧和 SIMD 化。

## 实现

### QR_SCAN 独立降频

API 层为虚拟通道维护整数频率累加器。QR 通道开启时预置为首帧立即处理，之后每两个20fps物理帧转换一次：

```text
RAW frame 1 -> QR convert
RAW frame 2 -> QR skip
RAW frame 3 -> QR convert
RAW frame 4 -> QR skip
```

门控位于 `_VIDEO_NormalizeQrScanY8()` 之前，因此被跳过帧不产生缩放成本。QR通道关闭后重开会复位相位，不增加首次取流等待。

### LCD_PREVIEW SIMD 转换

转换链路变为：

```text
640×360 NV12
  -> center crop 360×360
  -> NV12Scale 240×240
  -> SwapUVPlane
  -> NV12ToRGB565Matrix(kYvuI601Constants)
  -> 240×240 BGR565
```

`libyuv.so` 为 ARMv7、NEONv1构建，包含 `NV12Scale`、`SwapUVPlane` 和 `NV12ToRGB565Matrix` 的 NEON实现。UV→VU交换配合 `kYvuI601Constants` 保持既有 BGR565 位序：红色 `0x001f`、绿色 `0x07e0`、蓝色 `0xf800`，避免标准RGB565造成红蓝颠倒。

LCD通道使用一次性申请、关闭时释放的230,400字节工作区：

| 区域 | 大小 |
| --- | ---: |
| 输出 BGR565 | 115,200字节 |
| 缩放后 Y | 57,600字节 |
| 缩放后 UV | 28,800字节 |
| 交换后 VU | 28,800字节 |

热路径未新增 malloc/free，各区间互不重叠，crop访问未越过原始Y/UV平面。

## 验证

2026-07-22 对当前工作区执行：

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk git -C modules/api diff --check` | 0 | API源码差异无空白错误。 | `modules/api/src/api_video_pipe/api_video.c` | Project | 本条目 |
| `rtk make modules/api_obj_all -j20` | 0 | `api_video.c` 在 `-Werror` 下编译通过。 | 当前工作区构建结果摘要 | Project | `modules/api` object |
| `rtk make modules/api_lib_all -j20` | 0 | API静态库和动态库构建通过。 | 当前工作区构建结果摘要 | Project | `libapi.a`、`libapi.so` |
| `rtk make pcr02_app_all -j20` | 0 | PCR02最终应用链接通过，新增libyuv符号解析闭环。 | 当前工作区构建结果摘要 | Project | PCR02 application |
| `rtk nm -D libs/3rdparty/libyuv/lib/libyuv.so` 定向符号检查 | 0 | `NV12Scale`、`SwapUVPlane`、`NV12ToRGB565Matrix`、`kYvuI601Constants` 均存在。 | 目标libyuv符号表摘要 | Tool | `libyuv.so` |
| 旧标量helper和双层循环负向扫描 | 1（预期无匹配） | `_VIDEO_ClipU8`、`_VIDEO_PackBgr565` 和 `u32DstX/u32DstY` 标量循环已移除。 | `modules/api/src/api_video_pipe/api_video.c` | Project | 本条目 |
| 板端人工检查 | 0（用户确认） | LCD显示正常，整机CPU有改善。 | 当前会话人工反馈摘要；未保留设备地址和raw日志 | Device | 本条目 |

## 失败与排除路径

- 不能直接使用标准 `NV12ToRGB565()`：会改变当前BGR565红蓝位序。
- 不能只降低物理RAW帧率：会同时影响需要20fps的VISION和LCD消费者。
- 不在转换后丢QR帧：转换成本已经发生，达不到CPU减载目标。
- `build/check_diag_layer_deps.py` 与 `build/check_diag_naming.py` 在当前仓不存在，无法作为本次验证证据；该缺口不伪装为通过。

## 风险与回退

- `NV12Scale(kFilterNone)` 与原手写nearest-neighbor在边缘采样位置上可能存在细微差异；板端显示已确认正常，但没有逐像素golden对比。
- CPU只有定性改善，缺少固定场景、采样窗口和优化前后数值。
- 若出现颜色、裁剪或稳定性回归，可只回退LCD normalizer到原标量实现，不需要回退虚拟流架构或QR独立频率。
- 当前源码与构建产物尚未在本条目中绑定发布版本或BuildID，不作为release evidence。

## 后续动作

1. 固化相同BuildID和负载矩阵，量化 `prog_pcr02` 总CPU、热点线程、上下文切换和帧率。
2. 优先检查 `VISION_RGB` 从normalize buffer到ringframe/SHM的重复大帧复制，评估直接写最终slot。
3. 检查LCD与QR同时活跃时能否复用缩放后的Y平面，但必须保留QR解码准确率和滤波质量。
4. 继续执行双核A32整机规划中的Camera open/FPS幂等、Display静态停止刷新和Bridge按订阅构造消息。
5. 只有量化数据、BuildID和owner复核补齐后，才评估将本draft候选转为reviewing validation；不自动写memory或提升active。

## Provenance 与脱敏

- captured_at：2026-07-22。
- source：当前源码差异、定向编译/链接证据和用户提供的板端人工结论。
- sanitization：未保存设备地址、PID/TID、完整日志、二进制、客户资料、凭证或本机绝对源码路径。
- memory candidate：否。
- active promotion：否。

```yaml
manual_validation_pending: true
manual_validation_reason: 显示和CPU定性改善已确认，缺少BuildID、固定场景和量化前后数据
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: 2026-10-22
```
