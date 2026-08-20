---
id: xcrz-pcr02-libmsc-link-contract-debug-20260806
title: PCR02新增QIVW诊断调用后的libmsc链接契约排障
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-06-pcr02-libmsc-link-contract.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-debug-summary
  from: current-codex-session
  source_sha256: 4303647446ffbb00d6c3bb19c435ec7052d56bb3936c24a4eca11ec5d3ed94fd
  temporary_source_retained: false
review_after: '2026-09-06'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug
- link
- libmsc
- qivw
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-06-pcr02-libmsc-link-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-06-pcr02-libmsc-link-contract.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-06'
updated_at: '2026-08-06'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-06'
manual_validation_pending: true
summary_zh: 当前libapp新增MSP/QIVW强符号引用但pcr02平台链接契约未同步libmsc；恢复依赖后最小、主程序及全量构建通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 新增 QIVW 诊断调用后的 libmsc 链接契约排障

## 现象

全量构建在链接 `prog_sensor_test` 时失败，`libapp.a` 中的 AI 诊断 provider 无法解析 `MSPLogin`、`MSPLogout`、`QIVWSessionBegin`、`QIVWSessionEnd`、`QIVWRegisterNotify` 和 `QIVWAudioWrite`。前序 Wi-Fi 编译告警不是本次链接失败的直接原因。

## 影响范围

- 项目：PCR02 SigmaStar SSC305 源码仓。
- 失败阶段：使用 `pcr02/pcr02.mk` 平台链接契约的应用最终链接，已首先在 `app_sensor_test` 暴露。
- 运行包原本已经通过 `pcr02/dep.mk` 携带 `libmsc.so`，本次未新增第三方二进制。

## 时间线

| 阶段 | 操作或观察 | 结果 |
| --- | --- | --- |
| 基线复现 | `rtk make app_sensor_test_app_all -j1` | 稳定出现 6 个 MSP/QIVW undefined reference |
| 符号核对 | 读取当前 `libmsc.so` 动态符号表 | 6 个符号全部由当前库导出 |
| 链接核对 | 检查 `pcr02/pcr02.mk` | 模块组含 `libapp.a`，但最终链接缺少 `-lmsc` |
| 单变量修复 | 在 AI Speech 依赖后恢复 `-L.../aiawaken/lib -lmsc` | 最小目标、主程序和全量构建均通过 |

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| Wi-Fi 告警导致失败 | 比对失败阶段与 linker 输出 | 告警发生在编译阶段，最终失败是独立的 undefined reference | 排除 |
| 当前 SDK 必须新增 `libw_ivw.so` | 核对目录和当前 `libmsc.so` 导出表 | 仓内没有 `libw_ivw.so`，当前 `libmsc.so` 已导出全部目标符号 | 排除 |
| 静态库 group 顺序错误 | 核对模块 group 和第三方库清单 | `libapp.a` 已在 group 内，真正缺失的是 group 后的符号提供库 | 排除 |
| 平台链接契约遗漏 `libmsc` | 修复前后单变量构建对照 | 添加后所有目标完成链接，ELF 出现 `DT_NEEDED: libmsc.so` | 确认 |

## 根因

当前 `libapp.a` 的 AI 诊断 provider 新增了对 MSP/QIVW API 的强符号引用，但共享的 `pcr02/pcr02.mk` 链接契约仍处于先前移除 `libmsc` 直链后的状态。调用方与平台链接依赖没有同步更新，导致最终链接器找不到已经存在于当前 `libmsc.so` 中的实现。

## 修复

在 `pcr02/pcr02.mk` 的其他 AI 第三方库区恢复：

```make
LIBS += -L$(BUILD_TOP)/libs/3rdparty/aiawaken/lib -lmsc
```

回退时删除该行即可。历史上曾有意移除 `libmsc` 直链，因此该恢复会重新引入启动期 `DT_NEEDED`；若后续必须保持延迟加载，应另立设计变更，把诊断 provider 的 MSP/QIVW 调用整体改为经过验证的 `dlopen`/`dlsym` 生命周期，而不能只删除链接项。

## 验证

- 修复前：`rtk make app_sensor_test_app_all -j1`，失败并稳定报告 6 个未定义符号。
- 修复后：同一命令通过。
- 主程序：`rtk make pcr02_app_all -j1` 通过。
- 全量：`rtk make -j4` 退出码 0。
- 差异：`rtk git diff --check` 通过，本次源码差异仅 `pcr02/pcr02.mk` 一行。
- 产物：`prog_sensor_test` 与 `prog_pcr02` 均记录 `DT_NEEDED: libmsc.so`；发布树已包含 `libmsc.so`。

## 后续动作

- 该记录保持 `reviewing`，不提升为团队通用规则。
- 若设备侧出现启动期资源加载或第三方库生命周期问题，结合既有 libmsc UAF 记录评估延迟加载设计；本次编译修复本身未执行设备 HIL。

## Provenance

- Captured at: 2026-08-06
- Source: 当前源码、构建复现、ELF 符号表与修复前后构建对照
- Sanitization: 未保存完整编译日志、二进制、设备端点、凭证或客户资料
- Memory Candidate: no
