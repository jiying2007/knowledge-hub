---
id: provider-llm-agent-8aba0675f67e3ceadf5d9eac
title: 7.14.1 多仓主分支合并与回读
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-8aba0675f67e3ceadf5d9eac.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:8aba0675f67e3ceadf5d9eacf02d343ee088ec2b6049701f676486a0046acee8
  source_sha256: c3f20d015f7e0fd82bb2c20fba8a00fcb28f7222cc5770519d8b1e973f19a7ee
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
- projects/llm-agent/validation/provider-llm-agent-8aba0675f67e3ceadf5d9eac.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-8aba0675f67e3ceadf5d9eac.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 根仓PR181最终head f2380b50823e3532c0c9adcdbd06c587549e7bd9的8项托管检查全通过后，按已有授权合并为main a3ef58b035283cfa543af1b5a7627ec41dea26f1。实际根仓已快进同步，tracked无改动，仅保留用户既有参考目录；ADK子仓main仍为19dafa7c61355c04c08e87adcf3eae6946020f92，clean且与root
  gitlink、tree、manifest锁一致。合并后interface require-worktree、promotion claims及固定信任根的cosig
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 7.14.1 多仓主分支合并与回读
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 7.14.1 多仓主分支合并与回读

根仓PR181最终head f2380b50823e3532c0c9adcdbd06c587549e7bd9的8项托管检查全通过后，按已有授权合并为main a3ef58b035283cfa543af1b5a7627ec41dea26f1。实际根仓已快进同步，tracked无改动，仅保留用户既有参考目录；ADK子仓main仍为19dafa7c61355c04c08e87adcf3eae6946020f92，clean且与root gitlink、tree、manifest锁一致。合并后interface require-worktree、promotion claims及固定信任根的cosign验签再次通过。

Codex PR44的9项托管检查全通过后合并为main 9770140b813a612a2a673b0d3a9c6ddf90c32d38，实际源仓同步完成。五tracked用户修改的增删行完整保持，journal hash保持，未纳入本轮提交。旧Git不支持merge autostash，使用明确命名的stash保存再恢复，保留备份及stash。

实际source-to-live完成并通过最终check：344项单测、四profile smoke、来源/受管资产doctor及diff/drift。保留team-collab，配置hash未变；target输出和原plan的keep路径身份均匹配。此验证仅证明源码和运行资产一致性，不替代owner、M5或产品资格。真实模型评测未调用，收益没有量化。

剩余待核实事项：session-wrap LICENSE来源告警；ADK主线第一次CI临时Git目录清理偶发失败的具体写入者。已有负证据保留，没有以重试成功声称问题已修复。
