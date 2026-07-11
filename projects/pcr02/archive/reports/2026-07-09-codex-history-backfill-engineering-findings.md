# 2026-07-09 Codex 历史回填工程结论

## 摘要

本记录从本机 Codex 历史中回填尚未单独落入 Knowledge Hub 的 PCR02 工程结论。扫描范围覆盖 `~/.codex/session_index.jsonl`、`~/.codex/history.jsonl` 和 `~/.codex/sessions/**` 中可结构化读取的会话摘要；正文只保留可复用结论、验证摘要和后续风险，不复制 raw session、完整日志、附件、二进制或运行态缓存。

本次选择 3 组高价值主题：

- QMI8658 `SetCalibration`、动态 gyro 校准 reset 和轻量恢复语义。
- `app_product_test` 老化达标、复位键门禁、切入 `CALIBRATION` 后 LCD 行为。
- DS2 raw / AI 视觉链路高 CPU 的分层优化结论。

## 归档选择标准

- 已在 Codex 会话中形成清晰结论，且能从最终回复中追溯到代码点、验证命令或现场证据。
- 尚未在现有 `projects/pcr02/current/` 或 `projects/pcr02/archive/` 中以同等粒度单独归档。
- 结论对后续排障、发布或代码审查有复用价值。
- 不包含密码、访问凭证、客户资料、完整设备日志、core、二进制制品或私有运行缓存。

## 1. QMI8658 标定与恢复语义

来源会话：`019f36c3-fd44-77d3-9b82-6670862838d6`，时间 `2026-07-06`，线程名“评估 qmi8658 校准拆分”。

### 结论

`qmi8658_setcalibration()` 中 `STATIC_CALIBRATION` 和 `GYRO_DYNAMIC_CALIBRATION` 不应嵌套耦合。旧结构导致只开启 `GYRO_DYNAMIC_CALIBRATION` 时，动态 gyro 的 buffer、offset 和状态机不会被 reset。

推荐语义：

- `STATIC_CALIBRATION`：只清静态标定累计、offset 和 flag。
- `GYRO_DYNAMIC_CALIBRATION`：独立清动态 gyro 校准 buffer、offset 和状态机。
- 两个宏都未开启时，如果业务明确希望 `VSHDIIMU_setCalibration()` 具备恢复能力，应显式执行轻量 IMU 恢复，而不是依赖空的 calibration 实现。

会话中最终落地的轻量恢复为：

```c
qmi8658_powerdown();
qmi8658_delay(10);
qmi8658_wake_up();
```

该路径能重新配置 acc/gyro 并 enable sensor，适合作为“数据不更新、全 0、短时间异常、sensor enable 状态异常”的第一档恢复动作。

### 边界

轻量恢复不能保证覆盖所有 IMU 异常。以下情况仍需要更强诊断或二档恢复：

- I2C 通信异常或设备无响应。
- QMI8658 内部状态机卡死，需要 soft reset。
- 掉电/棕断后寄存器状态与本地 `g_imu` 状态不一致。
- `WhoAmI` 异常、设备地址异常、FIFO/sync sample/内部 clock 相关异常。
- 物理冲击、安装松动、饱和或噪声突刺。

后续如将该能力用于导航异常恢复，建议恢复后增加健康检查：

- 读 `WhoAmI`，确认仍是预期值。
- 读 `Status0`，确认 data ready。
- 丢弃恢复后的前几帧。
- 连续读 3 到 5 帧，判断 acc/gyro 是否全 0、固定值、饱和值或长时间不变化。
- 仍异常时升级到 soft reset 或完整 init。

### 验证摘要

Codex 会话记录的验证：

- `rtk git diff --check -- src/hdi_drv/hdi_imu/qmi8658/qmi8658.c` 通过。
- `rtk gcc -fsyntax-only ... qmi8658.c` 默认宏组合通过。
- `rtk gcc -fsyntax-only -DSTATIC_CALIBRATION ...` 通过。
- `rtk gcc -fsyntax-only -DGYRO_DYNAMIC_CALIBRATION ...` 通过。
- `rtk gcc -fsyntax-only -DSTATIC_CALIBRATION -DGYRO_DYNAMIC_CALIBRATION ...` 通过。

未确认项：未跑全量 SDK 构建，未归档板端恢复效果。

## 2. 产测老化到标定的门禁和 LCD 行为

来源会话：`019f374d-615f-7e53-a870-00d18c585383`，时间 `2026-07-06` 到 `2026-07-07`，线程名“修复老化后未进入标定模式”。

### 老化切标定语义

当前设计不是“老化 2 小时成功后立即自动进入标定”，而是：

1. `Stage=AGING` 时启动老化计时。
2. 达到 `[AGING_CTRL] DurationMs` 后，如果 `fail_bitmap == 0`，置 `qualified_latch=1` 并保存老化状态。
3. 达标后只是允许进入标定，不主动切阶段。
4. 收到复位键/工厂键 UART 事件后，调用 `VSPT_CommonHandleResetGate()`。
5. 门禁通过后才将 `product_test.ini:[INFO] Stage` 持久化为 `CALIBRATION`，随后 monitor 重载配置进入标定。

复位门禁核心是：

```text
qualified_latch == 1 && fail_bitmap == 0
```

`fail_bitmap=0` 只表示无失败项；如果 `qualified_latch=0`，仍会因为 `aging not ready` 拒绝切换。

### 调试判断

若现场宣称“已经超过 2 小时但按复位键未进标定”，应区分自然时间和程序认可的连续老化时长。会话中曾用状态文件判断：

```ini
continuous_elapsed_ms=2010000
fail_bitmap=0
qualified_latch=0
```

这表示程序只认可当前连续老化约 33 分 30 秒，无失败但未达标。常见原因：

- 中途设备或程序重启，未达标状态被清零重新计时。
- 文件不是同一次运行的最终快照。
- `product_test.ini` 在运行后才修改，程序未重新加载。
- 板端运行的二进制不是当前支持 `[AGING_CTRL] DurationMs` 的版本。

### LCD 行为结论

切到 `CALIBRATION` 后直接黑屏不适合产线体验，容易被误判为死机或阶段切换失败。会话最终选择的行为是：

- 不做旧配置兜底，仍由 `PROFILE_CALIBRATION_<Station>.EnableLcd` 控制是否启用 LCD。
- 当前配置要求 `PROFILE_CALIBRATION_1.EnableLcd=1`。
- 进入 `CALIBRATION` 后 LCD 文案随上位机绑定和标定步骤刷新。

典型显示状态：

```text
CALIBRATION / WAIT HOST
CALIBRATION / HOST READY
IMU AT180 / SAMPLING
IMU AT0 / WAIT STEP
TOF / RUNNING
CAMERA / RUNNING
WHEELS / RUNNING
IMU / PASS 或 FAIL
TOF / PASS 或 FAIL
CAMERA / PASS 或 FAIL
WHEELS / PASS 或 FAIL
SN / PASS 或 FAIL
```

### 验证摘要

Codex 会话记录的验证：

- `rtk git -C app_product_test diff --check` 通过。
- `rtk gcc -fsyntax-only ... app_product_test/pt_common.c` 通过。

未确认项：直接构建 `app_product_test` 子目录无有效目标；板端仍需确认 AGING 达标后按复位键切 `CALIBRATION` 时 LCD 按预期显示。

## 3. DS2 raw / AI 视觉高 CPU 优化链路

来源会话：`019f45f5-0166-7842-a761-5de0c8f46345`，时间 `2026-07-09`，线程名“评估80ms回调阻塞风险”。

### 分层结论

DS2 / AI 视觉链路高 CPU 需要分层处理：

- 降 `hdi_vi_out3`：减少或前移 DS2 producer 侧工作，尤其是 raw reader 取包、mmap/unmap、RGB 转换和 SHM publish。
- 降 `media_poll0`：减少 SHM subscriber callback 中的分配和大拷贝。
- 降 AI 总 CPU：限推理帧率、减少无效帧、降低每帧日志扰动。

仅在 AI 线程里丢帧不能显著降低 `hdi_vi_out3`，因为 producer 侧的取包、mmap、转换和发布已经发生。

### 已识别的关键链路

`hdi_vi_out3` 用户态重负载链路：

```text
hdi_vi_out3
  -> _VIDEO_DataCallback3()
  -> _VIDEO_ShouldDropDs2OutputFrame()
  -> _VIDEO_NormalizeDs2Rgb888()
  -> _VIDEO_DispatchNormalizedFrame()
  -> VideoRawFrameHub::publishRawFrame()
  -> ShmPublisher::acquire/commit
```

底层 raw output loop 还包括：

```text
SSPLAT_SYS_GetOutputPacket()
SSPLAT_PACKET_RAW_PA_Map()
API callback
SSPLAT_PACKET_RAW_PA_Unmap()
SSPLAT_SYS_PutOutputPacket()
```

如果系统态 CPU 高，`MI_SYS_Mmap/Munmap`、每帧 `GetFd/CloseFd`、driver buffer 取还和调度开销都是合理嫌疑点。

### 已形成的优化方向

1. `_VIDEO_NormalizeDs2Rgb888()` 由逐像素转换改成 4 像素展开，迁移历史 `_FRAME_CopyData()` 的低风险优化。
2. DS2 输出限帧必须表达“最高 fps”，不能写成固定 30 抽 20；低帧率输入不能被误丢。
3. raw PTS 可能为 0 时，API 侧基于 PTS 的限帧可能不生效；更稳的是在 HDI raw reader 中用 monotonic time 做时间预算桶。
4. HDI 前置限帧应放在 `GetOutputPacket` 之后、`Mmap` 之前；丢帧必须立即 `PutOutputPacket()`。
5. `Map` 或 `Unmap` 失败路径也应归还 packet，避免底层 buffer 被占住。
6. AI `pushVideoFrame()` 应避免每帧 `make_shared<vector>`；已有待处理帧时直接丢弃新帧，不做 1.23MB 拷贝。
7. 长期结构优化可评估 AI 专用 DS2 通道，只输出 `640x384`，或把 RGB 转换移出 `hdi_vi_out3`。

### 会话中的实现和验证摘要

会话记录的局部实现包括：

- `modules/api/src/api_video_pipe/api_video.c`
  - DS2 RGB888 转换 4 像素展开。
  - 有效高度不足时只清尾部 padding，避免整帧 `memset`。
  - DS2 最高输出 fps 限流从固定抽帧改为基于时间的限流。
- `modules/ai/AI_vision.cpp`、`modules/ai/AI_vision.h`
  - 预分配双缓冲。
  - 上一帧未被消费时丢弃新帧，避免无效大拷贝和 heap 分配。
- `modules/hdi/src/hdi_video/hdi_vi.c`
  - raw reader 读取 `u32Fps`。
  - 在 `Mmap` 前做 monotonic time 前置限帧。
  - 丢帧和错误路径归还 output packet。

会话记录的验证：

- `rtk git diff --check -- src/api_video_pipe/api_video.c` 通过。
- `rtk make modules/api_obj_all -j20` 通过。
- `rtk git diff --check` 在 `modules/ai` 和 `modules/api` 子仓内通过。
- `rtk make modules/ai_obj_all -j20` 通过，有既有 warning，无编译失败。
- `rtk make modules/hdi_obj_all -j20` 通过。
- `rtk make modules/api_obj_all -j20` 再次通过。

未确认项：

- 板端未完成最终复测。
- 需要部署后对比 `hdi_vi_out3`、`media_poll0`、`ai-vi-shm` CPU。
- 需要确认 30fps 输入时 DS2 实际输出约 20fps，1fps 输入时不误丢帧。
- `modules/hdi` 子仓存在其他非本次目标脏改，提交时必须隔离。

## 已跳过内容

- `019f46c0-92ae-76c2-9415-13a92f472f1a` “Fix thread name link error”会话在读取技能后被用户中断，只保留到链接错误现象和初步方向，未形成完整根因、修复和回归证据。本次不作为已归档工程结论。
- 2026-07-08 的 mm32spin023c 发布、IR light、播放器、WiFi 和 `VSAPIWIFI_DeInit()` 内容已由 `codex-daily-engineering-archive-summary-20260708` 覆盖，本次不重复归档。
- 2026-07-02 的 `prog_pcr02` 高负载监控、GDB 选择和 NFS runbook 已有独立条目或未提交候选，本次不重复整理。

## 后续建议

- 将 QMI8658 标定/恢复语义拆成项目 current runbook 或 debug note，前提是上板恢复路径验证补齐。
- 将产测老化门禁和 LCD 行为同步到 `app_product_test` 项目交付文档，避免产线误判“老化达标后应自动进入标定”。
- 将 DS2/AI 高 CPU 优化作为独立性能记录继续跟踪，下一轮必须补板端 CPU 对比数据。

## 归档元信息

- Source: `~/.codex/session_index.jsonl`、`~/.codex/history.jsonl`、`~/.codex/sessions/**`
- Source IDs: `019f36c3-fd44-77d3-9b82-6670862838d6`、`019f374d-615f-7e53-a870-00d18c585383`、`019f45f5-0166-7842-a761-5de0c8f46345`
- Topic: `pcr02-codex-history-backfill`
- Archive Candidate Path: `projects/pcr02/archive/reports/2026-07-09-codex-history-backfill-engineering-findings.md`
- Captured At: `2026-07-09`
- Sanitization: removed raw sessions, complete logs, attachments, credentials, binary content, runtime cache and device-private details.
- Provenance: summarized from local Codex final replies and command evidence summaries; raw sessions are retained only as source provenance.
- Verification: `rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "查找所有codex历史记录，归档一些值得归档还未归档的内容" --task-type archive --json`; `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run`
- Memory Candidate: no
- Gate Result: pass
