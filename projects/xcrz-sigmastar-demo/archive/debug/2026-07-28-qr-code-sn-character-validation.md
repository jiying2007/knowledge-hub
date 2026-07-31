---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-qr-code-sn-character-validation-20260728
title: PCR02 QR_CODE_SN字符校验失败分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-qr-code-sn-character-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019fa81a-c46a-7750-917f-516e5153adb0
review_after: '2026-10-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- qr-code-sn
- product-test
- validator
- privacy
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-qr-code-sn-character-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-28-qr-code-sn-character-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录SN长度十七已通过但reason=char表示字符白名单失败的判定链，建议只记录非法位置和字节值，不打印完整SN，并保留设备BuildID与上位机字节待核对。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 QR_CODE_SN 字符校验失败分析

## 现象

产测 Router 正常收到 `QR_CODE_SN` 消息，但写号返回失败。日志显示 `sn_len=17` 且 `reason=char`。

## 证据与判断

- Bridge heartbeat 和 Router 消息处理正常，排除通信链路未送达。
- 组件类型正确解码为 `QR_CODE_SN`。
- 长度错误会返回 `reason=length`；本次长度 17 且为 `reason=char`，因此长度已通过。
- `reason=char` 只会在至少一个字节不符合白名单时出现。
- “Process topic done”只表示消息处理结束，不表示写号成功。
- provenance：`codex-raw-sessions:019fa81a-c46a-7750-917f-516e5153adb0`。

## 字符规则

历史源码显示允许数字和大写英文字母，同时排除容易混淆的字符。常见失败输入包括：

- 小写字母；
- 被规则排除的混淆字符；
- 空格、连字符、下划线；
- 扫码枪附加的 `CR`、`LF`；
- 其他不可见控制字节。

本文不保存实际 SN，也不推断具体非法位置。

## 根因

可以确认当前失败属于字符白名单校验，不是长度、heartbeat 或 Router 通信失败。具体非法字节尚未确认，因为现有日志没有记录失败位置和脱敏字节值。

## 安全诊断建议

只增加以下脱敏字段：

```text
invalid_index=<0-based position>
invalid_byte=0xXX
```

不得打印完整 SN。上位机应检查 protobuf `sn` 字段的实际 17 个字节，并在序列化前明确处理扫码枪结束符。

## 验证

后续使用不含真实设备 SN 的合成向量覆盖合法值、小写、混淆字符、分隔符、`CR/LF`、NUL、长度 16/17/18，并核对设备与上位机的字节级一致性。

```yaml
manual_validation_pending: true
manual_validation_reason: 需要核对设备BuildID和上位机protobuf实际字节
required_followup: 使用合成SN向量执行设备与上位机联合字符校验
owner: leiwenjun
review_after: 2026-10-28
```

## 归档门禁

- Sanitization：通过；未保存完整 SN、日志、端点或凭证。
- Memory Candidate：no。
- Gate Result：`reviewing / byte-evidence-pending`。
