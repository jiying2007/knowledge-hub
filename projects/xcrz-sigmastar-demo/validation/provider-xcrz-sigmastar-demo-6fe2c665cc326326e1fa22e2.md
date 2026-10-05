---
id: provider-xcrz-sigmastar-demo-6fe2c665cc326326e1fa22e2
title: 本地 GROS 构建与制品交付审查验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-6fe2c665cc326326e1fa22e2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:6fe2c665cc326326e1fa22e2b7ccdc5cc2b39b6091ff8c68bb855790fd219d18
  source_sha256: e45407488dbbc758aae4909cd4b961ee0bae6d41ea9d747ecc815776b08a4430
  temporary_source_retained: false
review_after: '2027-01-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-6fe2c665cc326326e1fa22e2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/provider-xcrz-sigmastar-demo-6fe2c665cc326326e1fa22e2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-05'
updated_at: '2026-10-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-05'
manual_validation_pending: true
summary_zh: 'status: reviewing topic: gros-native-build captured_at: 2026-10-05 last_verified: 2026-10-05 source: goal_gros.md、GROS.md、BUNDLE-V2.md、PLAN.md
  与本轮定向审查和测试'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 本地 GROS 构建与制品交付审查验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 本地 GROS 构建与制品交付审查验证

status: reviewing
topic: gros-native-build
captured_at: 2026-10-05
last_verified: 2026-10-05
source: goal_gros.md、GROS.md、BUNDLE-V2.md、PLAN.md 与本轮定向审查和测试

## 已验证工程基线

当前使用本地原生 CMake GROS，暂不接入或修改其他团队维护的框架。第一方源码、组件、依赖、生成与安装只由 CMake 描述；应用从自身目录构建，SDK根不承担应用编译。Python只用于已有输入、执行结果及制品的独立审计，不恢复另一套构建图。

HDI/API/App采用统一模块/组件注册；OSAL及Platform沿用HDI仓，保持组件责任边界。外部团队组件只消费受控库和公共头，当前不恢复其实现源码。

## 交付模型

原生fresh执行记录实际配置/编译/安装，Host显式启用CTest后冻结非空测试集合、校验本轮结果及制品。源码身份采用声明输入、多仓Git内容身份与GCC -MD实际源码/头观察；拒绝stale及编译后文件/符号链接修改，不能宣称证明编译瞬间全部字节或可信Host。

候选adapter只消费已有stage、执行观察和显式catalog，关联实际notice、组件、用途和资源，生成bundle v2并回读，不编译、不签名、不推进current。新目录原子交接；发布后失败保留自身目录并尝试写失败marker。marker也失败时报告保留路径，由owner隔离，禁止当作成功候选。

动态正式导入要求实际匹配离线rootfs，重验目录树及静态依赖闭包，并核受管授权批准的baseline摘要。原生来源另要求签名绑定source-lock的producer资格。程序用途、法律准入、真实producer、产品rootfs、ABI/HIL和发布授权不能用fixture代替。

## 验证与未闭环项

Host CTest 86/86通过，含115项构建契约Python测试；SSC305/RDK交叉集成3/3通过；候选10项、SDK27项、编译输入9项及rootfs18项等契约回归通过；第一方硬切扫描通过。Proto-C/Diag首次/no-op/输出恢复/输入与工具身份变化生命周期通过；最后路径登记补丁另验受影响生成器单项与SSC重新配置。全流程与最终生成器独立静态复审、G00–G12需求证据复核通过；没有真实SDK发布或设备验收。

G00–G12框架能力及验收已收口，逐项依据见COMPLETION-AUDIT。工程验证、Runtime conformance及产品批准是独立验收线；域构建通过不能推导Runtime或产品PASS。

## 后续责任

在真实产品采用前，owner需提供可信producer资格、真实组件及用途catalog、许可证准入、匹配rootfs批准和板端HIL，并以受管签名绑定最终制品。代码/fixture验收不替代这些责任；候选归档也不提升为正式架构决策、规则或人工签收。

## 脱敏与来源

本候选不含私有端点、原始会话、完整日志、二进制或密钥；仅记录可复用决策、验证摘要和边界。不更新memory或全局规则。
