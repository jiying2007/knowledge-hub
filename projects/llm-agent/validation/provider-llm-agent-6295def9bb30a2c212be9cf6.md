---
aliases:
- M5执行来源与Gitlink身份修复验证闭环
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-6295def9bb30a2c212be9cf6
title: M5执行来源与Gitlink身份修复验证闭环
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-6295def9bb30a2c212be9cf6.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:6295def9bb30a2c212be9cf6ab73a4e4fb9a39b6e8d17ae0315e328f26f48437
  source_sha256: d194b7a0a6a2bdad13a8b3b4d750bd815030bd703c200a75054d95a2cfdba0c8
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-6295def9bb30a2c212be9cf6.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-6295def9bb30a2c212be9cf6.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 本轮修复三项审查问题：真实执行来源认证、managed Gitlink 实体身份绑定、执行前显式联网许可。源码基线为 `134d124ad2973f621f920f68eb14f4d0cbdbce65`，增量留在隔离工作树，未提交、推送、合并或更新
  live。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 6295def9bb30a2c212be9cf6ab73a4e4fb9a39b6e8d17ae0315e328f26f48437
---

# M5 执行来源修复验证记录

本轮修复三项审查问题：真实执行来源认证、managed Gitlink 实体身份绑定、执行前显式联网许可。源码基线为 `134d124ad2973f621f920f68eb14f4d0cbdbce65`，增量留在隔离工作树，未提交、推送、合并或更新 live。

## 已验证的行为

- 生产 runtime 消费端要求受信 workflow 的签名执行回执。测量摘要覆盖完整报告；修改模型、usage、response ID、执行器或源码后，重算普通摘要不能恢复原签名绑定。
- runtime 与签名 root CI 使用相同 source baseline，并核对 collector、producer 与 observer 的源码摘要。unsigned collector 输出 `qualification_eligible=false`。
- managed field 路径要求实际 HEAD Gitlink、独立子仓 HEAD、registry origin 与同一 pilot JSON 的身份一致。拒绝 dirty 和隐藏 index 标志；真实临时 Git fixture 覆盖 assume-unchanged 与 skip-worktree。
- 普通 execute 与 producer collect 都在没有显式网络许可时提前拒绝，不启动模型调用。
- 新工作流只接受 canonical main 的手动执行，固定 GPT-6.1-Sol / medium、最多一个任务，先核 owner 配置与制品 pin，再采集、签名、离线验证并导出。工作流代码存在不表示现实 runner、environment 与 owner 保护已经配置。

## 验证结果

| 验证 | 当前结果 | 证据范围 |
| --- | --- | --- |
| 新 provenance 反例 | 13/13 PASS | 含真实本地 Git fixture；密码学成功路径使用显式测试 mock |
| runtime smoke 命令 | 11/11 PASS | 缺联网许可零执行；输出路径拒绝覆盖与链接 |
| 独立 whole-increment 复审 | Spec PASS / Quality PASS | 隐藏 index 绕过修复后关闭，无剩余 confirmed finding；独立定向 52/52 PASS |
| ADK quick | 56/56 PASS | ADK 未修改 |
| 根仓完整回归 | 74/74 PASS | 覆盖最新隐藏 index 补强、runtime 与 rollover、workflow 兼容性；exit 0 |
| 源码冻结后 quick aggregate | 49/52，exit 1 | workspace fingerprint 稳定；三项负结果为 PATH 未提供 Cosign、隔离树缺 reference dirty 实体、历史 M5 资格不匹配及声明过期 |
| 真实旧 CI 与 ADK promotion 签名离线复验 | PASS | 实体 Cosign 3.1.3 与固定 trusted root 独立验证；不推导新 runtime 资格 |
| 新工具仓库外 help | PASS | 在非仓库 cwd 通过源码模块入口运行 |
| 原工作区保护 | PASS | HEAD、index 和 tracked diff 摘要与本轮前一致 |

旧 CI 回执测量摘要为 `e9aa86d59653b5170b12ac442b5b5da85a06759695498eac987dcccc623b0023`；ADK promotion 签名 payload 摘要为 `d607402e2e0e5248e0f53a4a525748e218b24bebeed9ef01d1397a49a73fbd02`。原 main HEAD 为 `30c7110eca5326a0bf6520733b9760293f930902`；index 摘要为 `7985679f94c0c03abab4b0627902038101bfc57fd1c57e1236be0bd2d0aeb1ba`，tracked diff 摘要为 `b2771be0c96c41a52881673090dfe9a2490171804f11196fd06704b69a33bd3d`。

本轮 quick 的机器结果保留于运行证据，未删失败检查或伪造参考实体。真实离线验证使用显式固定 Cosign 路径，不因 generic check 的 PATH 缺项而误报签名失败。快检结束后仅更新本验证记录与计划，功能源码未再变化；文档同步与 diff 检查单独复验。

## 尚未具备的资格

本轮没有真实模型、外网调用或 field 采集，也没有运行新签名工作流。历史 `5.0.0-rc.2` 候选与当前 ADK `8.0.5` 身份不一致，scorecard 过期，不能重标为当前资格。当前 human field、owner 审定、受治理 runner 配置和同基线 signed runtime 仍缺真实证据，整体 M5 保持阻断。

隔离工作树不包含原工作区的 reference dirty 实体；对应检查缺失不能伪造目录补齐。本地 quick 的环境与资格负结果单独保留。确定性测试、合成 verifier、独立代码复审和旧 CI 真签名各自只支持其验证范围。

归档目标是 reviewing 验证记录，不代表 owner 批准、active 晋升或产品放行。回滚通过审查本轮增量实施，不恢复生产端接受 unsigned 报告的 fallback，不删除现有证据或用户 dirty。
