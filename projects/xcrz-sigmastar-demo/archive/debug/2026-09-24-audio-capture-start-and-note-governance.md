---
id: audio-capture-start-and-note-governance-20260924
title: 音频采集首帧覆盖与备注输入治理
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-24-audio-capture-start-and-note-governance.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:bc78d367e9815febaae93e9d6942cc27433f5ad49c8d4a4cadd89e81dd909c7f
  source_sha256: bc78d367e9815febaae93e9d6942cc27433f5ad49c8d4a4cadd89e81dd909c7f
  temporary_source_retained: false
review_after: '2026-12-23'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- app-audio-test
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-24-audio-capture-start-and-note-governance.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-24-audio-capture-start-and-note-governance.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-24'
updated_at: '2026-09-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-24'
manual_validation_pending: true
summary_zh: 音频采集首帧覆盖失败与备注乱码的设备证据及源码修复边界
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频采集首帧覆盖与备注输入治理候选

## 范围与证据

项目源码：`workspace://xcrz-sigmastar-demo/app_audio_test`。一次板端 `near/voice/30s` 采集保存成功，但结构校验为 `frame_validation=-6`，`complete=false`。只读回取的事件和帧元数据显示：正式场景起点到首个有效输出为 41.685 ms，超过现有 32 ms 门槛；尾端距离场景终点 0.551 ms，窗口内有效样本 479488，刚好达到最低门槛。原总采样数 480000 不能单独证明场景覆盖。

同次记录中的 `session.json.note` 已含问号及残余非预期字符，表明输入内容在保存前已损坏。当前主机到设备 shell 的 UTF-8 字节传输测试正常；Windows 交互式 ADB 输入链的具体损坏点尚未在用户主机复测。

## 源码修复

- `--note` 改为仅接受 ASCII 字母、数字、下划线、短横线和点号，最多 200 字节；乱码中常见的 `?` 在采集前被拒绝。
- reader 在 profile 就绪后还必须发布一个新的有效输出帧，控制线程才开始正式场景计时。沿用原 5 秒启动期限；无有效输出则保留失败并记录 `capture_ready_timeout`。
- 首次板端复测显示 PTS/序号连续、窗口内有完整 480000 个有效样本，但回调到达呈突发间隔；首个窗口内有效回调晚于场景起点 38.390 ms，原 32 ms 首端门槛仍返回 `-6`。基于该证据把首端门槛调整为三个输出周期（48 ms），尾端 32 ms、样本量和 PTS 连续性要求不变；历史失败目录不升级为有效样本。
- `USER_GUIDE.md` 改为测试员工作卡，按预检、八场景逐项放行、失败停止、记录单与后续复测组织；八条正式命令仅在此处维护。参数、时间线与结果字段移到 `TEST_REFERENCE.md`，备注统一为 ASCII 编号，中文条件保存在主机侧记录表。

## 验证与边界

Host 全套定向测试和模块边界检查通过；隔离输出目录的 ARM 应用链接通过。首版修复已按授权部署并完成一次无运动近端复测，备注 ASCII 值正确保存，但结构校验仍为 `-6`。加入回调突发间隔的正反例回归后，第二版再次按授权部署并执行一次无运动 `near/voice/30s`。该轮 `session.json` 为 `complete=true`、`frame_validation=0`，备注为预期 ASCII 编号，程序 MD5 与候选一致；首个窗口内有效输出晚于场景起点 38.609 ms，尾端距离终点 5.591 ms，窗口内有效输出 480000 样本，PTS/序号连续，无采集错误或截止期失约。

这只证明本轮板端采集结构与备注保存通过；没有核验真人近端说话、声学质量、其他场景或长时重复性。现场程序写入、进程控制和运动测试应分别取得授权并核对制品身份。

后续一轮七场景现场回读均得到 `execution=0`、`cleanup=0`、`save=0`、`frame_validation=0`，且 `session.json.complete=true`。其中三次运动使用当时的 `+120/-120 RPM` 条件；程序记录了完整命令与新鲜里程计，但 `near-motion` 的后退窗口出现左轮约 1 秒接近零速而右轮仍接近目标的回报。`MotorObserve` 只检查回报是否过期和故障位，不比较实际 RPM 与目标值。因此七个 run 的采集结构可判通过，物理运动、声学与近端活动不能据此自动判通过；运动异常应先由现场负责人复核，不应直接提高到后续 `+240/-240 RPM` 条件。

本记录仅为项目 reviewing candidate，不晋升团队通用规范；不包含原始日志、录音、端点或个人信息。
