---
id: pcr02-camera-raw-preview-virtual-stream-architecture-20260711
title: PCR02 camera RAW_PREVIEW 虚拟流架构设计与实现归档
kind: decision
domain: projects/pcr02
status: reviewing
maturity: candidate
owner: leiwenjun
created_at: 2026-07-11
updated_at: 2026-07-11
review_after: 2026-10-11
tags:
  - pcr02
  - camera
  - raw-preview
  - virtual-stream
  - lcd-preview
  - qr-scan
  - vision-rgb
  - android-camera-hal
  - shm
  - libyuv
---

# PCR02 camera RAW_PREVIEW 虚拟流架构设计与实现归档

## Source

- Source type: current Codex engineering session and local repository diff.
- Repository: `xcrz_sigmastar_demo`.
- Capture date: 2026-07-11.
- Topic: camera physical capture stream plus virtual stream fan-out.
- Related archive: `projects/pcr02/archive/reports/2026-07-10-pcr02-ds2-ai-shm-session-archive.md`.
- Sanitization: raw logs, binary contents, device private state, credentials and full command output are not copied into this note.
- Boundary: this is a decision candidate and implementation archive, not a release note or owner-signed active rule.

## Context

PCR02 旧实现把 DS1、DS2 当作两个面向上层的采集通道使用：

- DS1 面向屏显和二维码扫描。
- DS2 面向 640x360 RGB 输出和 AI 推理。
- DS1/DS2 都映射到底层 SCL2 类资源时，容易出现一路活跃导致另一路 pending 或被阻塞的问题。

本次设计按 Android Camera HAL 的思想硬切换：底层只维护一个合适的物理 capture stream，上层暴露多个按需生成的 virtual stream，由 API/HAL 中间层完成 crop、scale、format convert 和 fan-out。

## Decision

底层物理源统一为：

```text
VI_RAW_CHANNEL_RAW_PREVIEW
640x360 NV12 / YUV420SP
20 fps
```

上层虚拟流统一为：

```text
LCD_PREVIEW  -> center crop 360x360 -> scale 240x240 -> BGR565
QR_SCAN      -> center crop 360x360 -> scale 240x240 -> Y8
VISION_RGB   -> 640x360 NV12 -> RGB888
```

命名上不再继续沿用 `DS1`、`DS2`、`YUV_DS*`、`AI_RGB` 作为架构概念。`VISION_RGB` 表示面向视觉算法和调试预览的 RGB888 virtual stream；AI 只是该流的一个 consumer。

Temporary compatibility exception:

- `proto.sensor_ctrl.VideoPayload.Stream` keeps `DS1_RAW = 3` as an alias of `LCD_PREVIEW = 3`.
- `proto.sensor_ctrl.VideoPayload.Stream` keeps `DS2_RAW = 4` as an alias of `VISION_RGB = 4`.
- `QR_SCAN` is assigned to `5` to avoid repurposing old `DS2_RAW = 4`.
- This is protocol compatibility only; the architecture names and new code paths remain `LCD_PREVIEW`, `QR_SCAN` and `VISION_RGB`.

## Stream Contract

| Stream | Pixel format | Size | Stride | Frame size | SHM channel | Primary consumers |
|---|---:|---:|---:|---:|---|---|
| `LCD_PREVIEW` | `BGR565` | 240x240 | 480 | 115200 | `shm/video/lcd_preview` | LCD preview, QR display scene, product LCD test |
| `QR_SCAN` | `Y8` | 240x240 | 240 | 57600 | `shm/video/qr_scan` | QR decode path |
| `VISION_RGB` | `RGB888` | 640x360 | 1920 | 691200 valid bytes | `shm/video/vision_rgb` | AI vision, RGB debug preview |

`VISION_RGB` has an additional AI compatibility contract: the SHM readable payload is committed as `640 * 640 * 3`, but producer only copies the valid `640 * 360 * 3` RGB region each frame. The tail remains black so model inputs such as 640x384 or 640x640 can read a padded view without per-frame padding copy.

## Crop And Scaling

The physical source is 640x360. Square virtual streams use a centered 360x360 crop:

```text
x = 140
y = 0
w = 360
h = 360
dst = 240x240
```

These values are safe for NV12/YUV420SP because x, y, width and height are even.

Current implementation details:

- `QR_SCAN` uses the Y plane only and scales the cropped 360x360 Y area to 240x240.
- `LCD_PREVIEW` samples the same cropped region and converts to BGR565 for the 240x240 LCD window.
- `VISION_RGB` converts the full 640x360 NV12 frame to RGB888.

## On-Demand Generation

Virtual streams are generated only when their API channel has active readers:

- `_VIDEO_RawPreviewSourceAcquire()` opens `VI_RAW_CHANNEL_RAW_PREVIEW` with refcount.
- `_VIDEO_RawPreviewSourceRelease()` destroys the physical raw reader when the last virtual stream releases.
- `_VIDEO_ProcessRawPreviewFrame()` checks `VIDEO_CHANNEL_LCD_PREVIEW`, `VIDEO_CHANNEL_QR_SCAN` and `VIDEO_CHANNEL_VISION_RGB` independently and only normalizes the active outputs.

This preserves the intended resource model: one physical stream, multiple virtual stream contracts, and no permanent work for unused consumers.

## Implementation Evidence

Core interface and metadata:

- `include/hdi/hdi_vi.h`: replaces DS1/DS2 raw channel naming with `VI_RAW_CHANNEL_RAW_PREVIEW`.
- `include/api/api_video.h`: defines `LCD_PREVIEW`, `QR_SCAN`, `VISION_RGB` stream sizes, channel ids, stream ids and frame source ids.
- `include/api/api_ringframe.h`: extends ringframe metadata with stream id, pixel format, width, height and stride.
- `modules/proto/sensor_ctrl.proto`: exposes `LCD_PREVIEW`, `QR_SCAN`, `VISION_RGB` payload types.
- `modules/proto/sensor_ctrl.proto`: keeps temporary `DS1_RAW` / `DS2_RAW` aliases for old deployed clients, while preserving new names as canonical generated mappings.
- `modules/proto/sensor_info.proto`: documents SHM video channels and adds `Y8` / `BGR565` pixel formats.

Physical source and virtual stream fan-out:

- `modules/api/src/api_video_pipe/api_video.c`:
  - `VIDEO_RAW_PREVIEW_WIDTH = 640`, `VIDEO_RAW_PREVIEW_HEIGHT = 360`, output fps = 20.
  - `_VIDEO_NormalizeVisionRgb888()` converts NV12 to RGB888.
  - `_VIDEO_NormalizeQrScanY8()` crops/scales Y plane to 240x240.
  - `_VIDEO_NormalizeLcdPreviewBgr565()` crops/scales and packs BGR565.
  - `_VIDEO_ProcessRawPreviewFrame()` dispatches active virtual streams independently.

SHM fan-out:

- `modules/common/transport/channel_list.{h,cpp}`: defines `shm/video/lcd_preview`, `shm/video/qr_scan`, `shm/video/vision_rgb`.
- `modules/common/transport/shm_channel_config.h`: keeps a shared raw/derived frame arena size of `640 * 640 * 4`.
- `modules/sensor/video/video_raw_frame_hub.{h,cpp}`:
  - exposes `acquireLcdPreview()`, `acquireQrScan()`, `acquireVisionRgb()`.
  - publishes typed `VideoFrameMeta` for the three virtual streams.
  - commits padded readable payload for `VISION_RGB` while copying only the valid 640x360 RGB region.

Consumers:

- `modules/sensor/qr/qr_capture.cpp`: consumes `QR_SCAN` Y8.
- `modules/sensor/display/qr/qr_scene.cpp`: consumes `LCD_PREVIEW` BGR565 for QR scene display.
- `modules/ai/AI_vision_thread.cpp` and `modules/ai/AI_vision.cpp`: consume `VISION_RGB` SHM and build model-sized RGB `cv::Mat` views.
- `app_product_test/pt_hw_lcd.c` and `app_main/app_main.c`: use `LCD_PREVIEW` / `VISION_RGB` command paths for local test and preview.
- `modules/app/src/app_diag/provider/api/app_diag_api_media_provider.c` and `modules/app/src/app_diag/provider/app_diag_ai_provider.c`: expose diag commands for the renamed virtual streams.

## Review Fixes Captured

The review finding about `VISION_RGB` payload size is valid. The final contract is:

```text
publish_size = 640 * 640 * 3
memcpy_size  = 640 * 360 * 3
```

Reason:

- AI models may require input heights greater than 360.
- AI side checks `view.size() >= model_width * model_height * 3`.
- Publishing only the valid 640x360 size breaks 640x384 and 640x640 model views.
- Reintroducing per-frame padding copy is unnecessary; the valid region is copied, and the SHM tail remains black.

## Validation Evidence

Completed validation in the engineering session:

- `rtk bash modules/proto/build_proto.sh`: passed.
- `rtk make -j8 NC=1`: passed; only pre-existing warnings were observed.
- `rtk git diff --check`: passed.
- Targeted source scans confirmed the intended stream names and SHM channels are present:
  - `LCD_PREVIEW`
  - `QR_SCAN`
  - `VISION_RGB`
  - `VI_RAW_CHANNEL_RAW_PREVIEW`
  - `shm/video/lcd_preview`
  - `shm/video/qr_scan`
  - `shm/video/vision_rgb`

Known validation gaps:

- No long-running board soak result is archived here.
- No owner-signed release decision is archived here.
- `pcr02/dep.mk` currently has a separate release packaging review finding about commented application binaries; that issue is not closed by this camera architecture decision.

## Commit And Release Risk

The working tree contains generated libraries and many untracked directories. Do not stage with `git add .`.

The camera architecture source scope should be curated explicitly. Binary artifacts and unrelated untracked directories require separate artifact/release policy confirmation.

The `pcr02/dep.mk` release binary packaging review item remains a separate P1 risk and should be resolved before treating the overall patch set as release-ready.

## Memory Candidate

No automatic memory write.

Potential project-local memory candidate for human review:

- PCR02 camera preview should be modeled as one physical `RAW_PREVIEW_640x360_NV12` source with virtual `LCD_PREVIEW`, `QR_SCAN` and `VISION_RGB` streams. Do not reintroduce DS1/DS2 as public architecture concepts.
- `VISION_RGB` SHM must keep padded readable payload for model-height compatibility while copying only valid 640x360 RGB bytes per frame.

## Archive Evidence

- Source: current PCR02 camera virtual stream implementation session.
- Topic: camera raw preview virtual stream architecture.
- Archive Candidate Path: `projects/pcr02/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md`.
- Sanitization: secrets, raw logs, binary contents, private runtime state and full command output omitted.
- Provenance: local repository diff, targeted source reads and validation commands.
- Verification: proto generation, full build, diff whitespace check and targeted source scans.
- Memory Candidate: yes, human review required; not written to memory.
- Gate Result: pass as archive candidate; release gate still needs `pcr02/dep.mk` P1 closure.
