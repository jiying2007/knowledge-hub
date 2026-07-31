---
related: []
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-ai-audio-stream-order-eof-contract-20260713
title: PCR02 AI音频流顺序与EOF语义契约归档
kind: architecture
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/design/2026-07-13-ai-audio-stream-order-eof-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f50b9-16f3-7523-8220-0079d25fe813,019f5a5d-4503-7403-b644-4538bdcab3cb
review_after: '2026-10-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ai-audio
- shm
- stream-order
- eof
validation_refs:
- projects/xcrz-sigmastar-demo/archive/design/2026-07-13-ai-audio-stream-order-eof-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/design/2026-07-13-ai-audio-stream-order-eof-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 归档同一SHM通道START、DATA、END有序交付的实现边界，区分丢帧和seq跳号与真正乱序，并记录Parser read failed 1实际为正常EOF及stream_id隔离缺口。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 AI 音频流顺序与 EOF 语义契约归档

## 摘要

本文归档 AI 音频 `STREAM_START → STREAM → STREAM_END` 在单一 SHM envelope channel 中的顺序边界，以及播放器正常 EOF 被误记为 warning 的历史问题。正常单 publisher、单 channel、单 consumer worker 条件下不会主动乱序；更现实的风险是丢帧、sequence 跳号、新旧流交叉和结束时序过早。

## 适用范围

- AI 音频 producer、`shm/audio/pcm/ai`、Sensor audio worker 和流式播放器。
- 不覆盖 Agora downlink 的独立 `STARVE` 根因；两者通过 related evidence 关联。

## 权威来源

- source_id：`codex-raw-sessions`
- source_path：sessions `019f50b9-16f3-7523-8220-0079d25fe813`、`019f5a5d-4503-7403-b644-4538bdcab3cb`
- owner：`leiwenjun`
- source_status：历史源码与构建验证，板级回归待补

## 当前契约

1. 同一 publisher 按 `START/DATA/END` 写入同一 SHM channel。
2. 非 `/yuv` SHM subscriber 使用 ordered delivery，不采用 latest-only。
3. Sensor worker 单队列 FIFO 执行，不主动重排。
4. acquire 失败可消耗 sequence 而未 commit，因此 sequence 不连续不等同乱序。
5. ring 强制回收表现为丢帧或 gap，不是旧帧后来反超新帧。
6. 协议缺少 `stream_id/playing_id` 时，旧流未 drain 完便启动新流会造成语义交叉。

## EOF 语义

历史日志中的 `Parser read failed: 1` 对应 `PARSER_STATUS_EOS=1`，属于内存 stream 在 `STREAM_END` 后返回的正常 EOF，不是 SHM 丢帧。日志级别和调用方判断应把 EOS 与真正 parser error 分开。

## 历史验证证据

| Evidence | Result | Boundary |
| --- | --- | --- |
| AI/Sensor SHM 发送与 worker 源码核对 | 单 channel 内正常有序 | 未证明多 publisher |
| API player 定向构建 | EOF 分支修改能够编译 | 未执行板端播放 |
| 最终应用链接 | 当时通过 | 当前源树未复跑 |
| session provenance | 保存结论与命令摘要 | 不复制 raw session |

## 建议验收矩阵

- acquire 失败、queue 满、forced reclaim 和 sequence gap；
- 连续两个短流无间隔启动；
- `STREAM_END` 前后 pending frame 和 cache drain；
- 单/多 publisher 误配置；
- 正常 EOF 不再输出 error/warning，真实 parser error 仍可观测。

```yaml
manual_validation_pending: true
manual_validation_reason: 需要板端验证EOF日志、drain事件与新旧stream隔离
required_followup: 使用stream_id和sequence观测执行连续流及故障注入回归
owner: leiwenjun
review_after: 2026-10-13
```

## 风险与限制

- 若未来增加多个 publisher，现有顺序假设失效。
- 单靠扩大 ring 不能替代 stream identity 和正确释放时序。
- 本文不保存音频、raw 日志或用户内容。

## Review

- owner：`leiwenjun`
- review_after：`2026-10-13`
- 下一次复核：`stream_id` 契约、EOF 板测和 Agora downlink 关联。
- Memory Candidate：no。
