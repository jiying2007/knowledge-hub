---
maturity: candidate
aliases:
- PCR02 camera RAW_PREVIEW 虚拟流架构设计与实现归档
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
decision_status: accepted-boundary-evidence-pending
review_scope: owner-attested-boundary-only-no-active-release-or-evidence-ready
owner_roles_required:
- PCR02 product decision owner
- camera/media owner
- protocol/API owner
- application/AI owner
- release owner
evidence_readiness:
  owner: accepted-boundary-evidence-pending
  source: pending-current-commit-and-artifact-identity
  device: pending-real-device-or-lab-evidence
  release: pending-release-and-rollback-evidence
  validation_path: artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
owner_attestation_ref: artifacts/manifests/knowledge-hub-pcr02-specialized-owner-attestation-20260716.md
owner_decision: accept-single-raw-preview-three-virtual-stream-contract-remain-reviewing
decision_date: '2026-07-16'
id: pcr02-camera-raw-preview-virtual-stream-architecture-20260711
title: PCR02 camera RAW_PREVIEW 虚拟流架构设计与实现归档
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current Codex engineering session and local repository diff
review_after: '2026-10-11'
review_status: delegated-review-closed-candidate-boundary
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; owner accepted the single RAW_PREVIEW and three-virtual-stream boundary; device soak, packaging,
  compatibility, release and rollback evidence remain pending
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
- decision-candidate
- manual-validation-pending
- no-active-promotion
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md
- artifacts/manifests/pcr02-owner-ready-validation-paths-20260713.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-13
- rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --as-of 2026-07-13
evidence_strength: current-codex-session-plus-local-repository-diff
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md
- current Codex engineering session and local repository diff
created_at: '2026-07-11'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-11'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: 归档 PCR02 camera RAW_PREVIEW 单物理采集流加虚拟流 fan-out 架构：底层统一 640x360 NV12 RAW_PREVIEW，上层按需生成 LCD_PREVIEW、QR_SCAN 和 VISION_RGB。该条目是
  decision candidate 和 implementation archive，不是 release note、owner-signed active rule 或源项目事实签收。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 camera RAW_PREVIEW 虚拟流架构设计与实现归档

## Source

- Source type: current Codex engineering session and local repository diff.
- Repository: `xcrz_sigmastar_demo`.
- Capture date: 2026-07-11.
- Topic: camera physical capture stream plus virtual stream fan-out.
- Related archive: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-10-pcr02-ds2-ai-shm-session-archive.md`.
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
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/decisions/camera-raw-preview-virtual-stream-architecture-20260711.md`.
- Sanitization: secrets, raw logs, binary contents, private runtime state and full command output omitted.
- Provenance: local repository diff, targeted source reads and validation commands.
- Verification: proto generation, full build, diff whitespace check and targeted source scans.
- Memory Candidate: yes, human review required; not written to memory.
- Gate Result: pass as archive candidate; release gate still needs `pcr02/dep.mk` P1 closure.

<!-- pcr02-owner-device-release-validation:start -->
## Owner、实机与发布验证门禁

> 本节定义真实验证路径，不表示任何命令已经执行，也不是 owner decision、active promotion 或 release 授权。

### 1. Owner 决策路径

- `decision_owner=leiwenjun`，并已通过 `knowledge-hub-pcr02-specialized-owner-attestation-20260716` 接受单物理 RAW_PREVIEW + 三虚拟流 fan-out，且 DS1/DS2 仅作为临时兼容 alias。
- 该决定不证明设备 soak、镜像打包、协议兼容、消费者端到端、发布或回滚验证已通过；候选继续保持 `reviewing`。

### 2. Source、构建与制品身份

- 记录 remote key `robot/xcrz_sigmastar_demo`、source commit、proto 生成器版本、依赖版本、dirty 状态及明确 source file list。
- 复跑 proto 生成、目标构建和定向测试，保存命令、返回码、关键日志摘要及目标镜像/应用/协议制品 SHA256。
- 单独关闭 `pcr02/dep.mk` 发布打包风险，证明目标镜像实际包含预期应用和库；源码 build pass 不能替代镜像内容验证。

### 3. 实机功能与并发矩阵

| 场景 | 必填检查 |
|---|---|
| 单消费者 | `LCD_PREVIEW`、`QR_SCAN`、`VISION_RGB` 分别启停，验证格式、尺寸、stride、frame size、颜色和释放 |
| 双/三消费者 | 逐组合并发，验证一个消费者阻塞/退出不会卡住其他流或泄漏 physical reader refcount |
| 兼容客户端 | 旧 `DS1_RAW`/`DS2_RAW` alias 与新枚举互操作，未知/重复订阅返回码稳定 |
| SHM 契约 | `VISION_RGB` valid 640x360 区域正确，640x640 readable tail 为确定性黑色，无越界和旧帧泄漏 |
| 消费链路 | LCD、QR、AI、diag/product test 使用实际发布二进制端到端读取，不只调用 producer 单测 |

每个场景记录设备/固件、帧计数、首帧延迟、持续帧率、drop/timeout、CPU、RSS/SHM、图像正确性和关键日志。长跑时长与通过阈值由 owner 在执行前按产品要求填写。

### 4. 故障、恢复与 soak

- 覆盖消费者异常退出、重复 acquire/release、producer 重启、SHM reader 超时、camera source 短暂失败和系统休眠/唤醒。
- 检查 physical source refcount 回到零、SHM 无陈旧敏感帧、恢复后 metadata/stream id/stride 正确，并执行 ASAN 或适用内存诊断。
- soak 结果必须关联 source commit、设备、负载、时长和失败计数；“运行一段时间正常”不构成发布证据。

### 5. Release 与回滚

- release owner 核对协议兼容、镜像内容、应用消费者 smoke、升级/降级路径和发布说明；记录制品 hash 与目标设备验收。
- 回滚制品必须能恢复旧 DS1/DS2 行为或明确拒绝新客户端，并验证升级后产生的 SHM/配置不会破坏旧版本。
- 缺少 owner、实机并发/soak、镜像内容或回滚证据时保持 `reviewing`，不得按 implementation archive 自动提升 active。

### 证据落地契约

- 证据记录必须包含 `owner_identity`、`source_commit`、`artifact_sha256`、`device_identity`、`environment`、`commands`、`exit_codes`、`result_summary`、`rollback_result` 和可恢复引用。
- raw log、视频、截图和二进制只保存在受控外部制品位置；Hub 正文只保存脱敏摘要、hash 和引用。
- 最终复核命令：`rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full --as-of 2026-07-13`。
<!-- pcr02-owner-device-release-validation:end -->
