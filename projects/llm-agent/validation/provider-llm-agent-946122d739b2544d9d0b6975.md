---
id: provider-llm-agent-946122d739b2544d9d0b6975
title: ADK 8.0.1 文件IO安全迭代与来源到运行资产验证
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-946122d739b2544d9d0b6975.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:946122d739b2544d9d0b69759535ffe24325b0af05c3d31a98e2497133e7fa71
  source_sha256: 6ab8efd025dbb01227bb450fad1e91335d9835e0edd922b33774e14ee2248080
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-946122d739b2544d9d0b6975.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-946122d739b2544d9d0b6975.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 状态：reviewing candidate；此记录是可复用验证结论，不是owner审核、产品资格或模型收益认证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK 8.0.1 文件IO安全迭代与来源到运行资产验证
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK 8.0.1 文件IO安全迭代与来源到运行资产验证

状态：reviewing candidate；此记录是可复用验证结论，不是owner审核、产品资格或模型收益认证。

内部确定性实证确认四个输入输出风险：消费端intake/hash及runtime配置存在路径检查后叶节点替换窗口；SDK安装plan/receipt固定临时路径可跟随预置链接而覆盖外部文件。消费端用lstat、NOFOLLOW/NONBLOCK open、fstat身份与type校验，在实际descriptor上执行预算和读取，并统一脱敏系统错误。SDK用同目录独占随机temporary，descriptor写入、flush/fsync/关闭后原子替换，仅清理自身temporary；保留strict JSON输出预算和安装失败资产恢复。

普通/叶节点链接/FIFO/另一regular替换、descriptor关闭、精确预算、错误脱敏、旧temporary保留及write/fsync/replace故障回滚均有确定性回归。新SDK文档在POSIX为0600，调用方须控制父目录；不声称防御同权限任意并发writer或提供整个安装事务的断电恢复。

真实来源为canonical jiying2007/agent-dev-kit main46c35605a400f422414bfae85e809143e527c37c，8.0.1，treee9955c89b7e425b50f5a94507caaed53e4c7b71e，manifestblob9e6e83d06b7c3cb1ec379ed8756bcd5c0347bfab。ADK PR177已合并；mainCI37425994529九jobs与tag/release37426558324成功。immutable v8.0.1 annotated tag979f928fa272064c14aa4f62b10931b66cb23493指向该main；实际归档SHA256c8de31339c864c947f34abdb356c93f6a318ae440cb94045533fdb767f0377be与API、signed evidence、contract一致。固定main workflow/issuer及reviewed trusted-root验签Verified OK，不重标旧签名。

Root读取包47定向和74完整回归通过，独立复审发现的preflight错误归一化minor已修复；Root PR185已合并ab40301。ADK安全writer定向17、三Python3.8/3.11/3.12各98完整回归和30路由、wheel/lint/type/strict及audit通过；发布main checkout的same-snapshot receipt复验通过。首lint未用import失败保留且修复后重新冻结验证。

两消费者通过已有signed source工具采用实际8.0.1。Root PR186八checks成功后合并38b91b24a9f172c5f9c7b620f48c7c4f8f021e9b，SDK/lock/interface/status/签名证据同事务更新。Codex PR48九checks成功后合并38ea745592c9a86292170f59d61371a11fd7b8a5；42Skill、9Agent、4policy上游原始内容保持，31consumerREADME仅来源commit更新，9Agent全部R100；旧fixtures/license/notice保留。validator、integration、adapter和固定测试向量同步exact identity。首迁移不全的unit失败纠正后，Python3.8/3.11各342测试、build/doctor/audit和whole-staged复审通过，不拿旧失败或旧build当PASS。

实际source-to-live依次build、doctor、SAFE plan、dryrun、precheck、独立冻结复审、apply、postcheck；保持team-collab且不使用overwrite，configkeep exists。69内容变更准确限定版本路径与来源metadata及退役旧受管Agent路径；没有auth/session/history/memory/journal写action。用户五处有效修改通过指定stash保护并恢复，增删内容及权限核对一致；journal和config摘要保持。实际pre/post各344测试和四profile离线smoke通过，live doctor0/0，最终same476、diff0/missing0及changed0/stale0/unmanaged0。实际source fingerprintdb6d74c7d52823520f2b474eece0a284d62face6346c1557d0c096a27c06e67e，buildef1fef991aecccd149d1fbd044bdad8db82857999d0708ec050ad508ed050147，SAFEplana32f39eacb83a8ad61e2cd8a439382e016c382a93ed368af587d44f323d4b3fe，postcheck04f386d978ae0a3bb4c2e6b183303df0ec676b89e7d5e09361e9afcfe1c3049b。

资格边界保持：Root完整74通过，串行workspacequick50/52仍有原参考基线过期和历史M5/current不一致；release_authorized=false，不伪造owner/date/qualification。Root Codex gitlink是冻结证据依赖，实际运行资产源独立，不把历史pin当运行源。真实模型未调用，收益未量化，不以源码/临时smoke/live一致性替代产品或模型验证。各源码包、实际计划分别独立只读复审，分阶段Execution Policy检查未触发预算stop。

外部设计参考：[Python安全temporary](https://docs.python.org/3/library/tempfile.html)、[Python原子替换](https://docs.python.org/3/library/os.html#os.replace)、[SLSA验证期望](https://slsa.dev/spec/v1.2/verifying-artifacts)、[Anthropic分层评测](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)。仅参考输入，不进入runtime/fallback。

复用原则：读取约束绑定实际descriptor，生产输出预算与消费者相同；临时文件所有权和失败恢复分别验证；source、build、target、plan和实际live证据绑定同一链；保护用户dirty与配置；软件、模型、owner及产品资格单列。
