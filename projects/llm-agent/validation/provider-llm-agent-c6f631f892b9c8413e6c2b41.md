---
aliases:
- M5 根仓交付与真实 runtime 负结果
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-c6f631f892b9c8413e6c2b41
title: M5 根仓交付与真实 runtime 负结果
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-c6f631f892b9c8413e6c2b41.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:c6f631f892b9c8413e6c2b417e1ec61e131d438411766e1fc7da5349f5a1bbdb
  source_sha256: 7d95d1ea142bbb1d3c2039e23b1d78e06359e459e9786dc4134cf3cdfa88a8c4
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
- projects/llm-agent/validation/provider-llm-agent-c6f631f892b9c8413e6c2b41.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-c6f631f892b9c8413e6c2b41.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-13'
updated_at: '2026-10-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-13'
manual_validation_pending: true
summary_zh: 记录日期：2026-10-13。项目：llm-agent。本文为 reviewing 验证候选，不能赋予 active、owner、human field 或产品放行资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: c6f631f892b9c8413e6c2b417e1ec61e131d438411766e1fc7da5349f5a1bbdb
---

# M5 根仓交付与真实 runtime 负结果

记录日期：2026-10-13。项目：llm-agent。本文为 reviewing 验证候选，不能赋予 active、owner、human field 或产品放行资格。

## 已实际交付的软件链

canonical ADK 8.0.6 固定于 `97cf0167e837c2095d9ec6a9431f5aa8c20a812b`，其 immutable release 和 signed promotion 已真实核验。根仓 [PR197](https://github.com/jiying2007/llm_agent/pull/197) 实际合并为 `80f59a3917ccc07142851ac30a8620aa42e1f929`，导入精确身份并使历史声明不再误标当前资格。对应 [push CI38342207909](https://github.com/jiying2007/llm_agent/actions/runs/38342207909) 全部技术任务成功，固定实际 Cosign 和 trusted root 的生产 typed 验签通过，独立审查通过。

根仓 [PR198](https://github.com/jiying2007/llm_agent/pull/198) 实际合并为当前 main `23aeb9a760e2e0e13740e1cdba913cb684158fcb`，tree `738db2a2a701210945186838da88998e97b00ac1`。修复 Collect 失败后的诊断保存缺口：严格字节、字段、类型和枚举白名单，只导出独立 unsigned negative summary；原 job 仍失败，成功仍只导出验证后的 signed measurement。负摘要不导出 raw model output、正文、SDK 日志或凭据，固定 qualification/certified/release/retry 为 false。

修复的定向测试 31/31、完整 root 回归 74/74、exact ADK quick 56/56；综合 quick 50/52，整体 FAIL。两项失败为隔离树无 reference 当前现场快照，以及历史 5.0.0-rc.2 的 M5 证据拒绝当前 8.0.6 promotion。真实 source/code 测试通过不能把综合 FAIL 或领域资格重标为 PASS。

自动 [CI38346040381](https://github.com/jiying2007/llm_agent/actions/runs/38346040381) SUCCESS，但 deep 与 signed receipt 被差异图 SKIPPED，不计完整签名资格。因此仅派发一次必要的 [forced CI38346245425](https://github.com/jiying2007/llm_agent/actions/runs/38346245425)，exact main/attempt1/manual/require_adk_integration=true，7 jobs 全部 SUCCESS。生产消费者以固定实际 Cosign/trust 验签通过，payload 强制集成声明 true。独立代理实际复核同一制品及 PR/main/tree/run/event/attempt，真实验签 exit0，Spec/Quality 技术交付 PASS，未关闭 B/M/m 为0。

- 当前 root CI envelope SHA256：`5af9af5d325f750543d2436f6189bfe4463c8eddcb4bfcff612e212e41273e74`。
- 当前 root CI payload SHA256：`25719521b100d449f9986cfde797058a1255d473958657a1355e4113d995c941`。

## 唯一真实 runtime 负结果

[run38343172937](https://github.com/jiying2007/llm_agent/actions/runs/38343172937) 绑定上述前一 main 80f59/attempt1。新的隔离准备和真实 namespace 拒绝测试通过，准确 runner22 启动该唯一任务。声明依赖、固定二进制和公开 trust 准备成功；Collect 以 ADK runtime eval exit1 失败，Sign/Export SKIPPED，artifact0。SDK exit0 不覆盖 workflow failure。runner22 准确注销且 registry 回读为0，独立失败复核确认。

配置请求为 gpt-6.1-sol/medium/单任务；实际上游请求数量、模型身份与具体失败根因未能从已保留证据核验。该旧额度按不可复用处理，无自动重试。后续诊断修复新增真实模型请求为0；不为证明新上传步骤而额外调用模型。新工作流的实际失败摘要上传尚未由另一真实运行证明，也不能恢复旧 run 已丢失的诊断。

## 继续闭环的实际缺项

1. 如需继续真实模型根因取证，须明确新增一次有界请求额度；旧累计最多一次额度不能因 unknown 而重开。
2. 当前 ADK97cf/8.0.6 的真实 independent pilot、实际人类 operator 和同候选 field 证据尚缺，不从 GitHub 登录、聊天授权、使用记录或 AI 执行推断资格。
3. Native/effect 与 G21/G22 的 owner/领域证据仍保持 blocked；历史 policy/scorecard/qualification 不刷新日期冒充当前候选。

待上述证据真实成立后再执行生产认证与 rollover。现阶段只关闭已验证的软件诊断修复和技术 SCM/签名 CI 链，不声明当前 M5、release 或人类资格已通过。
