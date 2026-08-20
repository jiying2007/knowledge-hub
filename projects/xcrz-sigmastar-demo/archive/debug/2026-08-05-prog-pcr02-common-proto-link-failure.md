---
id: xcrz-prog-pcr02-common-proto-link-debug-20260805
title: prog_pcr02 Common/Proto预编译库不一致排障
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-prog-pcr02-common-proto-link-failure.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-debug-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: 20cebb82fd2c20829c22c38cf1e9d215425870a81519b1364b6f43b7aa0de8b6
  temporary_source_retained: false
review_after: '2026-09-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug
- prog_pcr02
- common
- proto
- link
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-prog-pcr02-common-proto-link-failure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-prog-pcr02-common-proto-link-failure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-05'
updated_at: '2026-08-05'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-05'
manual_validation_pending: true
summary_zh: prog_pcr02链接失败源于Common/Proto源码与预编译库版本不一致；定向重建后普通和强制复链均通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# prog_pcr02 因 Common/Proto 预编译库过旧导致链接失败

## 现象

在 `codex/vi-fps-publish-20260731` 上构建 `pcr02_app_all` 时，源码编译完成，但链接 `prog_pcr02` 失败。主要缺失符号包括 `common::LoggingMutex()`、`common::SetCurrentThreadName()`、`common::ZmqPoller::~ZmqPoller()` 和 `proto::sensor_info::SocWakeupInfo` 构造/析构函数。

## 根因

父仓库中的 Common/Proto 源码已经包含上述定义，但随分支保存的 `libcommon.a` 与 `libproto.a` 不导出这些符号。父仓库源码与预编译 Common/Proto 动静态库不属于同一版本集合，导致 `prog_pcr02` 及其他静态模块在最终链接时出现大量 undefined reference。

链接顺序不是根因：`pcr02.mk` 已使用 `--start-group/--end-group`，在不修改链接命令的情况下，仅重建 Common/Proto 后链接成功。`pcr02` 源码回归也被证伪：强制重编 `pcr02` 自身后仍能成功链接。

## 最小修复顺序

1. 重新生成 `modules/proto`。
2. 重建 Proto 对象和动静态库。
3. 强制重建 Common 对象，避免旧对象时间戳误判为最新。
4. 重建 Common 动静态库。
5. 重跑 `pcr02_app_all`，再以 `-B` 强制重编 `pcr02` 验证。

## 验证

- 重建后的 `libcommon.a` 导出 `LoggingMutex`、`SetCurrentThreadName` 和 `ZmqPoller` 析构函数。
- 重建后的 `libproto.a` 导出 `SocWakeupInfo` 构造/析构函数。
- 普通 `pcr02_app_all`：通过。
- 强制 `pcr02_app_all`：通过。
- `app_test_app_all` 强制复链：通过。
- 生成 ARM EABI5 ELF `prog_pcr02`，Build ID 为 `edf595abb000afb0aa008c457b1486c9a358415d`。

## 边界

- 本轮只更新 Common/Proto 四个动静态库产物，没有修改源码。
- `tests/transport` 的默认交叉编译器不支持 C++17；显式使用项目 GCC 11.1 后，其 Makefile 又缺少 `protobuf-lite` 链接依赖。这是独立测试基础设施问题，不影响 `prog_pcr02` 已通过的链接证据。
- 库产物当前未提交，需 owner 审查后决定是否纳入分支。

## Provenance

- Captured at: 2026-08-05
- Source: 本地链接复现、符号表对照、定向库重建和强制复链
- Sanitization: 未保存原始长日志、设备地址、私有远端、凭证或二进制
- Status: reviewing
