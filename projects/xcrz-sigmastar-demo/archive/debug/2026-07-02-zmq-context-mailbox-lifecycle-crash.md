---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-zmq-context-mailbox-lifecycle-crash-20260702
title: PCR02 ZMQ context与mailbox生命周期崩溃分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-zmq-context-mailbox-lifecycle-crash.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f217a-de44-7d63-9a26-10e51cffbcb0
review_after: '2026-10-02'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- zmq
- context
- mailbox
- lifecycle
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-zmq-context-mailbox-lifecycle-crash.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-02-zmq-context-mailbox-lifecycle-crash.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录libzmq ctx_t::send_command访问slots mailbox崩溃的反汇编证据，优先排查context失效、socket跨生命周期和registry复用，并明确缺少core与BuildID时不能声明最终根因。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 ZMQ context 与 mailbox 生命周期崩溃分析

## 现象

Bridge 初始化 `ThreadSubscriber` 并连接 `inproc://` channel 时，调用栈落入 `libzmq` 的 `ctx_t::send_command()`，随后访问内部 mailbox/slots 时崩溃。

## 证据边界

- 当时本地 `libzmq.so` 带调试信息，能够对 `send_command()` 反汇编。
- 崩溃点对应从 context 的 `slots[tid]` 获取 mailbox，而不是简单的 endpoint 字符串解析。
- 同一 TCP PUB 端口和 SocketRegistry 复用是风险线索，但不是已确认根因。
- 缺少 core、完整寄存器和设备 BuildID，不能把推断写成最终根因。
- provenance：`codex-raw-sessions:019f217a-de44-7d63-9a26-10e51cffbcb0`。

## 假设与排除

| 假设 | 证据 | 状态 |
| --- | --- | --- |
| 普通 connect 参数错误 | 崩溃发生在 context slots/mailbox 解引用 | 不支持 |
| context 已析构或内部表失效 | 崩溃位置与失效 context 一致 | 高优先级推断 |
| socket 跨线程/跨生命周期复用 | registry 和共享 publisher 设计存在可能性 | 待验证 |
| `inproc` 角色反转直接导致崩溃 | 角色配置可导致连接异常，但不足以解释无效 mailbox | 低优先级 |
| `libzmq` 自身缺陷 | 无匹配 BuildID/core 与最小复现 | 未排除 |

## 当前结论

当前只能声明：表层崩溃是 `ctx_t::send_command()` 使用失效或不一致的 context/mailbox 状态。优先审计 context 的创建/销毁顺序、SocketRegistry 所有权、publisher/subscriber 是否跨线程使用，以及 shutdown 与 BridgeEntry 初始化是否并发。

## 后续验证

1. 获取匹配设备构建的 core、`libzmq.so`、主程序 BuildID 和寄存器。
2. 记录 context、socket、registry entry 的创建/销毁线程与时间。
3. 使用最小规则集分别验证单 publisher、多规则共享端口和重复 init/deinit。
4. 在 ASAN/UBSAN 可用的主机替身中压测 registry 生命周期。

```yaml
manual_validation_pending: true
manual_validation_reason: 缺少core、寄存器和设备BuildID，根因保持推断
required_followup: 取得匹配构建证据并执行context生命周期最小复现
owner: leiwenjun
review_after: 2026-10-02
```

## 归档门禁

- Sanitization：通过；无端点、raw 栈、二进制或凭证。
- Memory Candidate：no。
- Gate Result：`reviewing / inference-only`。
