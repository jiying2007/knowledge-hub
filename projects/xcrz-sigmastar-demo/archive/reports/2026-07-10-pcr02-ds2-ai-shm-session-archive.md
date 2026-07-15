---
id: pcr02-ds2-ai-shm-session-archive-20260710
title: PCR02 DS2 与 AI 共享内存链路优化会话归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
status: reviewing
maturity: candidate
owner: leiwenjun
created_at: 2026-07-10
updated_at: 2026-07-10
review_after: 2026-10-10
tags:
  - pcr02
  - ds2
  - ai
  - hdi_vi_out3
  - nv12
  - rgb888
  - shm
  - performance
  - session-wrap
---

# PCR02 DS2 与 AI 共享内存链路优化会话归档

## Source

- Source type: current Codex engineering session.
- Repository: `xcrz_sigmastar_demo`.
- Capture date: 2026-07-10.
- Archive type: session-wrap + knowledge-archive candidate.
- Sanitization: private lab endpoint, raw serial logs, full command output, binary contents, core/runtime cache and credentials are not copied into this note.
- Scope: records reusable engineering decisions, implemented code direction, validation commands and remaining commit risks for DS2/AI video transport optimization.
- Boundary: this candidate is not an owner decision, release note, or active project rule.

## Summary

本会话围绕 PCR02 `prog_pcr02` 高负载问题，重点优化 DS2 raw 视频到 AI 的数据链路。最终方向是减少无效 padding、避免重复 RGB copy、保留模型输入尺寸要求，并让 AI 侧按模型高度直接使用共享内存数据。

核心结论：

- DS2 源头使用 640x360 NV12，API 层只做 NV12 到 RGB888，不再生成 640x640 RGB padding。
- Sensor 发布 DS2 RGB888 时只复制有效 640x360x3 数据，共享内存底部区域依赖 raw 通用 640x640x4 arena 的零初始化保持黑边。
- AI 侧不再通过 `PrepareRgbModelInput()` 复制到 scratch，而是按模型实际高度构造 `cv::Mat`，支持后续 640x384 与 640x640 模型共存。
- 不修改模型输入要求；传输和内部拷贝优化不能改变模型期望的输入宽高。
- HDI raw reader 的 task timer 不应在 rate-limited raw output 下使用 reset 语义，否则周期会变成 `callback 耗时 + interval`，导致 DS2 实际 FPS 低于目标。
- 帧率监控只保留 AI 实际处理帧率打印，移除临时 DS2/API/Sensor/HDI 调试日志。

## Implemented Workstreams

### 1. DS2 API 归一化

有效修改集中在 `modules/api` 和公共头：

- `DS2_STREAM_HEIGHT` 固定为 360。
- `DS2_STREAM_FRAME_SIZE` 改为 `640 * 360 * 3`。
- 移除 `DS2_PADDING_HEIGHT`。
- `_VIDEO_NormalizeDs2Rgb888()` 要求 NV12 派生高度必须是 360。
- API 只做 `NV12 -> RGB24/RGB888`，不再 `memset` 640x640 padding。
- `VSAPIRF_FrameParam_t` 移除 `u32PaddingWidth` / `u32PaddingHeight`。

工程含义：API 的 DS2 输出语义从“640x640 RGB padding frame”收敛为“640x360 RGB888 valid frame”，模型 padding 责任移到 AI consumer。

### 2. Sensor 共享内存发布

有效修改集中在 `modules/sensor/video/video_raw_frame_hub.cpp`：

- DS2 meta 发布为 `width=640`、`height=360`、`format=RGB888`。
- DS2 使用 raw 通用共享内存 arena，上限仍可容纳 640x640x4。
- DS2 每帧只复制有效 `frame_data.u32Size`，即 640x360x3。
- 共享内存尾部不再每帧补黑，依赖 arena 初始化和前部有效数据覆盖。

风险边界：

- 该策略要求共享内存 slot 初始化为 0，且后续不把未覆盖尾部写成非黑色。
- 如果未来引入复用 slot 且尾部可能被其他格式污染，需要补充 slot clear 策略或 per-frame dirty-range 约束。

### 3. AI 侧零额外 scratch copy

有效修改集中在 `modules/ai`：

- 移除 `PrepareRgbModelInput()`。
- 移除 `m_model_input_scratch_`。
- AI 侧从共享内存读取 DS2 RGB888 后，校验 meta 为 `640x360 RGB888`。
- 通过 `YoloDetector::InputWidth()` / `InputHeight()` / `InputChannels()` 获取模型输入要求。
- 要求模型宽度为 640，模型高度不小于 360。
- 直接用共享内存地址按模型高度构造 `cv::Mat`：
  - 640x384 模型读取 640x384x3。
  - 640x640 模型读取 640x640x3。
- Pet behavior 等只需要有效画面的逻辑仍使用 640x360 ROI。

工程含义：AI 不再为 padding 做一份 scratch copy；640x384 和 640x640 模型并存时，仍由模型高度决定读取窗口。

### 4. AI 实际帧率监控

本会话最终保留的调试能力仅为 AI 实际处理帧率：

- `Detector FPS stats ... actual_fps`
- `ShmCapture FPS stats ... actual_fps`

临时 DS2 normalize stats、Sensor SHM stats、HDI out3 stats、padding/copy 统计均已移除，避免默认日志噪音。

### 5. HDI raw reader timer 语义修正

`VSHDIOS_TaskConfigTimer()` 的 `bResetTimer=VS_TRUE` 会在每轮等待前把起点重置为当前时间，再加 interval。对 DS2 这种 heavy callback 来说，实际周期会变成：

```text
callback_processing_time + target_interval
```

因此目标 18/20fps 时，reset 会直接压低实际输出帧率。

最终修改：

- 删除 `bResetTaskTimer` 临时变量。
- 删除“heavy callback 不追帧”的 reset 注释。
- `VSHDIOS_TaskConfigTimer(..., u32TaskIntervalMs, VS_FALSE)` 固定使用非 reset 调度。

已有 `_VI_ShouldDropOutputFrame()` 负责基于 budget 的输出帧率控制，task timer 不应再叠加 reset 限速。

## Validation Evidence

已完成的定向验证：

- `rtk rg` 检查无残留：
  - `DS2_PADDING_HEIGHT`
  - `u32PaddingWidth`
  - `u32PaddingHeight`
  - `PrepareRgbModelInput`
  - `m_model_input_scratch`
  - 临时 DS2/API/Sensor/HDI debug stats
- `rtk rg -n "ShmCapture FPS stats|actual_fps|Detector FPS stats" modules/ai/AI_vision.cpp -S` 确认 AI FPS 监控仍在。
- `rtk git -C modules/api diff --check` 通过。
- `rtk git -C modules/sensor diff --check` 通过。
- `rtk git -C modules/ai diff --check` 通过。
- `rtk git -C modules/hdi diff --check` 通过。
- `rtk git diff --check -- include/api/api_video.h include/api/api_ringframe.h modules/proto/sensor_info.proto modules/common/transport/shm_channel_config.h` 通过。
- `rtk bash build/check_public_headers.sh --root . api` 通过。
- `rtk make modules/api_lib_all modules/sensor_lib_all modules/ai_lib_all -j8` 通过。
- `rtk make modules/hdi_lib_all pcr02_app_all -j8` 通过。
- `rtk make pcr02_app_all -j8` 通过。
- `rtk bash ~/codex/scripts/commit-ready.sh` 执行成功，但提示未暂存提交范围。
- `rtk bash ~/codex/scripts/final-ready.sh` 执行成功；会话过长时提示需要收口。

未完成或未纳入本归档的验证：

- 未归档长期板端 soak 数据。
- 未确认所有模型版本在板端实际 FPS 达到目标 18fps。
- 未确认共享内存 slot 尾部黑边在长时间运行中永远不被污染。
- 未完成 curated staging 后的最终 `commit-ready`。

## Working Tree And Commit Risk

提交前检查发现根工作区混有大量非本次范围修改和未跟踪内容，包括：

- 多个 `libs/arm/libs/glibc/11.1.0` 下的 `.so/.a` 构建产物。
- `bin/prog_*` 产物。
- 大量 `3rdparty/*` 未跟踪目录。
- 若干 app/cmd/daemon 目录和 patch/tar.gz 文件。

因此不能使用 `git add .`。本次 DS2/AI 优化应手工 curated staging，至少区分：

- 源码与接口变更。
- 构建产物是否按项目发布规则纳入。
- 非本次未跟踪目录是否完全排除。

## Recovery Notes

若下一会话继续，应优先确认：

1. 设备端是否部署了当前 DS2 NV12/RGB888 + AI direct Mat 版本。
2. AI `actual_fps` 是否稳定满足目标 18fps。
3. `hdi_vi_out3` 是否仍连轴转；重点看 task tick、实际输出帧、drop 次数和 AI 消费帧。
4. 640x384 与 640x640 模型分别验证输入窗口是否正确。
5. 共享内存尾部黑边是否在长时间运行中稳定为 0。
6. 提交前按 curated path 暂存，再运行 `commit-ready`。

## Suggested Commit Scope

源码侧候选范围：

- `include/api/api_ringframe.h`
- `include/api/api_video.h`
- `modules/api/include/api_ringframe.h`
- `modules/api/include/api_video.h`
- `modules/api/src/api_video_pipe/api_video.c`
- `modules/sensor/video/video_raw_frame_hub.cpp`
- `modules/ai/AI_vision.cpp`
- `modules/ai/AI_vision.h`
- `modules/ai/yolo_detector.h`
- `modules/hdi/src/hdi_video/hdi_vi.c`
- `modules/common/transport/shm_channel_config.h`
- `modules/proto/sensor_info.proto`

构建产物是否纳入需要单独确认项目发布规则，不应默认混入。

## Memory Candidate

No automatic memory write.

Potential project-local memory candidate for human review:

- PCR02 DS2 raw reader should keep `VSHDIOS_TaskConfigTimer(..., VS_FALSE)` for fixed cadence; output FPS limiting belongs in `_VI_ShouldDropOutputFrame()`, not timer reset, otherwise heavy callbacks reduce actual FPS.
- DS2/AI transport optimization must not change model input requirements; use model height to choose `cv::Mat` view over shared memory.

## Archive Evidence

- Source: current Codex engineering session on PCR02 DS2/AI performance work.
- Topic: session-wrap / DS2 AI SHM performance.
- Archive Candidate Path: `projects/xcrz-sigmastar-demo/archive/reports/2026-07-10-pcr02-ds2-ai-shm-session-archive.md`.
- Sanitization: private endpoint, raw logs, full command output, binary data and credentials omitted.
- Provenance: local repository state and validation commands from the session.
- Verification: targeted `rg`, `diff --check`, public header check, module library builds, and `pcr02_app_all`.
- Memory Candidate: yes, human review required; not written to memory.
- Gate Result: pass as archive candidate; commit gate still requires curated staging and optional artifact policy confirmation.
