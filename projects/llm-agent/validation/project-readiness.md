---
id: llm-agent-readiness-validation-20260713
title: LLM Agent readiness validation
kind: validation
domain: projects/llm-agent
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- llm-agent
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
summary_zh: 记录 LLM Agent 的结构成熟度与精确源码证据：本地与 origin/main 已一致到 150fdee，七个 gitlink 未变，隔离与当前主机远端恢复 Full 均为 62/62，313 篇 live-corpus
  通过；owner_ref 已绑定，但私有 submodule 零配置跨主机恢复、正式制品、release 与 rollback 仍待闭环。
promotion_decision: none; owner boundary attested, no active promotion or evidence-ready claim
path: projects/llm-agent/validation/project-readiness.md
project_id: llm-agent
readiness_slot: validation
aliases:
- llm-agent validation
- llm-agent-validation
related:
- projects/llm-agent/README.md
- indexes/project-readiness.md
---

# LLM Agent readiness validation

## 结论

结构性工作台已建立；本机 source 定位由未跟踪 local mapping 动态报告，decision owner 与 owner_ref 已通过 hash-bound attestation 绑定。`llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94` 已 fast-forward 发布到 `origin/main`，隔离源码与当前主机远端恢复 Full 均为 62/62，313 篇 live-corpus 校验通过。正式 artifact、release record、私有 submodule 零配置跨主机恢复和 rollback 证据仍未完成。当前结论是 `remote-source-restorable-on-current-host / evidence-pending`，不是 release-ready。

## 自动结构检查

- [x] registry item 与正文 frontmatter 镜像一致。
- [x] 30 项目 route matrix 能将 `llm-agent` 稳定解析为本项目。
- [x] 单一 evidence contract 已登记，统一 dashboard 可从项目入口访问。
- [x] search known-answer 与 link audit 通过。
- [x] 本机 source 定位：2026-07-17 动态发现 `workspace://llm-agent` 的 HEAD 为 `150fdee1509b899bbb0d8c0762b7a9313b63ba94`；绝对路径不写入 tracked Markdown。

## 人工/真实环境门禁

- [ ] Hub 结构验证：registry、route、正文镜像、链接和检索矩阵通过。
- [x] 来源验证：本地 `main` 与 `origin/main` 均为 `150fdee1509b899bbb0d8c0762b7a9313b63ba94`、分叉 `0 0`；远端由直接父提交 `383274fed93ad143cabb1dbd977e1b766eca5c04` fast-forward，七个 gitlink 未变化。
- [x] 责任验证：真实 decision owner `leiwenjun` 已通过 `knowledge-hub-terminal-owner-attestation-20260716` 接受权威边界，并要求继续保持 `reviewing`。
- [x] 工程验证：推送前隔离精确源码与推送后纯远端来源 clone 的 `check-all.sh --full` 均为 62/62；主工作区 `check-wechat-intake-ledger.sh . --require-corpus` 对 313 篇 corpus 返回 `mode=live-corpus`。远端 clone 的私有 `agent-dev-kit` 需要临时 SSH URL override，详见 `2026-07-17-portable-full-gate-remediation.md`。
- [ ] 设备验证：需要硬件行为的结论必须补 HIL/实机、环境条件和可复现实验记录。
- [ ] 发布验证：记录制品身份、版本、回滚路径和端到端验收，不以 Hub 文档替代发布签收。

## 证据记录模板

| 字段 | 待填写 |
|---|---|
| decision owner | `leiwenjun` |
| source repo / commit / version | 本地 `workspace://llm-agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94`；远端 `jiying2007/llm_agent@150fdee1509b899bbb0d8c0762b7a9313b63ba94`；发布前基线 `383274fed93ad143cabb1dbd977e1b766eca5c04` |
| 执行环境与设备 | 本机 linked worktree、精确本地 submodule clone、真实公众号 corpus，以及当前主机新建远端 clone；无设备 |
| 命令与返回码 | 推送前 Full 62/62、远端恢复 Full 62/62、main live-corpus 313 pass；远端 submodule 首轮 HTTPS 初始化 exit 1，临时 SSH override 后 exit 0 |
| 日志/截图/制品 hash | [可移植 Full 门禁修复验证](2026-07-17-portable-full-gate-remediation.md)；snapshot manifest SHA256 `93c926be842eb4480cce754a74f10f8e9fe5977f60cbce09c31d4320e2222e19`；正式 artifact 仍 pending |
| 回滚验证 | pending |
| 结论和适用边界 | source remote 与当前主机远端恢复已通过；任意新主机零配置恢复、artifact、release 与 rollback 仍 pending |

## Related

- [统一 readiness dashboard](../../../indexes/project-readiness.md)
- [项目入口](../README.md)
