---
id: pcr02-video-audio-shm-usage-20260713
title: PCR02 Video/Audio 共享内存使用说明
kind: runbook
domain: projects/pcr02
status: reviewing
maturity: candidate
owner: leiwenjun
created_at: 2026-07-13
updated_at: 2026-07-13
review_after: '2026-10-13'
tags:
- pcr02
- video
- audio
- shm
- lcd-preview
- qr-scan
- vision-rgb
- h264
- pcm
- manual-validation-pending
- no-active-promotion
scope: project-specific
visibility: team-internal
review_status: manual-entry-pending-review
promotion: none
generated_by_ai: false
manual_validation_pending: true
summary_zh: 记录 PCR02 当前 Video/Audio 共享内存通道、启停前置条件、虚拟流、订阅接口和 payload 契约；来源为当前仓库实现与用户提供旧笔记，保持 reviewing，待真实 owner 与实机验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: none; capture does not authorize active promotion or owner decision
path: projects/pcr02/current/runbooks/video-audio-shm-usage.md
aliases:
- PCR02 Video/Audio 共享内存使用说明
related:
- projects/pcr02/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 Video/Audio 共享内存使用说明

## Source

- Source type: current repository implementation and user-provided legacy note.
- Repository: `xcrz_sigmastar_demo`.
- Capture date: 2026-07-13.
- Main evidence:
  - `modules/common/transport/channel_list.cpp`
  - `modules/common/transport/shm_channel_config.h`
  - `modules/common/transport/shm_pub_sub.cpp`
  - `modules/proto/sensor_ctrl.proto`
  - `modules/proto/sensor_info.proto`
  - `modules/api/src/api_video_pipe/api_video.c`
  - `modules/sensor/video/video_raw_frame_hub.cpp`
  - `modules/sensor/audio/audio_frame_hub.cpp`
- Sanitization: no raw logs, binaries, credentials or device private state are copied.

## 1. 当前可用通道

| 数据 | 终态流 / 控制流 | SHM channel | meta | payload |
|---|---|---|---|---|
| 高清编码流 | `MAIN_ENC` | `shm/video/h264/main` | `VideoFrameMeta` | H264/H265 frame |
| 标清编码流 | `LOW_ENC` | `shm/video/h264/low` | `VideoFrameMeta` | H264/H265 frame |
| 屏显预览 | `LCD_PREVIEW` | `shm/video/lcd_preview` | `VideoFrameMeta` | 240x240 BGR565 |
| 二维码扫描 | `QR_SCAN` | `shm/video/qr_scan` | `VideoFrameMeta` | 240x240 Y8 |
| 视觉 RGB | `VISION_RGB` | `shm/video/vision_rgb` | `VideoFrameMeta` | 640x360 RGB888 valid area, SHM readable payload padded to 640x640x3 |
| 麦克风上行 | `MIC enable=true` | `shm/audio/pcm` | `AudioFrameMeta` | PCM S16LE 16k/mono |
| 音频 AI/下行辅助通道 | 内部音频路径 | `shm/audio/pcm/ai` | `AudioFrameMeta` | PCM，具体 producer/consumer 由 AI/IOT 下行链路决定 |
| 音频下行播放 | 内部音频路径 | `shm/audio/pcm/downlink` | `AudioFrameMeta` | PCM，云端/声网下行播放 |
| DVR 回放视频 | 回放 | `shm/dvr/replay/video` | `VideoFrameMeta` | H264/H265 |
| DVR 回放音频 | 回放 | `shm/dvr/replay/audio` | `AudioFrameMeta` | PCM/AAC |

当前不再把 `DS1_RAW` / `DS2_RAW` 作为架构通道使用。它们只在 `proto.sensor_ctrl.VideoPayload.Stream` 中保留为临时兼容别名：

- `DS1_RAW = 3` 等价 `LCD_PREVIEW = 3`
- `DS2_RAW = 4` 等价 `VISION_RGB = 4`
- `QR_SCAN = 5`

旧的 SHM channel 不再作为当前对接目标：

- `shm/video/yuv/ds1`
- `shm/video/yuv/ds2`

通道定义在 `modules/common/transport/channel_list.cpp`，容量配置在 `modules/common/transport/shm_channel_config.h`。

## 2. 使用前置条件

video 侧必须先让 sensor 打开摄像头和对应视频流。否则对应 `ShmPublisher` 不会注册帧回调，也不会有数据。

通用顺序：

1. `CAMERA enable=true`
2. `VIDEO enable=true streams=[MAIN_ENC / LOW_ENC / LCD_PREVIEW / QR_SCAN / VISION_RGB]`
3. app 订阅对应 SHM channel
4. 使用结束后 `VIDEO enable=false streams=[对应流]`
5. 没有任何 video lease 后 `CAMERA enable=false`

远程标清监控：

```text
CAMERA enable=true
VIDEO enable=true streams=[LOW_ENC]
订阅 shm/video/h264/low
```

AI vision：

```text
CAMERA enable=true
VIDEO enable=true streams=[VISION_RGB]
订阅 shm/video/vision_rgb
```

二维码扫描：

```text
CAMERA enable=true
VIDEO enable=true streams=[QR_SCAN]
订阅 shm/video/qr_scan
```

LCD 屏显：

```text
CAMERA enable=true
VIDEO enable=true streams=[LCD_PREVIEW]
订阅 shm/video/lcd_preview
```

旧客户端如果仍发送：

```text
VIDEO enable=true streams=[DS1_RAW]
```

当前会按 `LCD_PREVIEW` 处理。旧客户端如果仍发送：

```text
VIDEO enable=true streams=[DS2_RAW]
```

当前会按 `VISION_RGB` 处理。新代码不要继续使用旧名字。

音频 live mic 需要显式打开 mic capture 后订阅：

```text
MIC enable=true
订阅 shm/audio/pcm
```

当前 sensor live mic 只发布 `PCM_S16LE 16k mono`。`channel_audio_aac_` 名字存在，但 live mic 没有默认 AAC publisher；不要按默认 live mic 通道假设 AAC。

## 3. 当前视频虚拟流架构

底层物理源统一为：

```text
VI_RAW_CHANNEL_RAW_PREVIEW
640x360 NV12 / YUV420SP
20 fps
```

上层虚拟流按需生成：

```text
LCD_PREVIEW -> center crop 360x360 -> scale 240x240 -> BGR565
QR_SCAN     -> center crop 360x360 -> scale 240x240 -> Y8
VISION_RGB  -> full 640x360 NV12 -> RGB888
```

方形流中心裁剪参数：

```text
src = 640x360
crop = x=140, y=0, w=360, h=360
dst = 240x240
```

`x/y/w/h` 都是偶数，对 NV12/YUV420SP 安全。

`VISION_RGB` 的特殊契约：

- `VideoFrameMeta.width = 640`
- `VideoFrameMeta.height = 360`
- `VideoFrameMeta.format = RGB888`
- `stride_y = 640 * 3 = 1920`
- 有效 RGB 数据大小为 `640 * 360 * 3`
- SHM readable payload size 提交为 `640 * 640 * 3`
- producer 每帧只复制有效 `640 * 360 * 3`，尾部保持黑底，供 640x384 / 640x640 等模型视图读取

## 4. C++ 订阅方式

核心头文件：

```cpp
#include "modules/common/transport/shm_pub_sub.h"
#include "modules/common/transport/shm_channel_config.h"
#include "modules/common/transport/channel_list.h"
#include "modules/proto/sensor_info.pb.h"
```

`ShmSubscriber` 普通回调签名：

```cpp
[](const common::FrameView &view,
   const uint8_t *meta_buf,
   std::size_t meta_size) {
}
```

`view.data()` 是帧 payload，`view.size()` 是 payload 字节数；`meta_buf/meta_size` 是 protobuf 序列化后的 `VideoFrameMeta` 或 `AudioFrameMeta`。

注意：

- `FrameView` 只在回调期间有效。
- 不要把 `view.data()` 指针保存到异步线程里。
- 需要异步处理时，回调内立刻复制到自己的 queue/buffer。
- 若使用 `OwningCallback` 重载，`FrameView` 以右值 move 给消费者；meta 需要从 `view.metaInline()` / `view.metaSize()` 读取。

## 5. 订阅 LOW_ENC 示例

```cpp
#include <memory>
#include <vector>
#include "modules/common/transport/channel_list.h"
#include "modules/common/transport/shm_channel_config.h"
#include "modules/common/transport/shm_pub_sub.h"
#include "modules/proto/sensor_info.pb.h"

class LowStreamConsumer {
public:
    void start() {
        sub_ = std::make_unique<common::ShmSubscriber>(
            common::ChannelList::channel_video_h264_low_,
            common::kShmVideoH264Config.max_payload,
            common::kShmVideoH264Config.queue_size,
            [this](const common::FrameView &view,
                   const uint8_t *meta_buf,
                   std::size_t meta_size) {
                proto::sensor_info::VideoFrameMeta meta;
                if (!meta.ParseFromArray(meta_buf, static_cast<int>(meta_size))) {
                    return;
                }

                std::vector<uint8_t> frame(view.data(), view.data() + view.size());

                const bool is_key = meta.key_frame();
                const uint64_t pts_us = meta.pts_us();
                const auto format = meta.format(); // H264 or H265

                handleFrame(frame, is_key, pts_us, format);
            });
    }

    void stop() {
        sub_.reset();
    }

private:
    void handleFrame(const std::vector<uint8_t> &frame,
                     bool key_frame,
                     uint64_t pts_us,
                     proto::sensor_info::VideoFrameMeta::PixelFormat format) {
        // app 自己处理：RTSA、推云、缓存等
    }

    std::unique_ptr<common::ShmSubscriber> sub_;
};
```

高清主码流只需要把 channel/config 换成：

```cpp
common::ChannelList::channel_video_h264_main_
common::kShmVideoH264Config
```

## 6. 订阅 LCD_PREVIEW 示例

```cpp
sub_ = std::make_unique<common::ShmSubscriber>(
    common::ChannelList::channel_video_lcd_preview_,
    common::kShmVideoRawConfig.max_payload,
    common::kShmVideoRawConfig.queue_size,
    [](const common::FrameView &view,
       const uint8_t *meta_buf,
       std::size_t meta_size) {
        proto::sensor_info::VideoFrameMeta meta;
        if (!meta.ParseFromArray(meta_buf, static_cast<int>(meta_size))) {
            return;
        }

        if (meta.format() != proto::sensor_info::VideoFrameMeta::BGR565
            || meta.width() != 240 || meta.height() != 240
            || view.size() < 240 * 240 * 2) {
            return;
        }

        const uint8_t *bgr565 = view.data();
        const size_t size = 240 * 240 * 2;

        // 复制后送 LCD、预览缓存或业务线程。
    });
```

## 7. 订阅 QR_SCAN 示例

```cpp
sub_ = std::make_unique<common::ShmSubscriber>(
    common::ChannelList::channel_video_qr_scan_,
    common::kShmVideoRawConfig.max_payload,
    common::kShmVideoRawConfig.queue_size,
    [](const common::FrameView &view,
       const uint8_t *meta_buf,
       std::size_t meta_size) {
        proto::sensor_info::VideoFrameMeta meta;
        if (!meta.ParseFromArray(meta_buf, static_cast<int>(meta_size))) {
            return;
        }

        if (meta.format() != proto::sensor_info::VideoFrameMeta::Y8
            || meta.width() != 240 || meta.height() != 240
            || view.size() < 240 * 240) {
            return;
        }

        const uint8_t *gray = view.data();
        const size_t gray_size = 240 * 240;

        // 复制后送二维码识别线程；不要在回调内直接做重识别。
    });
```

## 8. 订阅 VISION_RGB 示例

```cpp
sub_ = std::make_unique<common::ShmSubscriber>(
    common::ChannelList::channel_video_vision_rgb_,
    common::kShmVideoRawConfig.max_payload,
    common::kShmVideoRawConfig.queue_size,
    [](const common::FrameView &view,
       const uint8_t *meta_buf,
       std::size_t meta_size) {
        proto::sensor_info::VideoFrameMeta meta;
        if (!meta.ParseFromArray(meta_buf, static_cast<int>(meta_size))) {
            return;
        }

        constexpr size_t kValidRgbSize = 640 * 360 * 3;
        constexpr size_t kPadded640Size = 640 * 640 * 3;

        if (meta.format() != proto::sensor_info::VideoFrameMeta::RGB888
            || meta.width() != 640 || meta.height() != 360
            || meta.stride_y() != 640 * 3
            || view.size() < kValidRgbSize) {
            return;
        }

        const uint8_t *rgb = view.data();

        // 显示/调试只使用有效 640x360 区域。
        // 若模型输入高度 > 360，先确认 view.size() >= model_width * model_height * 3。
        // 当前 producer 对 VISION_RGB 提交 padded readable payload，常见 640x384/640x640 模型可直接建 view。
        if (view.size() >= kPadded640Size) {
            // 可作为 640x640 RGB view 读取，360 以下区域为黑底 padding。
        }
    });
```

## 9. 订阅音频 PCM 示例

```cpp
sub_ = std::make_unique<common::ShmSubscriber>(
    common::ChannelList::channel_audio_pcm_,
    common::kShmAudioPcmConfig.max_payload,
    common::kShmAudioPcmConfig.queue_size,
    [](const common::FrameView &view,
       const uint8_t *meta_buf,
       std::size_t meta_size) {
        proto::sensor_info::AudioFrameMeta meta;
        if (!meta.ParseFromArray(meta_buf, static_cast<int>(meta_size))) {
            return;
        }

        if (meta.format() != proto::sensor_info::AudioFrameMeta::PCM_S16LE
            || meta.sample_rate() != 16000
            || meta.channels() != 1) {
            return;
        }

        const uint8_t *pcm = view.data();
        const size_t pcm_size = view.size();

        // 这里可以送 ASR、声网、云端，或编码成 AAC。
    });
```

当前 sensor live mic 只发布 `PCM_S16LE`。如果系统休眠导致音频 suspend，需要 sensor resume 后才会继续有帧。

## 10. 消费语义

当前 `ShmSubscriber` 的投递策略由 `modules/common/transport/shm_pub_sub.cpp` 决定：

```cpp
enum class ShmDeliveryPolicy {
    kOrdered,
    kLatestOnly,
};

ShmDeliveryPolicy deliveryPolicyForChannel(const std::string &channel);
```

当前 common 内部按 channel 配置 delivery policy。裸帧/派生帧 channel 使用 latest-only；其他 channel 使用 ordered，每次 poll 最多处理 8 帧。该策略不改变 `ShmSubscriber` 构造函数签名，调用方不需要额外传参。

因此当前实际语义是：

| Channel | 当前投递语义 | 说明 |
|---|---|---|
| `shm/video/h264/main` | ordered | 编码参考帧不能随意跳 |
| `shm/video/h264/low` | ordered | 编码参考帧不能随意跳 |
| `shm/video/lcd_preview` | latest-only | 屏显预览只需要最新帧 |
| `shm/video/qr_scan` | latest-only | 二维码扫描慢时丢旧帧 |
| `shm/video/vision_rgb` | latest-only | AI/视觉调试慢时丢旧帧 |
| `shm/audio/pcm` | ordered | 音频按 seq 消费 |
| `shm/dvr/replay/video` | ordered | DVR 回放按 seq 消费 |
| `shm/dvr/replay/audio` | ordered | DVR 回放按 seq 消费 |

这和旧实现不同。旧实现只靠 channel 名是否包含 `/yuv` 判断 latest-only；新实现把 delivery policy 收敛到 common 内部配置函数，并把 `LCD_PREVIEW` / `QR_SCAN` / `VISION_RGB` 显式纳入 latest-only，避免新虚拟流因为命名不含 `/yuv` 而误走 ordered。

如果消费者确实需要主动拉取最新帧而不是 ordered callback，可优先评估 `common::ShmFetcher::fetchLatest()`，但要确认业务能接受丢帧。

## 11. 回调内不要做重活

回调跑在 `MediaPollerThread` 后台线程，建议控制在 1ms 内。

推荐：

- parse meta
- 校验 size/format/width/height/stride
- memcpy 到自己的 ring/queue
- notify 工作线程
- return

不推荐：

- 网络发送
- 模型推理
- 文件写入
- 阻塞等待
- 长时间加锁

如果要做 AI 推理或二维码识别，建议回调只复制或 move `FrameView` 到消费线程，业务线程再处理。

## 12. ZMQ 与 SHM 的边界

当前代码里有三类接口：

`ThreadPublisher` / `ThreadSubscriber`:

- `inproc://channel`
- ZMQ 线程内 pub/sub
- 适合小 proto 状态和控制

`ProcessPublisher` / `ProcessSubscriber`:

- `ipc://channel`
- ZMQ 进程间 pub/sub
- 适合小 proto 状态和控制

`ShmPublisher` / `ShmSubscriber`:

- 当前 sensor video/audio 实际使用的媒体帧通道

关键边界：

- `FramePool` 当前是进程内注册表和内存 arena，不是 POSIX mmap 跨进程共享内存。
- 同一进程内的 app/ai 可以直接用 `ShmSubscriber`。
- 如果是独立进程，只靠 `ShmSubscriber` 读不到另一个进程内的帧池。

如果 app 是独立进程，有三种方案：

方案 A：把消费者模块编进同一进程，用 `ShmSubscriber` 直接读。当前代码最匹配。

方案 B：做媒体 relay/bridge：

- relay 进程内订阅 `ShmSubscriber`
- 再通过 ZMQ ipc/tcp 或其他网络协议转发给外部进程
- 适合 PC 工具、外部 app、调试端

方案 C：改造为真正跨进程 shm：

- 使用 POSIX shm/mmap 或现有 `VSAPIZMQ_SharedChannel_t` 统一接入
- 当前 sensor video/audio producer 没有写 `VSAPIZMQ_SharedChannel_t`，不能直接用

## 13. 联调检查点

1. 先看控制是否成功：

```text
CAMERA enable=true -> success=true
VIDEO enable=true streams=[LOW_ENC / LCD_PREVIEW / QR_SCAN / VISION_RGB] -> success=true
MIC enable=true -> success=true
```

2. sensor 应出现类似日志：

```text
Video encoded source callback registered, channel=..., source=...
Video raw source callback registered, channel=..., source=...
audio pcm source callback registered channel=...
```

3. 消费者应能看到：

```text
view.seq() 单调递增
view.size() > 0
VideoFrameMeta.format = H264/H265/BGR565/Y8/RGB888
AudioFrameMeta.format = PCM_S16LE
```

4. 如果没有帧：

- 确认 `CAMERA` 是否已打开
- 确认对应 `VIDEO stream` 或 `MIC` 是否打开
- 确认订阅 channel 是否正确
- 确认 publisher 与 subscriber 是否在同一进程
- 确认回调没有阻塞导致 slot 被占满
- 对 `VISION_RGB`，确认模型读取大小不超过当前 padded readable payload

最小推荐对接方式：

- video 由 app 先用 `DeviceCommand` 明确打开 camera 和目标 stream，再用 `common::ShmSubscriber` 订阅对应 `shm/video/...`
- audio 先打开 mic，再订阅 `shm/audio/pcm`，按 `PCM_S16LE 16k mono` 处理

## 14. 迁移摘要

旧文档中的替换关系：

| 旧项 | 新项 |
|---|---|
| `DS1_RAW` | `LCD_PREVIEW`，proto 兼容别名仍为 3 |
| `DS2_RAW` | `VISION_RGB`，proto 兼容别名仍为 4 |
| `shm/video/yuv/ds1` | `shm/video/lcd_preview` |
| `shm/video/yuv/ds2` | `shm/video/vision_rgb` |
| DS1 NV12 480x480 | LCD 240x240 BGR565；QR 单独 240x240 Y8 |
| DS2 raw / padding height | VISION_RGB 640x360 RGB888，有效区 640x360，readable payload padded to 640x640x3 |
| DS1/DS2 HDI 互斥 | 单物理 `RAW_PREVIEW` 源按需派生多个 virtual stream |

二维码不再复用 DS1/LCD payload；二维码使用独立 `QR_SCAN` Y8 stream。
