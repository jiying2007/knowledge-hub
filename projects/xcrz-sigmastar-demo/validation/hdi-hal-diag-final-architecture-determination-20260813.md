---
doc_type: architecture-final-determination
review_id: pcr02-hdi-hal-diag-final-architecture-determination-20260813
reviewed_decision: pcr02-hdi-hal-cross-platform-host-development-architecture-20260813-v4
related_decision: pcr02-diag-observability-maintenance-cross-platform-plane-20260813-v3
supersedes_review: pcr02-hdi-hal-diag-hard-cut-review-20260813
reviewer: Codex
review_date: 2026-08-13
owner_attestation: pending
id: pcr02-hdi-hal-diag-final-architecture-determination-20260813
title: HDI/HAL/Diag 跨平台重构最终方案审查与定案
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-final-architecture-determination-20260813.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: final-design-review
  from: final separated architecture review and determination
  source_sha256: c0be2184b1d9ea1f48d8cb5aded8e0dea9c0fe0f039f16c8942cafce9459e9ee
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- architecture-review
- final-determination
- hard-cut
- zero-residue
- automation
- artifact-lifecycle
validation_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-final-architecture-determination-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/hdi-hal-diag-final-architecture-determination-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 最终审查修复 1 blocker、2 major、1 minor，复审 blocker/major/minor 均为零，确认 v4/v3 为唯一最终设计基线。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- HDI/HAL/Diag 跨平台重构最终方案审查与定案
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI/HAL/Diag 跨平台重构最终方案审查与定案

## 1. 最终结论

PASS。总体方案 v4 与 Diag 规范 v3 共同构成本次重构唯一、完整的最终设计基线，批准进入实现准备，不再保留“后续优化”设计清单。

本结论确认的是设计闭环，不声明源码已重构、SSC305 已回归、SSU9383CM/RDK X5/RTOS 已适配、Host target 已建成、HIL 已通过或产品可发布。Knowledge Hub 仍使用 reviewing 治理状态，等待 team-core、security、product、platform 和 release owner 对各自责任域正式 attestation；该状态不表示仍有未解决架构问题。

## 2. 冻结范围

本次定案冻结以下边界：

1. 依赖方向：APP → API → HDI → internal HAL backend → OSAL/SDK/driver；Diag 是正交平面，lower layer 不反向依赖 runtime。
2. HDI/HAL：HDI 提供稳定领域硬件语义；HAL 是私有平台适配机制；每 target 只链接一个 backend。
3. 平台：SSC305 为首个证明；SSU9383CM、RDK X5 为独立 backend；Linux x86_64 Host 是永久一等 target；RTOS 优先 rtos_control/amp_proxy。
4. 构建：本次只有现有 Make 一份构建权威；未来 GROS 另立项目完成全 target 等价后一次硬切，不长期双轨。
5. Diag：Common 仅有无 OS/JSON/runtime 的 ABI；immutable catalog + fixed provider slot；所有入口过中央 policy；非只读命令只经领域 use case。
6. 制品：一个 binary 只有一个 profile/catalog/target identity；production、service、factory、product_test 是独立签名与生命周期制品。
7. 兼容：源码 ABI、runtime ABI、wire、命令/CLI、工具和 profile 制品硬切；唯一例外是有真实部署证据且位于升级边界的一次性持久化 migrator。
8. 合并：C0–C6、D0–D7 只存在于隔离重构分支；产品分支只接收 C6/D7 完成态，旧目录、符号、shim、alias、fallback 和重复测试同一切换清零。
9. 测试：architecture/generated/Host/product/RTOS 稳定命令和 Presubmit/target integration/release certification 三层门禁长期保留。
10. 发布：target identity、签名策略、设备生命周期、boot/update、anti-rollback、HIL 和 receipt 共同决定某 target 是否可发布。

## 3. 最后一轮发现与闭环

本轮初审确认 1 个 blocker、2 个 major、1 个 minor，全部修复后复审为零。

### F-F01：独立 profile 制品没有闭合设备装载边界

- severity：blocker
- evidence：上一基线只要求 production/service/factory/product_test 为独立受签名制品，没有规定签名策略隔离、设备 lifecycle、普通 OTA、recovery 和 anti-rollback 的关系。
- impact：即使命令 catalog 隔离，量产设备仍可能通过错误签名信任或升级通道装载 factory/product_test，形成制品级维护后门。
- resolution：fixed
- fix：新增 target identity/signing/lifecycle manifest；制造生命周期转量产后不可逆拒绝 factory/product_test；production OTA 禁止换 profile；service 仅允许 nonce/ticket/物理或本地授权约束的临时 recovery 启动，并自动返回 production；Host 证明策略，目标 HIL 证明 secure boot/update/lifecycle/anti-rollback。

### F-F02：跨边界兼容政策没有单一判定表

- severity：major
- evidence：硬切、旧 client 拒绝、持久化 migrator、工具同包升级和制品 identity 分散在不同章节。
- impact：实施者可能只清理源码 shim，却在 wire、CLI、售后工具或 profile 制品中留下隐式兼容路径。
- resolution：fixed
- fix：新增唯一兼容矩阵，覆盖仓内源码、二进制 ABI、wire/schema、持久化数据、CLI/脚本/产测/售后工具与 target/profile 制品；除证据驱动的离线持久化 migrator 外全部硬切。

### F-F03：自动化阈值没有闭合发布门禁语义

- severity：major
- evidence：上一基线已有覆盖率、sanitizer、fuzz、HIL 和 receipt，但没有统一 Presubmit/target integration/release certification 层级，也未明确 infrastructure failure、test quarantine 和证据过期处理。
- impact：测试未执行、设备不可用、过期隔离或旧 receipt 可能被误记为绿色，阈值存在但发布结论不可重复。
- resolution：fixed
- fix：冻结三层阻断门禁；基础设施错误不计通过；固定重试预算；隔离必须有 owner/缺陷/14 天 expiry，关键测试禁止隔离；coverage 同时满足绝对阈值和 changed-line/branch 不回退；release receipt 绑定输入 identity，identity 变化立即失效，证据最大时效由受审查的 target release policy 声明。

### F-F04：认证边界仍有 role contract 表述残留

- severity：minor
- evidence：Diag 非目标仍写 runtime 消费 principal 与 role contract，与“role 仅存在于认证输入、runtime 只消费 immutable permissions/authentication strength”冲突。
- impact：实现者可能在 runtime 重新解释 role，形成第二授权事实源。
- resolution：fixed
- fix：统一为认证 adapter 输出 verified principal、不可变 permission set 和 authentication strength；runtime/provider 不消费外部 role。

## 4. 过渡、兼容和过期资产裁决

以下内容经审查不是目标态兼容实现：

| 内容 | 裁决 | 必须满足的边界 |
|---|---|---|
| C0–C6、D0–D7 | 允许的隔离分支 checkpoint | C6/D7 前不得合入产品分支，目标 binary 无新旧混合态 |
| 整体提交/上一版制品回滚 | 发布恢复机制 | 不在新 binary 中保留旧实现 |
| 维护 operation recovery | 领域事务语义 | 不转发旧 API/命令，不等价于兼容 fallback |
| 持久化离线 migrator | 唯一条件性迁移边界 | 必须有部署证据、floor、dry-run、幂等、断电恢复和自动删除门禁 |
| 未来 GROS 等价验证 | 独立构建切换项目 | 临时对比资产只在隔离工作区，切换后 Make 产品规则与对比资产删除 |
| service 临时启动 | 受控运维路径 | 不是旧版本/profile 兼容；不能替换 production 槽或走普通 OTA |

以下内容在目标仓库和发布制品中必须零残留：compat 目录、wrapper、alias manifest、weak symbol、旧全局注册/调用符号、旧命令运行时映射、feature fallback、双 backend、双 runtime、双 catalog、多 profile binary、ARCH=x86 Host 别名、i386 target、report-only 架构门禁、无 owner/expiry 的隔离测试和超过 supported upgrade floor 的 migrator/fixture。

## 5. 自动化与发布判定

实现完成必须同时满足：

- architecture/generated/Host/product/RTOS 命令存在、blocking、可复跑，无 skip/unsupported 伪通过；
- Diag DG-01 至 DG-22 全部有 identity-bound 证据；
- 规则 pass/fail fixture 100%、策略全矩阵、状态转换覆盖 100%、core Host line ≥ 90%/branch ≥ 85%、adapter line ≥ 80%；
- PR fuzz smoke 与 nightly corpus 均无 crash、hang、OOM、非确定 seed 或 corpus 回退；
- Host Fake 与真机共享 contract/test_id，但 Host 结果不替代 target contract/HIL；
- profile 签名、boot/update、设备生命周期和 anti-rollback 拒绝矩阵通过；
- release receipt 绑定 source、manifest、generator、toolchain、binary、target/profile identity、测试/HIL 与发布包 hash；
- retired-residue 和 stale-asset 检查零违规，cutover inventory 无 unknown/keep-legacy。

任一项未执行、基础设施失败、证据过期或 owner 输入缺失时，对应 target 状态只能是 BLOCKED/UNSUPPORTED，不能是 PASS；它不会触发通用 fallback，也不影响已独立完成 certification 的其他 target。

## 6. 最终复审结果

- blocker：0；
- major：0；
- minor：0；
- compatibility implementation：0；
- runtime fallback：0；
- duplicate SSOT：0；
- ungoverned stale asset：0；
- unresolved future optimization：0；
- owner attestation：pending；
- implementation/certification/release：not started by this design task。

结论：设计可以冻结。实现阶段不得以“兼容现网”“临时过渡”“先 report-only”或“Host 已通过”为理由偏离本基线；确有新事实时必须通过新 ADR 修改基线、给出 owner 和验证影响面，并重新执行受影响门禁。

## 7. 证据与边界

- reviewed sources：`docs/architecture/cross-platform-hdi-hal-host-development-plan.md` v4、`docs/architecture/diag-observability-maintenance-plane.md` v3、上一轮 hard-cut review；
- source evidence：当前公开头、HDI/API/APP/Diag、Make 与 Host/third-party 现状仍用于证明重构必要性，不用于声明实现完成；
- archive policy：总体、Diag 和本定案报告作为新的不可变 reviewing candidates 归档，旧 v3/v2/review 保留为 superseded 历史证据，不覆盖写；
- excluded：产品源码修改、Make source list 修改、Host/交叉构建、实板 HIL、签名基础设施配置、GROS 实现、commit/push/merge。

## 8. 可恢复执行与治理

- goal_statement：对 HDI/HAL/Diag 跨平台硬切换方案完成最终审查、修复、定案和不可变归档。
- completion_claim：最终设计基线与 review 证据完成；不包含实现和 owner attestation。
- claimant：Codex。
- verifier：本轮 final review；正式 owner attestation 待完成。
- retry_budget：同一验证路径最多 2 次。
- evidence_stale_after：24 小时。
- stop_conditions：blocker/major 未清零、三份归档候选任一失败、精确检索无法回读时不得声明定案完成。
