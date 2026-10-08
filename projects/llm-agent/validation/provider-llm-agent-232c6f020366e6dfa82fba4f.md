---
id: provider-llm-agent-232c6f020366e6dfa82fba4f
title: ADK临时Git fixture加固收口
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-232c6f020366e6dfa82fba4f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:232c6f020366e6dfa82fba4f3cf395f000f554a2420b602e8a8be9eb133f6f35
  source_sha256: 327a2fa3b47cb1703aff44b9a90e72d23d1b141190d7caf7e6bdd0084540eab3
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
- projects/llm-agent/validation/provider-llm-agent-232c6f020366e6dfa82fba4f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-232c6f020366e6dfa82fba4f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 最小修复统一fixture Git创建入口，隔离继承的GIT环境、global/system配置、hooks和template，显式关闭gc/maintenance及detach并持久到合成仓库local配置。保留两次独立构建、可复现身份与dirty-source拒绝断言。新增确定性敌意环境回归保证外部仓库HEAD/index不变及hook不执行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK临时Git fixture加固收口
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK临时Git fixture加固收口

最小修复统一fixture Git创建入口，隔离继承的GIT环境、global/system配置、hooks和template，显式关闭gc/maintenance及detach并持久到合成仓库local配置。保留两次独立构建、可复现身份与dirty-source拒绝断言。新增确定性敌意环境回归保证外部仓库HEAD/index不变及hook不执行。

负证据：旧流程在新增敌意环境下因invalid author date失败；新流程Python3.8和3.11定向各5/5通过。官方先前TemporaryDirectory清理.git非空的具体writer仍没有证据，本次只声明隔离加固，不宣称确定根因关闭。

初次PR175 source7.14.1候选本地97/97通过，托管三版本也均97/97，但run37394472190的contract-py3.11明确拒绝source version7.14.1到7.14.1。执行者遗漏README/CI每次合并require-advance，已replan前移全部版本投影至7.14.2，不放宽门禁、不重标旧回执。后续准备应在冻结范围前读取版本合并规则并运行真实base-manifest require-advance。

最终7.14.2快照完整本地97/97一次通过，receipt SHA256 dba74912c227e868fe4305669566b8057f2cec463d4a0807b0f06b68ed7404d6。strict非quick validate、版本前移CLI及diff检查通过。author-self-review两轮分别检查测试隔离与版本范围，非独立owner审查；完整分支无unstaged overlay。

PR175最终head d79cc650313d38b4fee72ed69cc0ed0d8569cb63的13项托管检查全通过后合并为main e9fab289f98961922342fa32a4f629067a5a9e21。source worktree在llm_agent/.worktrees/adk-fixture-source-20261006，已ff同步main、clean。合并tree37b5e02a544cb6a650137b239b29a9322ba00f98与受审分支相同。主线CI37395924472的9项全部成功，CodeQL主线也成功。

自动发布run37396400054成功；immutable v7.14.2非draft/non-prerelease，annotated tag7e82cb020cd89e57d511f8dd6b54643e65f0112c指向exact e9fab。实际下载归档SHA2566179c9853e47059123f1ef15f40acf34a95f04b063b2a3f238599ea6f0f690e5匹配API digest与release contract。归档release manifest明确clean exact e9fab/tree37b5、version7.14.2、reproducible/release_eligible；release contract status pass。

消费边界：root与Codex继续绑定真实签名发布7.14.1/19dafa，原ADK消费checkout保留该exact detached快照。Agent/Skill/workflow/profile/template资产在19dafa与e9fab间逐字节无差异，本轮没有将测试新分支伪装为已导入runtime。root immutable pin、完整lock、interface require-worktree再次通过，tracked无差异。新release本地只校验制品完整性和来源字段，未声明新bundle已通过本地cosign导入。

无真实模型调用，无用户dirty/reference清理，无memory写入。源码/组件发布验证不代替owner、M5、产品或真实效果资格；消费升级可作为后续独立来源导入阶段处理，不能从本记录推导已经完成。
