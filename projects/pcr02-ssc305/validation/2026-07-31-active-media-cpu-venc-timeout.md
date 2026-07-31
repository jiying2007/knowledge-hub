---
id: pcr02-ssc305-active-media-cpu-venc-timeout-20260731
title: PCR02 active 媒体 CPU 与 VENC 等待优化验证
kind: validation
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/validation/2026-07-31-active-media-cpu-venc-timeout.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: project-document
  from: PCR02 source project validation note
  source_sha256: 328a5c1c81a8029ed5d339a33994362c70d35b30874c83c61f335881f5cb23a2
review_after: '2026-10-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02-ssc305
- cpu-optimization
- hil
- venc
validation_refs:
- projects/pcr02-ssc305/validation/2026-07-31-active-media-cpu-venc-timeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/validation/2026-07-31-active-media-cpu-venc-timeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 记录 PCR02 active 编码负载的线程归因、HDI VENC packet timeout 10ms 到 30ms 的实机 A/B、正式制品身份、外部模块边界及真实 RTC/standby 未完成门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 active 媒体 CPU 与 VENC 等待优化验证
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 active 媒体负载 CPU 热点与 HDI 取流等待优化

## 结论

当前可在本仓独立复现的 `video encode + AAC reader` 场景中，整机双核 CPU
约 74%，`prog_pcr02` 约占双核总容量 57%。这已经接近用户观察到的“推流等
任务全部打开约 90%”，但诊断 provider 没有调用 `VSAPIRTSP_Init()`，因此
不包含 RTSP server/client、真实 Agora RTC 入会、远端用户和网络传输。
74% 与约 90% 不是同一个验收场景，不能直接比较收益。

本轮只落地一项低风险、单变量修改：把 HDI raw-preview 与 VENC packet
等待 timeout 从 10 ms 对齐到既有 30 ms `FRAME_DURATION`。20 秒同设备 A/B
中，两条 VENC 线程的 voluntary context switch 约下降 47%，VENC CPU 合计
从单核折算 2.65% 降到 1.91%，约下降 28%。整个 App 双核 CPU 从 57.21%
降到 55.82%，但同期整机 CPU 从 74.22% 变为 74.73%，说明全进程差值仍受
并行业务噪声影响；当前只对目标线程的下降作确定性结论。

该项收益真实但很小，无法单独把 90% 降到目标区间。下一阶段的主要容量位于：

- 本仓显示刷新：`sensor_disp0` + `sensor_disp1`；
- HDI 音频处理编排及外部 SEVC 算法：`hdi_ai_prc0`；
- 外部团队预编译模块：`ai-wakeup-aud`、`task_poller`、`nav.poll`；
- 第三方闭源 RTC：`libagora-rtc-sdk.so`。

## 场景与口径

- 设备、rootfs、启动 cwd 与依赖库保持一致。
- 使用正式 API 诊断入口启动 video 和 audio；video 创建 main/sub VENC，
  audio 启动 AAC reader。callback 会调用 `VSAPIRTSP_SendVideo/Audio()`，
  但 provider 没有执行 `VSAPIRTSP_Init()`，设备没有创建 RTSP 监听 socket，
  因此 send 调用不能代表真实网络发送。
- 预热完成后采样 20 秒。
- 整机 CPU：`/proc/stat` 两端 jiffy 差，占双核总容量。
- App CPU：`/proc/<pid>/stat` 两端 jiffy 差，同时报告双核总容量和单核折算。
- 线程 CPU：`/proc/<pid>/task/<tid>/stat`，表中均为单核折算。
- 唤醒代理：线程 `status` 中的 voluntary context switch 增量。
- 不记录设备地址、业务 token、频道、用户标识、二维码或 raw 业务日志。

直接调用 `diag.hdi.vi.h26x.start.run` 时失败，根因是该诊断 provider 把宽高
保留为 0；正式 `diag.api.media.video.start.run` 会补齐分辨率并可成功创建
VENC。这个现象是诊断入口参数缺陷，不是实际媒体 Pipeline 失败。

## 10 ms 与 30 ms 单变量 A/B

| 指标 | 10 ms 基线 | 30 ms 候选 | 变化 |
|---|---:|---:|---:|
| 整机 CPU（双核总容量） | 74.22% | 74.73% | +0.51 pp，场景噪声 |
| App CPU（双核总容量） | 57.21% | 55.82% | -1.39 pp |
| App CPU（单核折算） | 114.41% | 111.65% | -2.76 pp |
| `hdi_vi_preview` CPU | 5.51% | 5.41% | -0.10 pp |
| `hdi_vi_venc0` CPU | 1.36% | 1.01% | -0.35 pp |
| `hdi_vi_venc1` CPU | 1.29% | 0.90% | -0.39 pp |
| audio codec CPU | 2.14% | 2.08% | -0.06 pp |

| Thread | 10 ms voluntary CS/s | 30 ms voluntary CS/s | 变化 |
|---|---:|---:|---:|
| `hdi_vi_preview` | 139.9 | 120.2 | -14.1% |
| `hdi_vi_venc0` | 204.6 | 109.2 | -46.6% |
| `hdi_vi_venc1` | 189.9 | 100.7 | -47.0% |

两条 VENC 线程每秒上下文切换接近减半，且 CPU 同方向下降，符合“原先
10 ms timeout 在约 30 fps 输出上产生无效超时唤醒”的假设。preview 仍有
约 120 次/s 唤醒，说明该线程除 timeout 外还有帧到达、timer 和调度路径；
本轮不继续放大 timeout，避免未经验证地增加预览延迟。

## active 热点归属

下表来自同设备 active 短窗口的代表性线程样本，CPU 为单核折算。短窗口用于
排序，不作为 5～10 分钟放行数据。

| 优先级 | Thread/模块 | CPU | 源码与责任边界 | 本仓动作 |
|---:|---|---:|---|---|
| 1 | `sensor_disp0` | 约 12.45% | sensor/display 源码存在 | 作为下一单变量实验；需视觉验收 |
| 2 | `ai-wakeup-aud` | 约 10.39% | `libai.a`，外部团队 | handoff 性能契约 |
| 3 | `hdi_ai_prc0` | 约 9.20% | HDI 编排存在，SEVC 算法外部 | 先做 AEC/SEVC 音质与开销拆分 |
| 4 | `task_poller` | 约 9.20% | `libtask.a`，外部团队 | handoff 100 Hz poll 调查 |
| 5 | CUS3A | 约 8.25% | ISP/3A 路径 | 需画质与曝光稳定门禁 |
| 6 | `sensor_tof0` | 约 6.79% | sensor 源码存在 | 需 TOF 频率/延迟门禁 |
| 7 | `hdi_vi_preview` | 约 5.46% | HDI 源码存在 | 已完成 timeout 单变量 |
| 8 | AI VI shared-memory | 约 5.07% | AI 集成边界 | 与 AI 团队联合归因 |
| 9 | `nav.poll` | 约 4.65% | `libnavigation.a`，外部团队 | handoff 事件驱动调查 |
| 10 | `sensor_disp1` | 约 4.20% | sensor/display 源码存在 | 与 display0 同一实验验证 |

`sensor_disp0` 与 `sensor_disp1` 合计约占单核 16.65%，是当前本仓最明显的
下一候选。现实现 `UPDATE_INTERVAL_MS=40`，约 25 fps。把逻辑刷新试验性
降到 50 ms（20 fps）理论上可能节省 CPU，但会影响眨眼、跟随和动画平滑度；
在画面录制、撕裂/重影、交互延迟验收前不直接落地。

`hdi_ai_prc0` 的外部 SEVC 路径约占单核 9.2%。直接关闭 SEVC 可能换来较大
CPU 数字，但会改变 AEC/降噪和 RTC 音质，当前不作为可接受优化。

## 网络推流与 RTC 容量边界

历史完整业务样本中 `AgoraRTC` 线程约占单核 26%，但该数据来自旧制品和旧
场景，只能用于解释 74% 本地媒体负载到约 90% 完整推流之间的容量差，不能
作为当前版本的量化基线。

当前仓只有第三方 `libagora-rtc-sdk.so` 及 public headers，且诊断命令没有
RTC/RTSA 入会入口。真实 RTC A/B 必须由业务侧提供合法会话和远端用户，在不
记录凭证的条件下采样 join、publish、网络发送、leave 和重连。缺少该场景时，
不得声明“完整推流 CPU 已优化完成”。

现有 `diag.api.media.video/audio.start.run` 也不能用于 RTSP client 连续性
测试：它只打开 reader 并周期调用 send API，没有初始化 RTSP server。默认
554 端口拒绝和监听端口差分都证明没有创建 RTSP listener。后续若要保留 RTSP
诊断，应把 server init/deinit、动态 URL 返回和 client 连续读取作为独立的
测试基础设施改进，不能把当前 no-op send 误记为推流。

## 修改与制品

文件：`SourceCode/sdk/verify/xcrz_sigmastar_demo/modules/hdi/src/hdi_video/hdi_vi.c`

- raw preview `SSPLAT_SYS_GetOutputPacket()` timeout：10 ms → 30 ms；
- VENC `SSPLAT_VENC_GetPacket()` timeout：10 ms → 30 ms；
- 不改变帧率、分辨率、码率、GOP、编码格式、buffer depth、reader API 或
  callback 数据所有权。

诊断 A/B 候选 BuildID 为
`92e4ae5940a0fb406d8212d6f18d22a03912f1e9`。恢复
`SENSOR_DIAG_CMD_NODE_ENABLE=0` 后的正式 Release BuildID 为
`a200329e18100a32d1cd84454b365b78bf343210`，安装 ELF MD5 为
`622ba179606ec2a27cebec20f2167bc7`，独立 debug symbol 与主 ELF BuildID
一致。

## 放行门禁与阻塞

- 已通过：HDI Release 定向编译、App Release 构建、正式安装制品生成、
  Cortex-A32 hard-float ELF、strip/debuglink/BuildID 一致性。
- 已通过：诊断 reader `start-stop-start`；VENC0/1 按预期退出并重新创建，
  App 持续存活。
- 已通过：正式 `SENSOR_DIAG_CMD_NODE_ENABLE=0` 候选在隔离路径运行 20 秒，
  音频、预览、显示、IMU/TOF 线程存在，随后正常退出。
- 部分通过：候选进入自动 standby 后进程仍存活、TOF 工作线程退出；缺少可控
  业务唤醒输入，standby → active 恢复尚未验证。
- 待执行：真实 Agora RTC、端到端帧连续性、standby 恢复和 5～10 分钟
  active 长窗口。
- 待业务协作：真实 Agora RTC join/publish/leave 与远端收流。
- SSH 端口拒绝后改用设备现有 ADB 通道完成板端验证，不再构成阻塞。
- 当前工作树没有 HDI `AGENTS.md` 所列的三项 diag 静态检查脚本；该门禁记为
  `blocked-by-missing-test-infrastructure`，不记为通过。
- 设备安装 ELF MD5 始终保持原值；本轮创建的精确 `/data` 暂存和测试日志已
  清理。设备 init 未回收 4 个已退出测试 shell 的 zombie 条目；它们没有
  CPU、FD 或地址空间，但将在设备下次重启前保留进程表项。

在上述板端门禁完成前，30 ms 修改保留为候选，不覆盖设备已安装制品，也不作
量产/常驻放行声明。
