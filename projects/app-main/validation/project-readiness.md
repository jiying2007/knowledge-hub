---
id: app-main-readiness-validation-20260713
title: PCR02 Main App readiness validation
kind: validation
domain: projects/app-main
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- app-main
- project-readiness
- validation
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
decision_owner: leiwenjun
summary_zh: 记录 PCR02 Main App 的结构成熟度、本机 source 发现流程和工程/设备及发布验证待办；owner_ref 已绑定，源码可定位与 owner 确认仍不等于验证完成。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: projects/app-main/validation/project-readiness.md
project_id: app-main
readiness_slot: validation
aliases:
- app-main validation
- app-main-validation
related:
- projects/app-main/README.md
- indexes/project-readiness.md
---

# PCR02 Main App readiness validation

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，decision owner 与 owner_ref 已通过 hash-bound attestation 绑定；工程验证、实机/目标平台和发布证据尚未由本页完成。当前结论是 `structurally-ready / evidence-pending`，不是 release-ready。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] 项目 route matrix 能将 `app-main` 稳定解析为本项目。
- [x] 单一 evidence contract 已登记，统一 dashboard 可从项目入口访问。
- [x] search known-answer 与 link audit 通过。
- [ ] 本机 source 定位：运行 `knowledge-workspace-discover.sh --plan --json`，由 project gate 动态读取；结果不得复制到 tracked Markdown。

## 人工/真实环境门禁

- [ ] Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。
- [ ] 来源验证：确认 Git remote key、当前分支/版本和源码事实，Hub 不代替源仓事实。
- [x] 责任验证：真实 decision owner `leiwenjun` 已通过 `knowledge-hub-terminal-owner-attestation-20260716` 接受权威边界，并要求继续保持 `reviewing`。
- [ ] 工程验证：在源项目运行适用的构建、单元/集成测试并保留命令、版本和日志摘要。
- [ ] 设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。
- [ ] 发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。

## 证据记录模板

| 字段 | 待填写 |
|---|---|
| decision owner | `leiwenjun` |
| source repo / commit / version | pending |
| 执行环境与设备 | pending |
| 命令与返回码 | pending |
| 日志/截图/制品 hash | pending |
| 回滚验证 | pending |
| 结论和适用边界 | pending |

## Related

- [统一 readiness dashboard](../../../indexes/project-readiness.md)
- [项目入口](../README.md)
