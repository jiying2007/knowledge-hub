---
doc_type: architecture-review
review_id: pcr02-hdi-hal-diag-hard-cut-review-20260813
reviewed_document: docs/architecture/cross-platform-hdi-hal-host-development-plan.md
related_document: docs/architecture/diag-observability-maintenance-plane.md
reviewer: Codex
review_date: 2026-08-13
owner_approval: pending
id: pcr02-hdi-hal-diag-hard-cut-review-20260813
title: HDI/HAL/Diag 硬切换与零残留架构审查记录
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-hard-cut-review-20260813.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: independent hard-cut and zero-residue architecture review
  source_sha256: 0cd488084bd075beec88bab6c01e27a05c274929501dcede49e56f680dfc86ef
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- hdi
- hal
- diag
- hard-cut
- zero-residue
- architecture-review
- automation
- host-test
validation_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-hard-cut-review-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-hard-cut-review-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 专项复审确认并闭环运行时 compat、旧路径 fallback、非阻断门禁、GROS 双轨、Host/i386 冗余、动态 catalog、多 profile binary、ABI 降级、过期资产、自动测试、runtime
  profile 和 role/permission 双重事实共 2 blocker/10 major；最终 blocker/major/minor 均为零。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL/Diag 硬切换与零残留架构审查记录
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI/HAL/Diag 硬切换与零残留架构审查报告

## 1. Review scope

本轮只审查目标设计是否仍包含过渡实现、兼容路径、过期资产、重复事实源、运行时绕行和不可自动验证表述。审查覆盖总体 v3 与 Diag v2，不把代码尚未实现判作设计缺陷，也不把设计 PASS 当作实现通过。

硬约束：

- 当前 Make 保持唯一构建权威，但允许更新显式 source list；
- 产品分支只接受完成态，不发布新旧混合态；
- compat、alias、shim、feature fallback、双 runtime、双 catalog、动态命令注册和多 profile binary 均禁止；
- 旧消费者同切换包迁移，持久数据迁移只能位于升级边界；
- Host 与所有架构门禁是长期资产，不是临时迁移工具；
- 缺失、skip、unsupported 和 report-only 不计通过。

## 2. Verification baseline

静态盘点曾命中：v4 alias/compat 目录、旧全局符号转发、feature 回旧路径、report-only 后转 blocking、GROS 双轨、可选 i386、可删除 sidecar，以及 aliases manifest 长期化。这些命中证明 v2 存在过渡设计，不代表当前代码已经完成目标重构。

## 3. 第一轮发现与修复

共确认 2 个 blocker、10 个 major，全部在目标设计中修复。

### F-H01：运行时 compat 构成第二事实源

- severity：blocker
- evidence：v2 同时设计 compat/v4、aliases_manifest、旧全局符号转发和 P10/D8 延迟删除。
- impact：旧命令/旧 ABI 可长期绕行，catalog、测试和维护成本翻倍。
- resolution：fixed
- fix：目标树删除 compat 与 aliases manifest；旧 id/name 只进入不参与运行时的 tombstone，所有调用方同包切换，旧请求返回 UNSUPPORTED。

### F-H02：分域 feature fallback 使旧实现永久可达

- severity：major
- evidence：v2 多个阶段允许保留旧 adapter、旧视频路径和旧消费者适配器。
- impact：产品 binary 同时拥有两套生命周期、错误和资源所有权模型，边界门禁无法证明唯一性。
- resolution：fixed
- fix：C0–C6 只在隔离重构分支作为 checkpoint；C6 前不得合入，C6 同一提交删除旧目录、符号、调用链、feature 和重复测试；回滚仅整体 revert/上一版制品。

### F-H03：report-only 和 exception budget 允许架构债继续增长

- severity：major
- evidence：v2 允许门禁先 report-only，并给 compat shim 到期例外。
- impact：历史存量可能一直无法清零，新违规仍可能进入主线。
- resolution：fixed
- fix：所有架构规则从硬切换变更第一次 CI 起 blocking；composition root/health adapter 是图中明确边，不是例外；不存在 exception budget。

### F-H04：GROS 双轨会形成长期第二构建权威

- severity：major
- evidence：v2 设计 P9 按平台逐一双轨并允许单平台回旧构建。
- impact：Make/GROS source、define、依赖和 catalog 逐渐漂移。
- resolution：fixed
- fix：当前只维护 Make；未来 GROS 是独立项目，在隔离工作区做全 target 等价，单次切换为唯一权威并删除 Make 产品规则和临时对比资产。

### F-H05：Host sidecar 与可选 i386 造成目标冗余

- severity：major
- evidence：v2 将 Host 描述为可移除 sidecar，并保留 i386 条件性目标可能。
- impact：Host test 容易在迁移后废弃，i386 增加无业务证据的依赖和 ABI 组合。
- resolution：fixed
- fix：host_linux_x86_64 成为永久一等 target；ARCH=x86 退役零命中；不建立 i386 target，32 位只做布局/wire 交叉验证。

### F-H06：动态 catalog/注册增加无必要并发复杂度

- severity：major
- evidence：v2 Linux/Host 允许动态注册，并设计 catalog generation、snapshot epoch、注册/注销竞态。
- impact：命令集合实际由产品 manifest 决定，却承担 RCU/锁/生命周期分支和额外测试矩阵。
- resolution：fixed
- fix：所有 target 使用编译内置 immutable catalog 与 fixed provider slot；运行时只 bind/unbind context，保留必要 invocation lease，不允许新增/删除命令或 slot。

### F-H07：多 profile binary 仍可能把工厂 handler 带入生产制品

- severity：blocker
- evidence：v2 SSC305 target 同时列 production/service/factory，profile 还出现在 request context。
- impact：运行时开关或错误身份可扩大命令面，symbol audit 无法证明生产高风险代码不可达。
- resolution：fixed
- fix：profile 是编译内置 runtime_profile_id；production/service/factory/product_test 是独立 target 和受签名制品，一个 binary 只含一个 catalog，request/transport 不能覆盖。

### F-H08：目标 ABI 的 append-only 兼容继续积累字段与分支

- severity：major
- evidence：v2 Common ABI 采用 append-only、min(size, known_size) 和 transport negotiation。
- impact：实现长期维护多个结构形态和协议降级路径，与硬切换目标冲突。
- resolution：fixed
- fix：当前只接受一个 ABI/schema major 与精确 struct_size；major 变化全仓同一变更迁移，旧 major 明确拒绝，不协商降级。

### F-H09：长期资产没有自动清理过期内容

- severity：major
- evidence：v2 有生成资产和 alias evidence，但没有统一 retired identifier、consumer disposition、stale fixture/migrator 删除门禁。
- impact：过期脚本、fixture、命令 id、旧 target 和迁移器持续残留。
- resolution：fixed
- fix：新增 retired_identifiers、command_tombstones、cutover_inventory、supported_upgrade_floor 与 stale-asset gate；所有旧项必须 migrate/replace/delete，keep-legacy/unknown 为零。

### F-H10：自动测试缺少稳定命令、覆盖阈值和反 skip 规则

- severity：major
- evidence：v2 有测试矩阵，但没有统一 CLI、规则 fixture 覆盖、状态转换覆盖、core branch coverage 和 skip 处理。
- impact：CI 可能只验证一部分或以 unsupported/skip 伪通过。
- resolution：fixed
- fix：定义 architecture/generated/Host/product/RTOS 稳定命令；规则 pass/fail fixture 100%、策略全矩阵、状态转换 100%、core 90% line/85% branch、adapter 80% line、fuzz/receipt 与 no-skip gate。

### F-H11：生成期 profile 与运行时 profile allowlist 重复

- severity：major
- evidence：每个 binary 已按 profile 生成唯一 catalog，但 runtime descriptor/request/pipeline 仍携带 profile 并再次判定 allowlist。
- impact：同一策略存在生成期和运行时两份事实，增加分支、测试和错配可能。
- resolution：fixed
- fix：command manifest 的 build_profiles 只供 generator 过滤；runtime descriptor/request 不含 profile，target identity 绑定 binary/catalog，dispatcher 删除 profile 分支。

### F-H12：role 与 granted permissions 构成双重授权事实

- severity：major
- evidence：request context 同时携带 roles 和 granted_permissions，runtime 可能重新解释 role。
- impact：认证 adapter 与 runtime 可能产生不同权限结论，provider 也可能依赖 role 扩权。
- resolution：fixed
- fix：role 只存在于认证输入和 policy manifest；认证 adapter 一次映射为 immutable granted_permissions 与 authentication_strength，runtime/provider 不消费 role。

## 4. 第二轮复审

### Target uniqueness

- 每个 target 只有一个 backend、OSAL、Diag profile/catalog 和构建 identity。
- production 与 service/factory/product_test 二进制隔离。
- Host 与产品共享 contract/schema/source set，不复制 core。

结果：pass。

### Runtime residue

- compat、alias、旧全局符号转发、旧 handler、动态 command registration 和 runtime profile switch 均从目标态删除。
- tombstone/inventory 只做非运行证据，并有精确 allow-path。
- 持久数据 migrator 位于升级边界，有 floor 驱动的自动删除门禁。

结果：pass。

### Build and automation

- 本次只维护 Make 一份构建权威；GROS 不创建占位或第二依赖表。
- blocking 架构门禁、确定性生成、Host/target contract 命令和 receipt 字段已经明确。
- skip、unsupported、缺失命令和非确定性输出均失败。

结果：pass。

### Rollback semantics

- 代码回滚是完整提交/发布制品回退，不在新 binary 中留双实现。
- operation recovery 是领域事务语义，不等于兼容回退。
- 不可逆动作进入 MANUAL_RECOVERY，不伪造 rollback。

结果：pass。

## 5. False positives 与边界

- “完全不能有迁移工具”：not applicable。已部署持久数据可能必须迁移，但工具只能位于升级边界，必须有真实证据和自动删除 floor，不能进入核心 runtime。
- “version/size 字段本身就是兼容层”：false。目标使用它们防御错误装载，只接受当前 exact major/size，不维护多结构形态。
- “阶段 checkpoint 违反硬切换”：false。checkpoint 只在隔离分支用于执行恢复；产品分支没有阶段性混合态。
- 当前 Make 继续存在不是过渡冗余，它是用户明确约束下的唯一构建权威；未来 GROS 切换另立项目。

## 6. Owner inputs

这些不是可选优化；未确认时对应 target/动作 fail closed：

- team-core：ABI major、target/source-set 和 retired identifier 清单；
- product/security：每个独立 profile target 的 command/policy/catalog；
- platform：SSU9383CM、RDK X5、RTOS identity、limits 和 HIL；
- factory/service：所有外部 consumer 同包切换证明；
- release：supported_upgrade_floor 与持久数据 migrator 删除时点；
- build：未来 GROS 正式规格和独立切换授权。

## 7. Verification evidence

- frontmatter 查询确认总体 v3、Diag v2 为 design-review-passed，本报告为 pass，三者互相关联且 owner approval=pending；
- 精确负向查询确认目标设计不存在 compat/v4、aliases_manifest、运行时 alias、旧符号转发、feature 回旧路径、report-only 过渡、GROS 长期双轨、P10/D8 延迟清理、runtime profile 分支和 allowed_profiles；
- 正向查询确认 C0–C6、D0–D7、DG-01 至 DG-20、retired identifiers、tombstone、cutover inventory、supported upgrade floor、稳定自动化命令、覆盖阈值和反 skip 规则存在；
- runtime redundancy 查询对 allowed_profiles、runtime_profile_id、roles 字段、profile allowlist、snapshot epoch 和动态注册允许项返回零命中；
- profile target 查询确认 SSC305 production/service/factory/product_test 为独立 target/制品；
- 行尾空白查询返回零命中；
- git check-ignore 确认 docs 仍由仓库 .gitignore 第 37 行忽略，因此 Knowledge Hub 候选是耐久副本；
- git status/diff 只显示用户已有源码/构建工作区内容，本轮没有修改产品源码或 Make 规则。

Negative/disproved paths：

- 用户规则引用的 docs/codex-operating-model.md 与 docs/codex-asset-management.md 在当前仓库不存在，未据此伪造规则；本轮使用用户消息中的显式 AGENTS 指令。
- 一次合并 frontmatter 的 apply_patch 因 patch hunk 格式错误被拒绝，没有写入；随后使用合法独立 hunk 完成。
- 一次宽泛 forbidden regex 因 AC-D8 中包含 D8 字符而产生非目标命中；精确目标态查询返回零命中，该宽泛结果未作为残留结论。
- 当前源码确有旧 Diag/APP runtime，证明实现尚未完成；本审查只裁决目标设计，不把“设计无残留”误报为“仓库实现无残留”。

## 8. Re-review result

- blocker：0；
- major：0；
- minor：0；
- owner approval：pending；
- out-of-scope：源码重构、Make source list 修改、实际测试工具实现、Host/交叉构建、HIL 和发布切换。

## 9. Final verdict

PASS。总体 v3 与 Diag v2 已形成硬切换、单实现、零残留和自动验证的唯一目标态，可作为 reviewing candidate 归档。此结论只覆盖设计，不代表实现或平台支持已完成。
