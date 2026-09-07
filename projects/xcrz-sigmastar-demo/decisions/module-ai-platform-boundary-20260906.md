---
id: module-ai-platform-boundary-20260906
title: 四仓 AI 资产跨平台边界修正候选
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/module-ai-platform-boundary-20260906.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: session-summary
  from: workspace://xcrz-sigmastar-demo
  source_sha256: 2b08517a8cf0e3506221c3dddbe9a64dd94ba856379fc7d6c1cb408c5cf93a4f
  temporary_source_retained: false
review_after: '2026-12-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- decision
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/module-ai-platform-boundary-20260906.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/module-ai-platform-boundary-20260906.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-06'
updated_at: '2026-09-06'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-09-06'
manual_validation_pending: true
summary_zh: 修正模块与产品耦合，以选定源码和原生构建图为准，明确双源技能兼容和历史测试适用边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 四仓 AI 资产跨平台边界修正候选
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 四仓 AI 资产跨平台边界修正候选

- captured_at: 2026-09-06
- status: reviewing
- source: 当前四仓 AI 资产、团队工具及 refactor/hdi-hal-hard-cut 工作树的只读对照
- correction_of: projects/xcrz-sigmastar-demo/decisions/four-repo-ai-coding-team-knowledge-20260905.md

## 边界修正

HDI、API、APP、Sensor 是可复用模块，不能以产品前缀命名其通用身份。PCR02 的芯片型号由用户确认为 SSC305，此信息只属于对应产品适配。
模块契约v2只描述中立module_id、检查目录、技能和知识引用，不保存固定产品、构建目标或源码图。
原生构建以当前CMakeLists/sources.cmake和配置缓存为准；AI工具只转发显式build-dir/target，不自动configure。
旧Make-only工程可显式选择legacy适配，不得在CMake重构树恢复退役图。
设备预检显式提供serial、process和binary，不默认某产品进程或安装路径。

## 源码和测试权威

最新源码必须绑定选定分支、HEAD和当前dirty工作树。对照树虽正在跨平台重构，不能按目录名、文件时间或提交日期推断应覆盖谁。
本轮master HEAD由原生git rev-parse校准：hdi 9f13b9dd，api 748f48dc，app 8e0d5ab4，sensor 2936885a。
四仓source-evidence包含源内容hash、架构文档hash、stale_reasons与raw_fallback，仅作为本轮快照。
旧测试不匹配时分为接口适配、owner转交、明确退役或有效需求暴露代码缺陷；不能为适应新源码而删除仍有效断言。
上一轮暂不迁移判断仅对当时master工作树成立，不是跨分支或永久结论。

## 技能目录

tools旧目录13个技能，新目录1个技能，无同名正文重复；它是双源兼容，存在维护成本。
生成器过去只检查新目录，能造成旧目录/跨scope同名重复。本轮改为写入前检查docs/tools与两套布局，冲突时无写入失败。
长期建议单一.agents源；旧目录迁移须先盘点引用与安装软链接，验证新发现和幂等性，不能直接删除旧目录。

## 验证

- 团队真实目录check-all通过75项测试及其他强制门禁；1条既有到期复核提示不阻断。
- 专项23项通过；独立复审spec-compliance与quality均PASS。
- 隔离验收44/44，包含临时最小CMake C库实际configure/plan/build、错误cache、旧Make回流负例。
- 四仓默认check通过，原生技能发现均enabled且无错误。
- 10个团队文件增量补丁应用后哈希一致；已有4个业务脏改未变化；未修改重构树。
- 这些是工具与资产验证，不是跨平台业务固件、产品构建或Board/HIL证据。

## 待优化与责任边界

重构树已采用能力target及独立Diag，但HDI构建仍可见固定板级GROS_BOARD_PCR02_029C宏，应由后续产品/板级拆分审阅处理。
双源技能目录收敛、平台能力矩阵、原生最小消费者测试和团队发布仍需各自范围与证据，不能由本轮AI资产通过推定完成。
未提交/推送、不修改成员用户配置；新runbook保持draft。
Runtime Control缺少会话工件的门禁单列，不以其代替真实工具验证。
