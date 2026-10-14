---
aliases:
- M5 单次运行磁盘负结果与存储修复
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-31988cd2df2d624396e03cd0
title: M5 单次运行磁盘负结果与存储修复
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-31988cd2df2d624396e03cd0.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:31988cd2df2d624396e03cd037e9bc99a4a3366e76d3819b8324179b53ae0890
  source_sha256: 77eed4deb664dd7402793bfb442384f6e61bd09a75b301bb2711b03ed2a79f42
  temporary_source_retained: false
review_after: '2027-01-11'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-31988cd2df2d624396e03cd0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-31988cd2df2d624396e03cd0.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 状态：reviewing candidate；真实模型测量未完成，M5、field、owner、G21/G22 与 release 资格仍为 BLOCKED。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 31988cd2df2d624396e03cd037e9bc99a4a3366e76d3819b8324179b53ae0890
---

# M5 新增单次运行的基础设施负结果与存储修复

状态：reviewing candidate；真实模型测量未完成，M5、field、owner、G21/G22 与 release 资格仍为 BLOCKED。

当前取证基线为 llm_agent main `23aeb9a760e2e0e13740e1cdba913cb684158fcb`、tree `738db2a2a701210945186838da88998e97b00ac1`，ADK `97cf0167e837c2095d9ec6a9431f5aa8c20a812b` / 8.0.6。此前 main 完整签名 CI 证据继续有效于其软件范围，不替代本次真实模型测量。

唯一新增实际 dispatch 为 GitHub run `38353421151` / attempt 1。工作流在 Set up declared Python 阶段失败，Collect one real upstream-observed measurement 仍为 pending，artifact 数量为 0。公开 check annotation 命中 `No space left on device`，注释摘要 SHA256 为 `c80ae087b6d997ef00742ae7dad70f975594420ff0f1ca7a9e21a307371bd643`。现场 df 显示根分区 100% 且仅约 45 MiB 可用，随后只读测量约 299 MiB；容量是动态现场值，不能将后一次空余量当成失败时空余量。该失败没有成功测量、用量或签名证据，不能声明运行通过。

SDK runner exit 0 没有覆盖 GitHub workflow failure。runner ID 23 已准确注销，独立只读回读注册表为空。旧 run `38343172937` 的未知模型额度、失败记录与所有已有工作区修改均保留。本次一次 dispatch 已使用，没有第二次 dispatch 或自动模型重试。

存储修复已实际落地为独立 prepare-only 入口：runner 数据使用 /vsdata 上的专用私有目录，校验固定路径、非 symlink、同 UID、0700 和至少 12 GiB 空余量后才解包。入口不包含执行、注册或 dispatch 能力，不删除原根分区数据，不修改共享 SDK/helper、live 配置或凭据。真实 prepare 已 exit 0：SDK 固定 2.338.0、原生二进制摘要、登录状态、current main 和 registry0 均通过；新 state 为 prepared，run/runner ID 为空。准备前后实际空余分别为 402359242752 / 401644503040 字节。

新存储位置下的真实 namespace 拒绝测试已 exit 0：guard 阻止后续步骤，进程已终止；该测试没有 auth mount、网络或模型调用。此类隔离证据仅验证软件生命周期，不能替代模型、签名、field 或 owner 资格。

复用模式：临时自托管 runner 必须先检查实际数据卷容量，工作目录、tool cache、private home 和私有 SDK 输出都放在同一受控容量充足卷上。下一次实际执行前重新检查容量、current main、实体摘要、环境 public pins、零 registry 和 pending runs；任何未知 POST/DELETE 只读对账，不能自动重发。

promotion_candidate=false；owner_review=false；do_not_promote_reason=缺成功模型测量、upstream 身份、usage、签名及领域资格。reduced_by=容量前置检查与 prepare-only 恢复入口；reduction_evidence=真实存储准备与无凭据 namespace 拒绝回执。rollback_path=保留旧状态与共享 helper，停用新 prepare-only 入口；不清理用户或旧 runner 的现场数据。

证据索引：second-authorized infrastructure verification、execution result、prepared review；storage-recovery state、dry-run、isolation-result，以及对应独立审查报告。宿主临时 compact 客户端存在三项未修 Major，未执行且禁用，不进入此存储修复或模型运行链路。

剩余项：如需继续取证，单独授权一次新的 bounded dispatch，再按 fresh whole-lifecycle readiness、实际执行、成功固定密码学验签或严格负诊断、准确注销及独立复核收口；不能使用本记录提升 M5 或生产资格。
