---
id: pcr02-ai-video-output-fps-integration-20260804
title: PCR02 AI视频输出帧率联调归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-08-04-ai-video-output-fps-integration.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: git-and-source-validation
  from: 2026-08-04当前源码、提交历史、构建验证及根仓库提交dfae60a3的脱敏摘要
  source_sha256: 1a95ba8cfc2d0723405d0818b67326cf9a5a4d3f91032223d8a56398429cccf2
  temporary_source_retained: false
review_after: '2026-11-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ai-video
- vision-rgb
- fps
- task
- iot
- sensor
- api
- hdi
- idempotency
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-04-ai-video-output-fps-integration.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-08-04-ai-video-output-fps-integration.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 固化PCR02由task/iot控制AI视频输出帧率的分层边界、0～30fps行为、0fps不停通道、重复命令幂等修复、构建证据和待补真机验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AI 视频输出帧率联调归档

## 归档目的与结论边界

本文记录 PCR02 应用侧由 task/iot 控制 AI 视频输出帧率的分层设计、实现约束、
已验证行为和剩余风险，供后续模块源码提交、设备计帧验证和相似虚拟视频通道
控帧需求复用。

当前可确认：

- task/iot 的 AI 业务命令能够通过 sensor 协议入口映射到 `VISION_RGB` 输出通道。
- API 对外只暴露通用的虚拟视频通道输出帧率能力，不包含 `AiVideo` 或 `AI YUV`
  业务命名。
- 相机 30fps 时，请求 0～30fps 对应输出 0～30fps；相机 1fps 时，请求 0fps
  输出 0 帧，请求 1～30fps 均受采集上限约束为 1fps。
- 0fps 只抑制 `VISION_RGB` 帧投递，不关闭通道、不销毁 reader、不改变通道
  引用计数或其他视频流状态。
- 相同 `channel + fps` 重复设置为幂等操作，不重置帧率累加器，避免控制命令
  重发造成低帧率输出突增。

结论边界：

- 已完成源码检查、交叉编译、库构建、最终应用链接和确定性帧率模型验证。
- 尚未在设备上对共享内存中的 `VISION_RGB` 帧进行实际计数，因此本文不是 HIL
  或量产验收结论。
- 根仓库已提交并推送公共头文件及 API/sensor 二进制；`modules/api` 与
  `modules/sensor` 源码在归档时仍是本地未提交状态，远端暂不能从模块源码完整
  重建该二进制行为。
- 本文不保存原始会话、完整构建日志、二进制、设备标识、网络端点、凭证或本机
  绝对路径。

## 背景与来源

协议起点为根仓库提交
`31ba036df45d05dc6c527452a20433d73c4a380e`，其中增加：

- `AiVideoFrameRatePayload.framerate`；
- `AI_VIDEO_FRAME_RATE` 设备命令；
- `ai_video_frame_rate` oneof payload。

后续根仓库已有 task/iot 预编译实现和配置：task 库包含
`AiVideoFrameRateCtrl` 与 `SensorCtrl::requestAiVideoFrameRate()`，iot 库包含
`AI_VIDEO_FRAME_RATE` 协议枚举。此次联调补齐 sensor 接收、API 通用控帧和最终
二进制集成。

根仓库交付提交：

- branch：`feat/sensor-ai-video-framerate`；
- commit：`dfae60a36ea5a9eaadbeb4fc33067fc448750357`；
- subject：`feat(video): 支持AI视频输出帧率控制`；
- 提交内容：公共 API 头文件、`libapi` 和 `libsensor` 静态/动态库。

模块源码基线：

- `modules/api`：`master`，基线 HEAD
  `267cba5d5aae1c5789dbf77b00bc3636e5a1ab7d`，本地有 2 个未提交修改文件；
- `modules/sensor`：`master`，基线 HEAD
  `be43cb5a33d52529de354319d6b4e9da4bd450f5`，本地有 3 个未提交修改文件。

## 分层决策

### task/iot 与 proto

task/iot 拥有 AI 场景、应用监控、通话和录像等业务语义，因此
`AiVideoFrameRateCtrl`、`AI_VIDEO_FRAME_RATE` 和
`AiVideoFrameRatePayload` 保留在该层是合理的。

### sensor

sensor 是协议与硬件能力的适配边界：命令处理仍识别
`AI_VIDEO_FRAME_RATE`，但进入 HardwareApi 后映射为通道语义
`set_vision_rgb_framerate()`，避免继续向下传播 AI 业务名。

### API

API 提供通用接口：

```c
VS_S32 VSAPIVIDEO_ViSetOutputFps(VSAPIVIDEO_Channel_e enChannel,
                                  VS_U32 u32Fps);
```

接口只接受虚拟视频通道，范围为 `0..VIDEO_FRAME_FPS`。0fps 的合约是
“suppress frame delivery without closing the channel”，不承担 AI 场景判断，
也不改变相机采集帧率或其他视频流。

### HDI

HDI 的 raw reader 已支持 `u32Fps`，并在 reader 目标帧率高于实际 Sensor FPS
时输出全部实际帧，因此无需新增 AI 专用 HDI 接口。

重要负向结论：HDI 丢帧逻辑中的 `u32OutputFps == 0` 表示“不丢帧”，不能把
协议的 0fps 直接下沉为 HDI reader 0fps，否则会得到与需求相反的结果。0fps
停投递必须由 API 虚拟通道层处理。

## 控帧实现

### 共享 RAW preview 源

共享 RAW preview reader 请求上限由 20fps 提升到 30fps，使 30fps 相机能够向
`VISION_RGB` 提供完整的 0～30fps 输出空间。LCD、QR 和 VISION 的默认输出仍
分别保持 20、10 和 20fps，由 API 在共享源之后独立控帧。

### 累加器

每个虚拟通道保存目标 `u32OutputFps` 和帧率累加器：

- 目标为 0：当前输入帧不投递；
- 目标大于等于实际输入 FPS：每个实际输入帧都投递；
- 目标小于实际输入 FPS：使用整数累加器均匀选择输入帧；
- 相机 FPS 变化或目标 FPS 真正变化时重置累加器，使首个目标帧及时输出。

目标输出始终受 `min(实际相机 FPS, RAW preview 上限)` 约束。

### 重复命令幂等

早期实现每次调用 setter 都重置累加器。模型复现：相机 30fps、目标 1fps 时，
如果在 0.5 秒处重复下发一次相同命令，该秒会输出 2 帧，违反 1fps 合约。

最终实现同时比较持久目标值与当前通道值；两者均已等于请求值时，在状态锁内
直接返回成功，不修改累加器。修复后相同模型仍只输出 1 帧。

## 行为矩阵

| 实际相机 FPS | 请求 FPS | 预期输出 | 说明 |
| ---: | ---: | ---: | --- |
| 30 | 0 | 0 | 保持通道开启，只抑制投递 |
| 30 | 1～29 | 1～29 | 整数累加器均匀控帧 |
| 30 | 30 | 30 | 每个输入帧投递 |
| 1 | 0 | 0 | 保持通道开启，只抑制投递 |
| 1 | 1～30 | 1 | 受实际采集 FPS 上限约束 |

## 验证证据

### 构建与链接

以下命令在 2026-08-04 执行成功：

- `rtk make modules/proto_script_start`；
- `rtk make modules/proto_lib_all -j20`；
- `rtk make modules/api_obj_all -j20`；
- `rtk make modules/api_lib_all -j20`；
- `rtk make modules/sensor_lib_all -j20`；
- `rtk make pcr02_app_all -j20`。

构建过程中曾发现 `sensor_info.pb.*` 生成物落后于 `sensor_info.proto`，导致最新
sensor master 引用的 `MotorData::set_linear_velocity()` 与
`set_angular_velocity()` 缺失。重新生成 protobuf 后，proto、sensor 和最终
应用构建均通过；该问题不是协议源缺字段。

### 语义、符号与边界

- 稳定请求矩阵：30fps 下 0～30 全部匹配，1fps 下 0→0、1～30→1 全部匹配。
- 重复命令回归：30fps/目标 1fps，在 0.5 秒重复一次同值命令仍为 1 帧。
- `libapi.so` 导出 `VSAPIVIDEO_ViSetOutputFps`。
- `libsensor.so` 包含 `HardwareApi::set_vision_rgb_framerate(unsigned int)`。
- task 库包含 `AiVideoFrameRateCtrl::applyLocked()` 和
  `SensorCtrl::requestAiVideoFrameRate(unsigned int)`。
- iot 库包含 `AI_VIDEO_FRAME_RATE` 协议枚举。
- API 目标文件未出现 `AiVideo`、`AI video`、`AI YUV`、`modules/app` 或
  `DIAGPROV_Register`。
- 根仓库、API 子仓库和 sensor 子仓库的 `git diff --check` 均通过。
- 模块 API 头文件与根仓库发布头文件内容一致。

### 未完成或降级证据

- 项目规则列出的 diag layer/naming/coverage 检查脚本在当前工作区不存在，无法
  执行；本次使用直接依赖、命名扫描和 API 对象构建替代，但不冒充脚本门禁。
- 尚未执行设备共享内存计帧、快速 0↔N 切换压力测试或进程重启后的持久目标
  行为验证。

## 风险与后续动作

1. 优先在 `modules/api` 和 `modules/sensor` 分别完成 owner review、提交和推送，
   使远端源码与根仓库二进制恢复可重建一致性。
2. 真机分别在 Sensor 30fps 和 1fps 下，对请求 0、1、15、29、30 计数至少
   10 秒，并确认 PTS 单调。
3. 增加重复同值请求、0→N、N→0、相机 30→1 和 1→30 的压力序列，确认无瞬时
   超发、无通道 close/open、无 reader 引用计数变化。
4. 补齐或恢复 API AGENTS 指定的 diag 检查脚本，再执行正式提交门禁。
5. 由 API/sensor owner 人工复核本文；`reviewing` 状态不代表 active 事实、设备
   验收或发布批准。

## 回退边界

- 代码回退应以根仓库提交
  `dfae60a36ea5a9eaadbeb4fc33067fc448750357` 及后续模块源码提交为定位点，
  不手工混用不匹配的头文件与二进制。
- 若控帧异常，可回到固定 20fps 的既有虚拟 RAW preview 行为；不得把协议 0fps
  映射为 HDI reader 0fps。
- 回退不应修改相机 1fps/30fps 物理切换逻辑，也不应影响 LCD、QR、H26x、JPEG、
  BMP 或 DVR 生命周期。

## Provenance

- captured_at：2026-08-04
- last_verified：2026-08-04
- source：当前源码、提交历史、构建结果、符号检查和确定性帧率模型的脱敏摘要
- source workspace：`xcrz-sigmastar-demo`
- evidence state：source-build-link-model-validated
- manual validation：需要 API/sensor owner 复核，设备 HIL 待补
- generated_by_ai：true
- promotion：none
- memory candidate：no；结论为项目特定实现，不自动提升为全局规则
