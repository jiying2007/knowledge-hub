---
id: app-audio-test-usage-guide-20260922
title: 音频场景采集工具完整使用指南
kind: runbook
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/app-audio-test-usage-guide.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:38ac75f8f91dcadaa4dd9cbced64f52aeb2903f258cadddb206cef29d6d9fa7e
  source_sha256: 38ac75f8f91dcadaa4dd9cbced64f52aeb2903f258cadddb206cef29d6d9fa7e
  temporary_source_retained: false
review_after: '2026-12-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- runbook
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/app-audio-test-usage-guide.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/app-audio-test-usage-guide.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-22'
updated_at: '2026-09-24'
generated_by_ai: false
manual_validation_pending: true
summary_zh: app_audio_test的构建、设备准备、八类场景、数据判读和板端边界使用指南
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 音频场景采集工具完整使用指南
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 音频场景采集工具完整使用指南

> 历史候选快照，原文的 `1..300 RPM`、`3/3 RPM`、中文 `--note` 等命令已经与当前程序不符，禁止作为现场执行入口。现行操作顺序和正式命令以 `workspace://xcrz-sigmastar-demo/app_audio_test/docs/USER_GUIDE.md` 为准；该工作卡的运动基线示例显式使用前进 `+240 RPM`、后退 `-240 RPM`，程序没有隐式 RPM 默认值。具体参数与结果判读见同目录 `TEST_REFERENCE.md`。本条仍为 reviewing，待 owner 决定后续替换或归档。

## 适用范围

`app_audio_test` 是全 C、单轮、有人值守的诊断采集应用。它记录双麦原始输入、原始参考、算法实际参考、最终输出，以及播放、近端提示、轮速 TX 和遥测事件。

它用于定位 AEC、AES、NR/NN、AGC、双讲和运动噪声问题。一次采集成功不代表回声消除、唤醒、通话质量或设备运动通过，声学结论仍须结合录音和现场条件判断。

## 构建与制品边界

从集成源码根按以下顺序执行：

```bash
rtk bash build/sync_public_headers.sh --header hdi_ai.h hdi
rtk make -C app_audio_test/tests test
rtk make NC=1 modules/hdi_lib_all -j4
rtk make NC=1 app_audio_test_app_all -j4
```

先完成 HDI 库构建，再链接应用；不要并行执行这两个目标。输出为 `out/arm/app/prog_audio_test`。后编译应用不会自动进入已有 image 或 OTA，设备使用前须按独立部署流程核对制品身份。

`make -C app_audio_test/tests test` 覆盖参数、WAV、采样映射、保存、生命周期、播放线程、电机适配和正式场景帧完整性；这不替代板端验证。

## 设备准备

1. 人工停止占用 AI、AO 或 UART 的产品/测试程序，并处理 watchdog 或自动拉起 owner。工具只检查已知进程名，不能识别全部别名。
2. 确保没有其他音频、播放或电机控制程序运行。
3. 确认 `/dev/mmcblk0p1` 实际挂载到 `/var/run/media/mmcblk0p1`。未挂载、不可写或空间不足时工具应在运动前退出。
4. 运动前确认方向、空间、人员看护、低速参数和下层失联行为。工具不自动 kill、重启、挂载、清理 SD 卡、急停、锁止、清故障或反向补偿。
5. 首次按静止、播放、低速短运动、运动双讲顺序执行；每一步检查结果后再扩大范围。

零速只表示串口 TX 成功，不代表锁止、物理静止或 MCU 已确认执行。车辆滑行是允许且应记录的观测。

## 播放素材

涉及远端播放的场景必须使用 PCM、小端、16-bit、单声道、16 kHz WAV，最长 60 秒。素材必须覆盖计划播放窗口；工具不会循环、重采样或补静音。建议放入：

```text
/var/run/media/mmcblk0p1/audio_test/assets/far_end.wav
```

近端应由真人按提示说固定句子、唤醒词或弱语音文本。设备不播放提示音。远端素材和近端文本应不同，便于后续归因。

## 场景

| scene | 近端真人 | 设备播放 | 有限前后移动 | 用途 |
| --- | --- | --- | --- | --- |
| quiet | 否 | 否 | 否 | 底噪、静音段、异常增益 |
| near | 是 | 否 | 否 | 近端保真、弱词首词尾 |
| far | 否 | 是 | 否 | 纯远端残留回声、参考有效性 |
| double-talk | 是 | 是 | 否 | 双讲保护与残留 |
| motion | 否 | 否 | 是 | 电机、启动、滑行噪声 |
| near-motion | 是 | 否 | 是 | 运动近端保真 |
| far-motion | 否 | 是 | 是 | 运动回声路径变化 |
| double-talk-motion | 是 | 是 | 是 | 运动双讲综合场景 |

默认 profile 为 `voice`、正式场景默认 30 秒，时长范围为 20–60 秒。`--note` 最多 200 字节，用来记录距离、方位、噪声和文本 ID，不记录个人身份。

## 参数与预演

基础格式：

```text
./prog_audio_test capture --scene <scene> [--profile voice|call] [--seconds 20..60] [--note <说明>] [--dry-run]
```

所有首次执行先加 `--dry-run`。该模式只校验参数和输出时间线，不检查硬件、SD 卡或素材，也不创建目录。

近端静止预演：

```text
./prog_audio_test capture --scene near --profile voice --seconds 30 --note "正前方1m，文本A" --dry-run
```

静止远端采集：

```text
./prog_audio_test capture --scene far --profile voice --seconds 30 --play-file /var/run/media/mmcblk0p1/audio_test/assets/far_end.wav --play-volume 20 --note "静止，远端素材R01"
```

播放场景必须提供：

```text
--play-file <PCM16单声道16k WAV>
--play-volume <1..100>
```

## 双讲模式

双讲可指定：

```text
--pattern far-first|near-first|alternating
```

默认 `far-first`。

| pattern | 时间线 |
| --- | --- |
| far-first | 第 3 秒远端播放；第 6 秒提示近端；近端在结束前 5 秒停止；播放在结束前 3 秒停止 |
| near-first | 第 3 秒提示近端；第 6 秒远端播放；播放在结束前 3 秒停止；近端在结束前 1 秒停止 |
| alternating | 从第 3 秒起，每 9 秒按 3 秒远端独讲、3 秒重叠、3 秒近端独讲循环 |

`near_prompt_only` 和 `far_schedule_only` 是计划事件，不能当作真人已说话或扬声器已发声的证明。若出现 `console_prompt_dropped`，说明提示无法输出，近端窗口须人工复核。

## 运动

运动场景必须显式提供：

```text
--forward-rpm <1..300>
--reverse-rpm <1..300>
--forward-ms <100..10000>
--reverse-ms <100..10000>
--coast-ms <1000..10000>
```

RPM 为正逻辑幅值：前进使用正值，后退由工具转换为负逻辑值；适配器集中反转右轮原生符号，不使用 Sensor 的历史倍率补偿。

工具选择双轮速度控制模式，场景第 8 秒开始前进；前进结束发送零速，保留滑行间隔，然后后退，后退结束再次发送零速。后退必须至少在正式场景结束前 5 秒结束。

低速运动预演：

```text
./prog_audio_test capture --scene motion --profile voice --seconds 30 --forward-rpm 3 --reverse-rpm 3 --forward-ms 1000 --reverse-ms 1000 --coast-ms 2000 --note "空旷地面，人工看护" --dry-run
```

确认方向后执行时去掉 `--dry-run`。零速 TX、遥测、控制循环发生错误时，本轮终止，不继续后退。

运动双讲仅在前述场景已验证后执行：

```text
./prog_audio_test capture --scene double-talk-motion --profile call --seconds 30 --pattern alternating --play-file /var/run/media/mmcblk0p1/audio_test/assets/far_end.wav --play-volume 20 --forward-rpm 3 --reverse-rpm 3 --forward-ms 1000 --reverse-ms 1000 --coast-ms 2000 --note "近端正前方1m，文本W01，远端R01，低速人工看护"
```

## 输出数据

每次运行创建唯一目录：

```text
/var/run/media/mmcblk0p1/audio_test/runs/run-<monotonic-us>-<pid>/
```

不会覆盖或删除旧目录。采集期间只使用预分配内存，结束后才保存到 SD 卡。

| 文件 | 含义 |
| --- | --- |
| mic.wav | 双麦原始输入，双通道交织 |
| ref_raw.wav | SDK 原始参考，双通道交织 |
| ref_used.wav | 实际送入算法的单声道参考 |
| output.wav | 算法最终单声道输出 |
| frames.csv | 单调时间、PTS、epoch、stage、帧号、采样偏移、样本数、输出有效标志 |
| events.csv | 场景、提示、播放计划、轮速 TX、原生轮速观测和退出事件 |
| session.json | 参数、MD5、profile、参考延迟、完整性及错误 |

WAV 中的样本连续存放；断流/epoch 变化必须结合 `frames.csv` 判断，不能把拼接 WAV 视为无缺口音频。

## 完整性与结果判读

`session.json` 当前为 schema v2。可用于正式比较的最低条件是：

```json
{
  "schema_version": 2,
  "complete": true,
  "frame_validation": 0
}
```

这只证明执行、清理、保存和正式窗口帧结构通过，不证明声学效果。

| frame_validation | 含义 |
| --- | --- |
| 0 | 帧结构及正式场景覆盖通过 |
| -1 | 无有效记录、容量或采集错误 |
| -2 | 场景起止标记缺失、重复或时长不足 |
| -3 | 阶段、epoch、序号、时间或采样偏移不连续 |
| -4 | 输入输出数量、PTS 或二比一配对关系不一致 |
| -5 | 正式场景有无效输出帧 |
| -6 | 有效输出没有覆盖正式窗口首尾或时长 |

v2 以唯一 `scene_start/scene_end` 限定正式窗口，逐帧检查序号、PTS、采样偏移、两个输入块到一个输出帧的配对和输出有效性。预热采样不能用于补足正式场景缺失的尾段。

`complete=true` 不证明真人近端实际发生、扬声器实际发声、双讲真实重叠、AO 物理排空、回声改善或唤醒通过。

## 建议分析顺序

1. 检查 `session.json`、文件是否完整和 `frame_validation` 是否为 0。
2. 检查 `events.csv` 是否有 `motor_tx_failed`、`motor_telemetry_failed`、`console_prompt_dropped`、异常退出或 discontinuity。
3. 用 `ref_raw.wav`、`ref_used.wav` 确认参考存在、连续且符合播放区间。
4. 将近端独讲、远端独讲、双讲、前进、后退、零速后滑行和尾声分段试听与计算指标。
5. 保留原始响度试听；如制作响度归一化对比副本，不得覆盖原始 WAV。

## 失败处理

| 现象 | 含义和处理 |
| --- | --- |
| 退出码 64 | 参数错误；用 dry-run 校验场景和必填参数 |
| owner conflict | 有 AI/AO/UART 占用；人工处理进程及自动拉起 owner |
| SD 创建失败 | 未挂载、挂载对象不符、不可写或空间不足；禁止回落写 rootfs |
| complete=false | 查看 frame_validation、events.csv 和原始 WAV；不用于正式算法对比 |
| console_prompt_dropped | 人工复核近端窗口；下轮保留终端或正常消费管道 |
| motor_tx_failed | 不扩大测试；检查 UART、MCU 和现场状态 |
| motor_telemetry_failed | 运动结果不完整；检查遥测和电机状态 |

## 板端验收边界

Host 测试和 ARM 链接不证明真实双麦、参考通道、VOICE/CALL 切换、播放连续性、CPU/RSS、SD 卡拔插/满盘、轮速方向、滑行、下层失联和中文双讲效果。

板端每一轮结束后先检查最终进程状态、SD 数据目录和文件完整性，再启动下一轮。原始录音只保留在受控 SD 卡或测试目录，不提交 Git，不写入知识正文。
