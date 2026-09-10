---
id: pcr02-dvr-ringframe-lease-closure-20260908
title: PCR02 DVR 调度落后与 ring-frame 零拷贝 lease 修复记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-08-pcr02-dvr-ringframe-lease-closure.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: session-source-build-host-validation
  from: PCR02 current working-tree source diff, host behavior tests, ARM cross-build and ELF symbol checks; board HIL pending
  source_sha256: f136fd3789eb5396a18f3a0aebca4433e164ba974b805b924d586ed85c9f3634
  temporary_source_retained: false
review_after: '2026-12-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- dvr
- ring-frame
- zero-copy
- lease
- sync-lost
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-08-pcr02-dvr-ringframe-lease-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-08-pcr02-dvr-ringframe-lease-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-08'
updated_at: '2026-09-08'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-09-08'
manual_validation_pending: true
summary_zh: 归档 PCR02 DVR 调度落后场景的零拷贝 lease、有界追帧、真实覆盖恢复、消费者迁移和验证边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 DVR 调度落后与 ring-frame 零拷贝 lease 修复记录

## 归档目的与结论边界

本文记录 PCR02 SSC305 DVR 录像在消费者线程调度落后时出现视频 PTS 间隙、音视频时长不一致的源码分析、ring-frame lease 契约、DVR 有界追帧、消费者迁移和验证结论。

当前已完成源码、Host 行为测试和 ARM 交叉构建验证；未执行匹配制品的板端长时录制、调度抖动注入或 soak。因此本记录只能作为 `reviewing` 项目调试候选，不能据此声明现场问题已在产品上关闭。

## 已确认背景

- VENC/VI 上游帧和音频源由现场确认无异常。
- MP4 写接口、文件 flush、SD I/O 和相关锁不作为本轮主要阻塞假设。
- 不调整线程优先级、调度策略或 affinity，避免影响其他实时线程。
- 不修改 MP4 通用库。
- DVR 原顺序读取在消费者落后超过阈值时会主动寻找后续关键帧；真实落后超过 ring 容量时还会发生物理覆盖。

## 设计决策

### 零拷贝 lease

- 使用 `Acquire -> 同步消费 -> Release` 代替直接返回未保护的 ring payload。
- 每个 reader session 只有一个游标，只允许一个 outstanding lease；同 reader 第二次 Acquire 返回 `VS_ERROR_BUSY`。
- 一个 writer 支持多个独立 reader；多个 reader 可以同时 lease 同一槽位。
- slot 使用保护计数，任一 lease 未释放时 writer 不得复用该槽位。
- lease token 同时绑定 owner handle、单调 session cookie、lease epoch、write generation 和 slot index，拒绝跨 reader、陈旧 session 和重复 Release。
- held lease 存在时 `SessionClose` 返回 `VS_ERROR_BUSY`，不做无界等待。
- 普通 Acquire 与 pre-frame Acquire 共用唯一 FrameView 填充路径，保证 payload、extra data、PTS、序号、stream、pixel format、尺寸和 stride 一致。

### DVR 有界追帧

- DVR 使用 `READ_MODE_ORDER_NO_DELAY_SKIP`，不执行 legacy delay-triggered key-frame skip。
- 20 ms callback 第一轮至少成功写入一个 packet 时，最多增加第二轮处理；正常无积压时第二次读取为空即退出。
- 每次回调最多两轮，不形成无界 drain，也不改变线程调度。
- MP4 写入直接使用 lease payload，写调用返回后立即 Release，不增加大视频帧复制。

### 真实覆盖恢复

- `ORDER_NO_DELAY_SKIP` 只保证不主动跳帧，无法恢复已被 ring 物理覆盖的数据。
- 在游标推进前检测 generation；发生真实覆盖时第一次 Acquire 返回 `VS_ERROR_SYNC_LOST`，不得把 overwritten frame 伪装成正常帧或 `BUFFER_EMPTY`。
- DVR 收到视频或音频 `SYNC_LOST` 后关闭当前文件、清除首个视频关键帧和音频帧状态，并等待下一视频 I 帧重新开始。
- loss recovery 期间禁止 pre-roll 回溯，避免把覆盖前的旧 generation 带入新文件；新 I 帧和首个新音频 packet 写入后恢复正常 pre-roll 能力。

### 消费者边界

- RTSP 采用边界复制：当前 `libss_rtsp` C wrapper 同步进入 packet pool 构造路径，normal packet 构造时深拷贝 slice；Send 返回后释放 lease。该结论绑定当前三方库版本，升级后必须复核。
- LCD、二维码、产测分析在同步处理结束后 Release。
- protobuf 消费者先复制到消息对象，再 Release。
- 旧 Video/Audio Direct 和 ring raw payload 公共符号同步删除，不保留兼容别名。

## API 与兼容性

- 保留已有 read-mode 数值：`ORDER=0`、`LATEST=1`、`LATEST_IF_NEW=2`；新增 `ORDER_NO_DELAY_SKIP=3`。
- 新增 lease-blocked writer 独立统计，不与 ring overwrite count 混用。
- Video/Audio ReaderClose 透传底层 `VS_ERROR_BUSY`。
- 本变更是明确 breaking change：所有消费者、公共头、静态库和动态库必须同步更新；禁止新旧 ABI 混装。

## 验证证据

### Host 行为测试

实际编译生产 `api_ringframe.c`，仅 mock OS 内存、互斥锁、原子和时间层，覆盖：

- 双 reader 同帧 lease；
- 同 reader 并发 Acquire 只有一个成功；
- owner/cookie/epoch/generation/slot 校验；
- held lease Close BUSY；
- writer 槽保护和多 reader 计数；
- lease-blocked write 统计；
- double Release；
- pre-frame metadata parity；
- ring 真实覆盖后单次 `SYNC_LOST`，随后无新帧为 `BUFFER_EMPTY`。

单次测试通过，pthread 竞态重复 50 次通过。当前 Host 缺少 `libtsan_preinit.o`，TSAN 明确为 skipped，不计作通过。

### 交叉构建

以下目标在当前 working-tree 快照通过：API obj/lib、APP obj/lib、主程序、app_test、app_product_test、app_sensor_test、app_tool、app_ota、CLI、cmd_server 和 daemon。

API 公共头一致性、DVR refcount、ShellCheck 和相关仓库 `git diff --check` 通过。

### 负向符号门禁

- 正式源码旧 Direct/raw API 零命中。
- 当前动态库、`release/bin` 和正式候选程序旧 Direct/raw API 零命中。
- orphan `prog_main` 已从 release/output 隔离；本地构建同步脚本改为九个正式程序 allowlist，禁止任意 `prog_*` 回灌。

## 提交与制品边界

- 变更跨 API、APP、app_test、app_product_test 四个独立仓以及父仓公共头、预编译库、构建脚本和 Host 测试，必须按仓库边界分别提交。
- `app_product_test` 和父仓存在无关 dirty，提交时必须精确排除。
- 普通 app build 不自动生成匹配 debug 三件套，也不会进入既有 image/OTA；发布前必须重新 split-debug、核 BuildID，并重生 image/OTA。
- 本记录不保存二进制、原视频、raw 日志、设备地址、客户信息或凭据。

## 未完成与板端验收

- 使用匹配 BuildID 候选在设备执行单次 60 秒录制。
- 执行 5 至 10 次短循环、调度抖动窗口、长循环和 soak。
- 同时记录 video/audio seq gap、PTS gap、SYNC_LOST、lease-blocked writes、ring overwrite、MP4 视频/音频时长和致命日志。
- 出现 sync-lost 时确认旧文件正常关闭，新文件从 I 帧开始，恢复阶段不会回溯旧 pre-roll。
- HIL 结束核对安装制品 MD5/BuildID、进程健康和最终录像可播放性。

## 回滚

- 源码回滚必须同步回滚所有消费者和父仓公共头/预编译库，禁止仅恢复旧符号的一部分。
- 运行制品回滚必须成套恢复应用、`libapi`、`libapp` 和匹配 debug symbol。
- 不以调整线程优先级或修改 MP4 通用库作为回滚替代方案。

## Provenance

- captured_at: 2026-09-08 Asia/Hong_Kong
- source: PCR02 当前会话的源码 diff、Host 行为测试、ARM 交叉构建和 ELF 符号检查
- source snapshot: `modules/api` HEAD `74250fe78187cbe8404a42c13534fffa0285f736`，working diff SHA256 `fc934420b9a11fff26eb70c9f3de255e7627ed6ff66e91c5dd39af445b5d69f5`
- evidence level: source and Host verified; board HIL pending
- sanitization: raw media, raw logs, binaries, endpoints and credentials excluded
- memory candidate: no; pending owner review and board validation
