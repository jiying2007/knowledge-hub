---
aliases:
- M5合并与本机一次性runtime准备
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-4c54541ddc25de0417e371c4
title: M5合并与本机一次性runtime准备
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-4c54541ddc25de0417e371c4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:4c54541ddc25de0417e371c4af37271083f1eabebc65ad2bca6e21987242c74e
  source_sha256: 0cc2acffd34872571551451a3cb30ccfffa0e1666b556105fa8946af70da950a
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
- projects/llm-agent/validation/provider-llm-agent-4c54541ddc25de0417e371c4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-4c54541ddc25de0417e371c4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 'verified_at: 2026-10-11 status: reviewing software_m5_certified: false owner_review: 无人类field或资格审批'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 4c54541ddc25de0417e371c4af37271083f1eabebc65ad2bca6e21987242c74e
---

# M5 合并与本机一次性 runtime 准备

verified_at: 2026-10-11
status: reviewing
software_m5_certified: false
owner_review: 无人类field或资格审批

用户已全部授权后续合并、治理设施准备与固定GPT-6.1-Sol medium单任务真实采集，无需重复询问相同权限；仍不以授权代实际field/owner证据。

PR194已match-head squash合并，main455df932，main CI38147680682 success但完整集成与签名CI SKIPPED，不能当正式rootCI。随后修复受信main显式forced workflow_dispatch的签名CI入口，保持四个required jobs全success、真实event和signed boolean force，不重标push。PR195六文件定向93/93与独立consumer23/23、Spec/Quality PASS；PR CI38148268149含完整集成PASS。PR195已精确head cec03308 squash合并至main af92f63dc91b668dd716e763ffe1f9683de7280a。

该最终main的新CI38148730646已启动。本文登记时仍在完整集成中，不声明其成功或已取得签名rootCI；后续须以实际完成记录及Sigstore回执核验。

GitHub设施实际：仓库runners为0；software-m5-runtime environment及variables查询404；repo variables为空；调用账号有仓库admin权限。没有创建environment、注册runner或dispatch模型。

没有专用主机时可继续使用本机一次性隔离runner。只读验证本机Linuxx64、Codex ChatGPT登录、bwrap user/pid只读隔离以及Docker可用；最小隔离namespace只挂载独立认证文件的Codex login status成功，没有复制凭据或挂载完整Codex配置/原工作区。官方actions runner2.338.0资产已下载并匹配官方发布摘要af4b794c1bc41d73d40535e3fe092a39f9679cd8d965954c2aca25a05ca41d32；仅准备安装包，没有安装服务或注册runner。

后续一次性runner须在独立临时目录运行，限制受信main的准确workflow/run/head；启动hook需独立核GitHub服务端run/job绑定本唯一runner，拒绝其它PR/job后才允许任务步骤。只读挂载固定Codex实体二进制和单独认证文件，隐藏原工作区与其余个人目录，既有登录能力不变。临时registration凭据仅内存和官方runner自身私有状态，不输出归档；一次任务后退出注销，不启动常驻服务。该执行设计尚待实现与独立复审，不能当设施已就绪。

真实signedCI、signedruntime、independent humanpilot与owner资格逐项验收。当前promotion实体Cosign离线PASS不能替代；历史5.0.0-rc.2和过期scorecard不改日期或重标。原主仓dirty保持，无live改动。所有已知失败、skipped与准备状态保留。

来源：GitHub PR/run/设施API实际回读、本机只读隔离与登录检查、官方release资产digest、源码与测试及独立审查回执。仅脱敏可复用结论，不归档凭据、raw session或模型原始响应。
