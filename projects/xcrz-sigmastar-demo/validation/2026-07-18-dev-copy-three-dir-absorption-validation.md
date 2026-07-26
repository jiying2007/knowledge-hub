---
related:
- projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md
- sources/pcr02-project-docs/coverage.md
- sources/pcr02-project-knowledge/coverage.md
- sources/pcr02-project-scratch/coverage.md
target_version: ba398e5a
test_environment: Knowledge Hub host; source read-only audit plus exact-path deletion
aliases:
- xcrz_sigmastar_demo_dev 三目录完全吸收与删除验证
id: xcrz-sigmastar-demo-dev-copy-three-dir-absorption-validation-20260718
title: xcrz_sigmastar_demo_dev 三目录吸收与删除验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-absorption
  from: workspace://xcrz-sigmastar-demo-dev
  source_sha256: 9a1609ce2e07dfffdb540031912805b730662ba17df0773aada4cca1acf96f95
review_after: '2026-10-18'
review_status: human-reviewed-accepted
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; source closeout evidence only
tags:
- pcr02
- source-absorption
- deletion
- provenance
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
artifact_refs:
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- artifacts/manifests/xcrz-demo-dev-three-dir-raw-evidence-20260718.md
evidence_strength: file-level-sha256-manifest-plus-isolated-restore-drill
evidence_refs:
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- artifacts/manifests/xcrz-demo-dev-three-dir-raw-evidence-20260718.md
- 'source commit: ba398e5a'
created_at: '2026-07-18'
updated_at: '2026-07-26'
generated_by_ai: true
ai_role: extracted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
manual_validation_pending: true
manual_validation_reason: 媒体休眠板测、50 轮压力、功耗和 Sensor 构建漂移尚未闭环；本条目只证明来源处置，不证明功能完成。
summary_zh: 对 workspace://xcrz-sigmastar-demo-dev 的三个已授权目录执行逐文件吸收、排除、删除和恢复演练；长期正文只保留结论与证据索引，17 份唯一源文本移入不可搜索的冻结原始证据，不把历史内容当作当前项目事实。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# xcrz_sigmastar_demo_dev 三目录吸收与删除验证

## 结论

本条目记录对 `workspace://xcrz-sigmastar-demo-dev` 下三个精确目录的来源收口。243 个非 Git 内容文件均进入逐文件 manifest：已有权威来源的只保留 hash/provenance，缓存和 Git object 排除，17 份没有其他可靠来源的文本保存在不可搜索的冻结原始证据中。

本条目只证明来源已分类、删除边界已执行且恢复材料在执行时通过隔离校验，不证明媒体休眠、功耗、压力或板端功能完成。

## 权威证据

| 证据 | 用途 |
| --- | --- |
| `artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl` | 243 个文件的路径、大小、SHA-256、处置和目标引用 |
| `artifacts/manifests/xcrz-demo-dev-three-dir-raw-evidence-20260718.md` | 17 份唯一源文本的冻结证据；不参与默认检索 |
| `auth-20260718-xcrz-demo-dev-docs-knowledge-scratch-absorb-delete` | 精确删除范围、回滚和验证授权 |
| source commit `ba398e5a` | 外层工作区身份；不替代未提交源文本证据 |

执行时创建的临时压缩包已经完成隔离恢复演练，但临时目录不再作为长期证据引用。长期恢复依赖逐文件 manifest、冻结原始证据和可追溯 source commit。

## 处置结果

- `docs`：44 个文件；27 个已有权威来源，17 个唯一文本进入冻结原始证据。
- 嵌套知识目录：191 个非 Git 文件；非缓存内容绑定精确 source commit，13 个可再生缓存排除。
- `scratch`：8 个 Markdown；只提取可复用结论，raw session、脏工作树和二进制变化不进入长期正文。
- 总计：243 个非 Git 内容文件，0 个符号链接。
- 删除：只处理授权中的三个精确目录；没有修改远端、memory、active 状态或 owner decision。

## 可复用结论

1. 随机 `SIGBUS` 横跨多个线程和模块时，必须联合内核日志、I/O 并发、core 时间线和二进制身份取证，不能只按单一业务模块归因。
2. WAV 历史 core 存在二进制漂移风险；修复短读写、`EINTR` 和边界检查后仍须用当前二进制重新复现。
3. Diag 生命周期应保持 catalog/help 发现先行、provider owner 明确和事务化维护语义。
4. Media pipeline suspend 只有实现证据，板端 smoke、50 轮压力、功耗和构建漂移仍未闭环。

## 明确边界

- 不复制第二份 canonical 正文。
- 不把源文档中的 `active`、`verified` 或历史计划状态提升为当前事实。
- 不把 source commit 可恢复解释为当前脚本可运行。
- 不写 memory，不创建兼容路径，不保存内部网络端点。
- 默认检索只返回本验证摘要；冻结原始证据只能通过显式 artifact 路径读取。

## 剩余验证

- 修复 Sensor include/proto/header 漂移后重跑对象级和全量构建。
- 执行 idle、video、mic、DVR 和 remote-monitor 板端 smoke。
- 执行至少 50 轮 suspend/resume 压力。
- 记录 camera/mic 功耗测量点、平均值、峰值和版本身份。

在这些证据完成前，本条目保持 `reviewing` 和 `manual_validation_pending`。
