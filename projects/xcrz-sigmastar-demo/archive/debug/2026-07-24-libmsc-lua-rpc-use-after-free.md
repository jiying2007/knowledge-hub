---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-libmsc-lua-rpc-use-after-free-20260724
title: PCR02 libmsc Lua RPC释放后使用core分析
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-libmsc-lua-rpc-use-after-free.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: registered
  from: manual-entry:knowledge-new.sh
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
  source_id: codex-raw-sessions
  source_path: codex-raw-sessions:019f9397-6a5d-7dd0-b796-a5f9a1487b9c
review_after: '2026-10-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- libmsc
- core-dump
- use-after-free
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-libmsc-lua-rpc-use-after-free.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-07-24-libmsc-lua-rpc-use-after-free.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-29'
updated_at: '2026-07-29'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-29'
manual_validation_pending: true
summary_zh: 记录AI语音core中libmsc同步Lua RPC等待方提前释放上下文、队列消费者随后访问已释放对象的高置信根因，以及主程序BuildID不匹配导致业务调用方仍待确认的边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 libmsc Lua RPC 释放后使用 core 分析

## 现象

2026-07-24 的 AI voice core 显示 `prog_pcr02` 在讯飞 `libmsc.so` 内收到 `SIGSEGV`。崩溃线程与 Lua engine 同步 RPC 消息相关，内存状态呈现对象已释放后再次被消费的特征。

## 影响范围

- 项目：PCR02 / SigmaStar SSC305。
- 模块：AI voice、讯飞 MSC/Lua RPC。
- 本记录只覆盖该 core 对应的第三方库现场，不代表所有 AI voice 崩溃。
- raw core、完整栈、设备端点和本机绝对路径未进入 Hub。

## 环境与证据可信度

- `libmsc.so` 的 BuildID 与本地第三方库匹配，库内函数名、偏移和反汇编可用。
- core 中主程序与当时工作区的 release/debug 主程序 BuildID 不匹配。
- 因此可以判断第三方库内部失效对象和消费路径，但不能可靠恢复业务调用方源码行。
- provenance：`codex-raw-sessions:019f9397-6a5d-7dd0-b796-a5f9a1487b9c`。

## 时间线

| 阶段 | 观察 | 结论 |
| --- | --- | --- |
| 同步 RPC 入队 | 消息保存 RPC proto 与同步等待上下文引用 | 消息生命周期跨越调用线程 |
| 等待方提前返回 | proto/同步上下文被释放 | 队列中仍有悬空引用 |
| Lua engine 消费 | 消费者读取已释放对象 | 触发 UAF 与非法地址访问 |

## 假设与排除

| 假设 | 证据 | 结论 |
| --- | --- | --- |
| 普通空指针 | 失效地址和 allocator 状态指向已释放对象 | 不支持 |
| glibc allocator 自身损坏 | 释放记录与 RPC 消息引用关系能够闭环 | 优先级低 |
| `libmsc.so` 同步 RPC 生命周期错误 | 等待方释放与队列消费时序一致 | 高置信 |
| 具体业务 API 调用方已确认 | 主程序 BuildID 不匹配 | 未确认 |

## 根因

高置信根因是：同步 Lua RPC 的等待线程在消息仍可能被 Lua engine 消费时提前返回并释放 proto/同步上下文，随后队列消费者访问悬空对象，形成 Use-After-Free。

该结论只覆盖 `libmsc.so` 内部根因；究竟由哪个 `QIVW*`、`MSP*` 或业务封装调用触发仍待匹配主程序符号确认。

## 修复或规避建议

1. 在 RPC 消息完成消费前保持 proto 和同步上下文有效，可使用明确所有权或引用计数。
2. timeout/cancel 路径先撤销队列消息或等待 consumer acknowledgement，再释放对象。
3. 业务层避免并发 stop、session teardown 与同步 Lua RPC。
4. 无法修改第三方库时，在上层串行化相关 API，并保留 crash rate 与 timeout 统计。

## 验证

本轮只归档历史证据，未修改源项目或复跑 core。落盘验证仅证明文档、registry 与检索契约；修复有效性必须使用匹配 BuildID 的主程序、同版 `libmsc.so` 和可重复触发场景验证。

```yaml
manual_validation_pending: true
manual_validation_reason: 主程序 BuildID 不匹配，业务调用方、修复方案和设备复现仍待验证
required_followup: 使用匹配 BuildID 的主程序符号复核调用方，并执行 timeout/cancel/stop 并发压力测试
owner: leiwenjun
review_after: 2026-10-24
```

## 归档门禁

- Source：受控 Codex session provenance。
- Sanitization：未保存 core、完整日志、绝对路径、设备端点或凭证。
- Memory Candidate：no。
- Gate Result：`reviewing / device-validation-pending`。
