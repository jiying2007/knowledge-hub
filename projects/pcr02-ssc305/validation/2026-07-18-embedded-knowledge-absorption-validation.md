---
related:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md
- sources/embedded-knowledge/coverage.md
- sources/pcr02-project-knowledge/coverage.md
target_version: cadbf4d6777319c8d43b15f842cbea002cd94cef
test_environment: host-side source identity and filesystem audit; no device validation
aliases:
- SSC305 方法与工具来源吸收验证
id: pcr02-ssc305-embedded-knowledge-absorption-validation-20260718
title: PCR02 SSC305 方法与工具来源吸收验证
kind: validation
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-absorption
  from: source://embedded-knowledge
  source_sha256: e09afd5d842d6f41af37e1c6d57e621a308a32c412ec7f511765f018b06b0901
review_after: '2026-10-18'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; source closeout evidence only
tags:
- pcr02-ssc305
- embedded-knowledge
- source-absorption
- provenance
validation_refs:
- projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
artifact_refs:
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- artifacts/manifests/pcr02-ssc305-source-absorption-raw-evidence-20260718.md
evidence_strength: exact-source-commit-plus-file-level-manifest
evidence_refs:
- 'source alias: source://embedded-knowledge'
- 'source commit: cadbf4d6777319c8d43b15f842cbea002cd94cef'
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- artifacts/manifests/pcr02-ssc305-source-absorption-raw-evidence-20260718.md
created_at: '2026-07-18'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: extracted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
manual_validation_reason: 7 篇方法中的设备命令和板级步骤尚未逐项在当前 SDK、Hub 和真实板卡复验。
summary_zh: 核验已退役团队知识源的 178 个非缓存文件并提炼 7 篇 SSC305 项目方法；当前验证只保留中文结论和精确 source commit，原始长清单移入不可搜索证据，不保留内部端点、旧路径或兼容执行入口。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SSC305 方法与工具来源吸收验证

## 结论

项目副本中的嵌套知识目录不再作为第二知识入口。178 个非缓存文件绑定到 `source://embedded-knowledge` 的精确 commit；13 个可再生缓存和 Git 元数据不进入知识正文。7 篇 SSC305 方法只作为项目候选提炼，不能自动成为团队标准或当前设备验证结论。

## 来源和证据

| 证据 | 作用 |
| --- | --- |
| `source://embedded-knowledge` | 本地受控 source alias；不在长期正文保存内部端点 |
| commit `cadbf4d6777319c8d43b15f842cbea002cd94cef` | 178 个非缓存文件的来源身份 |
| `artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl` | 文件级路径、SHA-256 和处置 |
| `artifacts/manifests/pcr02-ssc305-source-absorption-raw-evidence-20260718.md` | 原始长清单和当时验证输出；不参与默认检索 |

临时压缩包不再作为长期证据。需要恢复来源时，使用受控 alias、精确 commit 和文件级 manifest。

## SSC305 项目方法摘要

1. 资料导航：先按 BSP、MI、ISP、IPU、Audio、DualOS、CM4 等能力域定位，再回到项目源码和设备证据；资料命中不代表项目已经实现。
2. 构建与升级：构建、install、产物身份、首启 smoke、升级切换和回滚必须形成闭环；`make all` 成功不等于 release 可交付。
3. 调试工具链：固定进程、binary、sysroot 和固件身份后再采 runtime/media/crash bundle；core 分析必须先做二进制配对。
4. Diag 回归：保持 catalog/help 发现先行，区分 local/remote runtime，新增命令需要 metadata、naming、coverage 和层次依赖门禁。
5. DualOS/低功耗：先定义 Boot、RTOS、CM4、Linux、App 的资源 owner，再核对启动、休眠和唤醒时序；功耗结论必须绑定测量点和版本。
6. 媒体与 AI：按 Sensor/电源/I2C、MIPI/VIF、ISP、SCL/VENC、IPU/算法、App 分层定位；AI 结论必须绑定模型、输入、前后处理和耗时。
7. 官方资料：只保留主题 ID、archive、路径和项目证据引用，不复制大段官方原文。

## 工具处置边界

- 旧 source 中的脚本没有迁入当前 Hub 工具链，也没有形成兼容 wrapper。
- source commit 可恢复不等于脚本在当前环境可运行。
- 重新采用任何工具时，必须进入当前工具源码、补依赖和安全审查，并执行 help/dry-run/定向测试。
- 冻结 `domains/embedded` 历史 corpus 不参与默认检索；只有精确登记正文能够成为当前知识。

## 剩余验证

- 对 7 篇方法逐项核对当前 SDK 路径和命令。
- 在真实 SSC305 板卡上验证构建、烧录、diag、媒体和低功耗步骤。
- 将验证通过的项目方法拆成独立项目 runbook；跨项目提升必须另走 owner review。

在上述验证完成前，本条目保持 `reviewing` 和 `manual_validation_pending`。
