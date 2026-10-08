---
id: provider-llm-agent-25d0ff0e4fc8c26e5698cdb2
title: 合并与受管应用检查点（外部 CI 阻塞交接）
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-25d0ff0e4fc8c26e5698cdb2.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:25d0ff0e4fc8c26e5698cdb21925d1c275747bfba8ddb79d543eb0278f81a245
  source_sha256: 94ffdc7a24192dc22cd1296e123c6200025779d541cf6a16c465da3be055e42b
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
- projects/llm-agent/validation/provider-llm-agent-25d0ff0e4fc8c26e5698cdb2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-25d0ff0e4fc8c26e5698cdb2.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: '状态：in-progress / reviewing。用户已授权合并此前 ADK #173 和依赖修正后的 llm_agent #181，并继续原已授权的提交推送与受管应用。源身份、签名 promotion、产品资格和
  live 校验分别验收；不调用真实模型。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 合并与受管应用检查点（外部 CI 阻塞交接）
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 合并与受管应用检查点（外部 CI 阻塞交接）

状态：in-progress / reviewing。用户已授权合并此前 ADK #173 和依赖修正后的 llm_agent #181，并继续原已授权的提交推送与受管应用。源身份、签名 promotion、产品资格和 live 校验分别验收；不调用真实模型。

## 当前检查点（本节优先）

- ADK #173 已合并且原主工作区 main clean；实际 HEAD=3bb4ce3356f6b2b13f3f6f72a3f4816af6e9b737。root #181 仍 OPEN/BLOCKED，head=25ff781bbc2d3d7d026a3e2fc66e7a2e7c7a3395；未执行 root merge。
- 主线 CI 37365201897 attempt 1 和 attempt 2 均结束失败：GitHub hosted runner 无法分配，相关 check annotation 为 The job was not acquired by Runner of type hosted even after multiple attempts。第二次已通过三版本完整回归及 Python 3.8/3.12 contract；剩余 deterministic-eval-package、static-security、contract-py3.11 被取消，promotion-evidence 被跳过。CodeQL run 37365202078 两次同类 runner 失败。
- GitHub 官方状态 API https://www.githubstatus.com/api/v2/summary.json 报告 Actions degraded_performance / runner assignment delays，incident=3q1yb5m7ltvb。仅作已查询时的外部诊断，不将其推导为所有后续失败的原因。
- 已执行一次失败 job 重试；停止无新信息的连续重试，等待服务恢复或可实际分配 runner 的新证据。没有绕过必需 job、伪造签名、改 CI source identity 或手动发布。
- 尚无绑定新 main 的 promotion evidence/attestation/artifact digest，故 root promotion apply、Codex exact-source import、root/Codex merge 和 managed live apply 均未执行。Codex worktree 的 baseline edits 只是未验证的升级草稿，不能拿旧 artifact digest 构造新 release 身份。
- 原 ~/codex 五个 tracked dirty 文件及 untracked execution_policy_journal.py 的 SHA256 与升级前完全一致；原参考仓未清理。managed live source/profile 仍为原 ~/codex / team-collab，未应用新来源。
- Codex repeat-import 修复：12 新增 + 28 既有 audit tests 在 Python 3.8 和 3.11 各 40/40 PASS，独立 whole-diff spec/quality PASS；三个文件 fingerprint=daf674fe1f1e4e2e96273be63e773cbd5ce30ef8a8142fa698b0d9461c1136c1。候选未提交、未导入真实新资产。
- 下一轮 ADK 候选已转到真实 main 的等树基线，branch=codex/next-strict-version-main-20261006：strict version preflight、Git worktree file modes 修复及 fixture symlink/hook 隔离均实现。完整 host 97/97 PASS；最后仅测试 fixture 添加 hooksPath=/dev/null，之后定向 test_file_modes 与独立复审 PASS。full 回执未重标成最终微调字节快照。最终独立 diff snapshot=0b04c2e53b42a2ef097e4fcb2178eb8ace1d278729f6d26e41a1c1298185df34；仍未提交或应用。

## 恢复入口（无需重复合并/应用授权）

1. 复查官方 runner 状态、main=3bb4ce 和 37365201897/37365202078 当前 attempt；条件恢复后只重试失败 job。成功后下载 adk-promotion-evidence-3bb4ce3356f6b2b13f3f6f72a3f4816af6e9b737，验证 main/commit/tree/manifest、官方 issuer/workflow 身份、真实 artifact SHA 和 immutable release；不能使用本地未签 candidate 替代。
2. 从 root .worktrees/llm-promotion-20261006 运行已存在的 promotion tool dry-run 与 source apply 事务（当前除 child gitlink 外 clean），再补本交接文档、定向身份/证据回归并更新 #181。Codex worktree=.worktrees/codex-adk-7.14.0-20261006；先更新实际 artifact SHA，再运行已修 importer 的签名 plan/apply，生成 exact fixture、退休旧受管 Agent 目录，完成整体 consumer review/tests/build/doctor。按真正完成的源码实现阶段裁决 commit gate；不要提前关闭含后续 merge/apply 的整个交付目标。
3. 必需检查通过后按已授权范围合并并同步原 ~/codex，保护和核验现存 dirty；保持 team-collab。冻结 source/build/target，执行 plan/dry-run、真实 apply 和 check，使用真实回执收口。当前 Execution Policy task-5171bae2b926e23475a14b1b 保持 active，criterion=source-to-live-prepared，open_items=6；不能把尚缺签名和应用标 complete。

## 目标与边界

1. 核验并合并 ADK #173，保留原分支与本地有效修改。
2. 获取绑定实际 main SHA 的 hosted promotion，验证官方发布者身份与内容摘要；用既有 promotion 事务更新根仓 gitlink/lock/interface/status/evidence/attestation，复跑 #181 后合并。
3. 在 canonical Codex 独立 worktree 做 exact-source 导入与消费身份基线更新，修复重复导入阻塞，独立审查、回归及 PR 合并。原 ~/codex dirty 不进入本轮提交。
4. 保持实际 live 的 team-collab profile，执行 build、doctor、plan、apply dry-run、apply、check，保存 source/build/target 与回滚身份。

验收：两个项目 PR 的最终 main refs、真实签名与制品、Codex exact source audit/consumer gates、完整 source-to-live 回执、原 dirty 保留证据。没有匹配证据时保持待验证，不改旧签名、owner、日期或产品资格。

## 已验证事实

- ADK #173 已合并：main=3bb4ce3356f6b2b13f3f6f72a3f4816af6e9b737，tree=2adf96c5a41018846cb1303117e676f17351ac46，manifest blob=538995c328009f640ee9208e7a4d57249dbe106e，source candidate=7.14.0。
- squash 前 b668712 与 main tree equality 已验证。原本地 main 的 a6a1367 历史保存为 codex/pre-squash-main-20261006；原交付分支和下一轮隔离候选保留。
- 三版本 full local parity：每版本 97/97、routing 30/30、wheel/audit PASS；receipt=/tmp/adk-delivery-b668-parity.json，sha256=7947969afcd022831f1004598d231b43ee57c4ae627be03784e76ca6398109b0。它是源码矩阵证据，不是 main promotion 或 live 证据。
- 根仓先前冻结 full 72/72 PASS；#181 原 integration-deep 失败明确为 promotion evidence source.version 与新 lock 不匹配，未忽略此失败。
- 主线 CI run=37365201897；当前等待实际 signed promotion，不能沿用 b668 的组件 archive hash。
- official cosign v3.1.3 仅下载到 /tmp；binary SHA256=4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71，与官方 release API digest 和 checksums 一致。使用已审核 exact trusted root SHA256=6494e21ea73fa7ee769f85f57d5a3e6a08725eae1e38c755fc3517c9e6bc0b66。
- Codex source audit：42 Skill tree、9 Agent blob、四 policy blob 均与现有消费内容一致，无 source/distribution gap。仅更新真实来源与消费身份，不推导新的模型收益。

## 风险与恢复

- Root promotion 工具要求隔离且 clean 的输入；原根仓 untracked reference 不清理，事务在 .worktrees/llm-promotion-20261006 实施。
- Codex importer 的旧 README 固定 pin 导致重复导入末段失败，先修复并测试、再实施导入。
- ~/codex 既有 dirty snapshot=/tmp/codex-user-dirty-before-upgrade-20261006.patch，包含当前全部 tracked diff；untracked journal 另行保留。若同步发生冲突，保留两侧并定向解决，不 reset 或覆盖用户修改。
- 回滚锚点：交付提交、原 main 备份分支、保留的 worktree、apply plan backup。没有用户请求，不删除这些恢复资源。
- retry_budget=2；同一失败第三次前 replan。heartbeat 更新为阶段实际证据时间；staleness_threshold=源码/目标/签名身份变化立即复验。
- merge/promotion readiness 与 runtime apply preparation 分阶段登记 Execution Policy，terminal conformance 不推导产品资格。长期结论只经 Provider 保存 reviewing candidate。
