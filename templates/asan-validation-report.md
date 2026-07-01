---
id:
title:
kind: validation
domain: projects/<project>
path: projects/<project>/validation/reports/<date>-asan-validation-report.md
scope: project-specific
visibility: team-internal
status: reviewing
owner:
source:
review_after:
created_at:
updated_at:
promotion: none
promotion_decision: none; project-local validation evidence only
tags: [asan, address-sanitizer, validation, non-pcr02]
related:
  - domains/embedded/runbooks/asan-debug-guide.md
validation_refs: []
artifact_refs: []
target_version:
test_environment:
summary_zh:
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
evidence_strength: project-local-asan-execution-evidence
evidence_refs: []
generated_by_ai: false
ai_role: none
ai_model_or_tool:
ai_generated_at:
human_reviewed_by:
human_reviewed_at:
review_basis:
---

# 非 PCR02 ASAN 验证报告

## 验证目标

说明本次要证明的 ASAN 目标，例如定位内存越界、use-after-free、double-free、栈溢出、堆泄漏，或证明某条路径在 ASAN 构建下未复现。

本报告只记录项目本地验证证据，不修改团队级 ASAN 方法论，不提升 `domains/embedded/standards/`，不替代 owner decision。

## 验证对象

| 字段 | 值 |
| --- | --- |
| project_id |  |
| repository / source |  |
| module_or_binary |  |
| target_version / commit |  |
| architecture |  |
| runtime_environment |  |
| owner |  |

## 构建证据

| 检查项 | 证据 | 状态 |
| --- | --- | --- |
| `-fsanitize=address` 已进入编译或链接参数 |  |  |
| 保留调试符号或可匹配符号文件 |  |  |
| BuildID、符号表或制品 hash 可匹配运行二进制 |  |  |
| ASAN runtime 库部署方式已说明 |  |  |

## 运行证据

| 字段 | 值 |
| --- | --- |
| `ASAN_OPTIONS` |  |
| 启动命令或服务入口 |  |
| 触发步骤 |  |
| 日志或报告路径 |  |
| 是否出现 `ERROR: AddressSanitizer` |  |
| 首发错误类型 |  |

## 结果矩阵

| case | 期望 | 实际 | 状态 | 证据 |
| --- | --- | --- | --- | --- |
| ASAN 构建启动 |  |  |  |  |
| 缺陷触发或 negative reproduction |  |  |  |  |
| 符号化可读性 |  |  |  |  |
| 修复后复测 |  |  |  |  |
| 回退普通构建 |  |  |  |  |

## 根因与修复

- 首发错误：
- 关键调用链：
- 根因判断：
- 修复动作：
- 复测结论：

若本次是 negative reproduction，明确写明未复现范围、覆盖输入、运行时长、样本数量和不能证明的内容。

## 资源与回退

| 项 | 观察值 | 风险 | 回退 |
| --- | --- | --- | --- |
| 制品体积 |  |  |  |
| 内存开销 |  |  |  |
| 性能影响 |  |  |  |
| runtime 库部署 |  |  |  |
| 现场恢复路径 |  |  |  |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk ...` |  | 中文摘要。 |  | Project / Tool / Device |  |

补充说明：

- date：
- cwd：
- scope：

## 结论

明确写：通过、失败、部分通过或不可判定。没有 ASAN report、构建参数、符号匹配和复测证据时，不得写“已验证”。

## 剩余风险

- 未覆盖路径：
- 环境限制：
- 与团队 runbook 的差异：
- 需要 owner 判断的问题：

## 后续动作

1. 将本报告登记到对应项目 registry item。
2. 在 `embedded-asan-non-pcr02-evidence-followup-20260629` 中追加 evidence ref。
3. 复跑 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics` 和 `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile max-body --full-regression`。
