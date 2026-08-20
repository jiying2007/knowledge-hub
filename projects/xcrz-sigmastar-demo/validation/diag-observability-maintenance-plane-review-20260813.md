---
doc_type: architecture-security-review
review_id: pcr02-diag-observability-maintenance-plane-review-20260813
reviewed_document: docs/architecture/diag-observability-maintenance-plane.md
related_document: docs/architecture/cross-platform-hdi-hal-host-development-plan.md
reviewer: Codex
review_date: 2026-08-13
owner_approval: pending
id: pcr02-diag-observability-maintenance-plane-review-20260813
title: Diag、Observability 与 Maintenance 平面架构审查记录
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/diag-observability-maintenance-plane-review-20260813.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: design-review
  from: separated architecture and security review with repository static evidence
  source_sha256: 71a550f317ce327074087c7f8440763fd7357ba6f5147e251aaebdc4e22f46d7
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- diag
- observability
- maintenance
- architecture-review
- security-review
- host-test
- rtos
validation_refs:
- projects/xcrz-sigmastar-demo/validation/diag-observability-maintenance-plane-review-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/diag-observability-maintenance-plane-review-20260813.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 独立安全与架构审查确认并闭环 provider 生命周期、高风险审计时序、HDI self-test 越界、权限模型、维护恢复与长期资产 SSOT 问题；最终 blocker/major/minor 均为零。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Diag、Observability 与 Maintenance 平面架构审查记录
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# Diag、Observability 与 Maintenance 平面架构审查报告

## 1. 审查结论

裁决：PASS，可作为 Knowledge Hub 的 reviewing decision candidate 长期归档，并作为总体 HDI/HAL 跨平台方案的强制组成部分。

最终分级：

- blocker：0；
- major：0；
- minor：0；
- owner approval：pending；
- out-of-scope：代码重构、构建调整、Host 测试、交叉编译与 HIL。

PASS 只证明设计边界、迁移、验收和治理可以指导实现；不代表当前 Diag 已具备权限隔离，也不代表任何新平台、Host 或 RTOS 功能已实现。

## 2. Requirement baseline

- Diag 不能整体塞入 Common、HDI、API 或 APP 单层。
- 当前 include/common/diag 的 runtime/JSON 混合必须在目标架构中解决。
- 权限、生命周期、RTOS/Host、资源预算和兼容移除不能留作无验收的后续优化。
- 当前编译规则不变。
- 设计必须形成可独立维护、可机械验证、可归档的长期资产。

## 3. Verification baseline

静态证据确认：

- diag_types.h 包含 4096 字节 JSON reply、layer enum 和 JSON handler。
- diag_provider.h/diag_contract.h 声明的 register/invoke 由 modules/app 实现。
- dispatcher 找到 handler 后直接调用；未发现 effect/permission/deadline/audit 中央门禁。
- registry 返回裸 handler，使用 atomic_flag busy spin。
- cmd node 动态申请 32 KiB result buffer。
- provider 含 volume/gain/start/stop/format/SN/motor/OTA 等非只读动作。

证据只支持设计问题存在，不证明当前入口可被外部利用。

## 4. 第一轮发现、修复与真实性核验

### F-D01：provider lease 顺序存在竞态描述

- severity：major
- evidence：初稿 policy pipeline 在 provider lease 之前执行可能访问 provider/device state 的步骤，而 lifecycle 又要求 drain 安全。
- impact：实现者可能在 provider 正在 DRAINING 时使用 context，或为未授权请求长时间持有 active lease。
- authenticity：confirmed，属于设计内部不一致。
- required action：区分 immutable catalog snapshot 与 invocation lease。
- resolution：fixed。
- verification：最终 pipeline 先做 admission/catalog/profile/permission/capability，再原子获取 READY generation lease；provider-owned guard/handler 只在 lease 内执行，snapshot epoch 与 lease 均清零后才能 cleanup。

### F-D02：高风险 audit 只有执行后语义

- severity：major
- evidence：初稿只写 handler 后 audit；format/OTA/reboot 等成功后 audit 失败无法回滚。
- impact：高风险副作用可能发生但没有可恢复记录。
- authenticity：confirmed。
- required action：增加 pre-intent durable audit、completion audit 和失败收敛。
- resolution：fixed。
- verification：最终规范要求副作用前 intent 持久化/预留；completion audit 失败不伪造 rollback，runtime 阻断后续高风险动作并进入恢复状态。

### F-D03：HDI self-test 直接访问边界前后冲突

- severity：major
- evidence：初稿同时写“非只读必须经 maintenance use case”和“hdi adapter 可调用 self-test port”。
- impact：self-test 可以改变资源和运行态，形成 direct HDI 后门。
- authenticity：confirmed。
- required action：HDI adapter 只保留 observe；self-test/maintenance 经领域 use case。
- resolution：fixed。
- verification：目标图、各层职责、D4 与总体方案均已对齐。

### F-D04：required_role 不能表达最小权限

- severity：major
- evidence：单一 role 隐含层级，难以表达售后可读但不可 format、update agent 可升级但不可 motor 等组合。
- impact：权限过宽或 provider 自行解释 role。
- authenticity：confirmed。
- required action：角色与 permission 解耦。
- resolution：fixed。
- verification：principal 携带 roles/granted_permissions，policy manifest 显式映射，descriptor 使用 required_permissions；不存在隐式 role 大小关系。

### F-D05：维护恢复与 Diag 故障隔离缺口

- severity：major
- evidence：初稿有 idempotency/confirmation，但未定义回复丢失、重启、不可逆操作、audit backlog 和 Diag 过载时的收敛。
- impact：重复副作用、错误声称 rollback，或诊断线程拖垮关键业务。
- authenticity：confirmed。
- required action：operation journal/recovery state 与 bounded failure containment。
- resolution：fixed。
- verification：新增 recovery_policy、operation 状态、precondition/idempotency、MANUAL_RECOVERY、重启恢复、队列/线程/内存/优先级和 high-water mark 门禁。

## 5. 长期资产审查

发现：初稿虽声明 manifest SSOT，但目标布局仍使用手写 C manifest，容易形成文档、C 表和测试三份事实。

- severity：minor
- resolution：fixed
- final design：
  - command/policy/limits/aliases 使用 versioned JSON source manifests；
  - command_id 显式分配、唯一、永久不复用；
  - C catalog、文档和 golden vectors 为禁止手改的生成物；
  - 生成物携带 source hash；
  - production policy/catalog/limits 编译内置或经 trust service 验证；
  - profile/catalog diff 是审查门禁。

## 6. 第二轮复审

### Architecture

- Common、runtime、adapters、domain use cases 和 backend 依赖方向单向。
- Diag 是正交平面，不反向污染 HDI/API/OSAL/backend。
- Observability、self-test 和 maintenance 语义分离。

结果：pass。

### Security

- principal、role、permission、profile、effect 和 capability/state 各有独立职责。
- 高风险动作具备 confirmation、intent audit、idempotency、recovery 和安全 guard。
- IPC/local/inproc 不再被默认视为可信。
- production 高风险 handler 默认不注册并要求 symbol/catalog audit。

结果：pass。

### Concurrency and lifecycle

- catalog snapshot、provider lease、generation、drain、cancel 和 cleanup 边界完整。
- registry lock 内禁止 handler。
- timeout、不可取消操作和迟到结果有明确语义。

结果：pass。

### Portability

- JSON 从 Common 移到 Linux codec。
- RTOS 使用 static catalog、bounded writer、fixed limits 和 TLV/CBOR/proxy。
- x86_64 Host 可覆盖 policy、codec、lifecycle、fuzz、resource 和 recovery。

结果：pass。

### Maintainability

- D0–D8 与总体 P0–P10 强制映射。
- DG-01 至 DG-18 可执行。
- manifest/generated/evidence 权威边界清楚。
- v4 有 alias、deprecation、remove_after、consumer evidence 和 rollback。

结果：pass。

## 7. Owner approval inputs

这些不是设计优化欠项；未获批准时默认 fail closed：

- security owner：principal trust adapter、permission mapping、confirmation 和 durable audit/journal 实现；
- product owner：production/service/factory/product_test catalog；
- platform owner：target limits、capability identity、RTOS durable sink 和 HIL；
- factory/service owner：v4 消费者、维护流程和 remove_after；
- build owner：Make sidecar 与未来 GROS source set。

## 8. False positives 与 out-of-scope

- “所有 Diag 都应放 APP”：not applicable。仅 transport/auth/composition 属于 APP，公共 contract/runtime 不能由 APP 垄断。
- “只要命令名叫 diag 就可直达 HDI”：false。代码已有非只读命令，名称不是安全边界。
- “当前已存在外部未授权漏洞”：not proven。静态证据只确认 dispatcher 内无中央门禁，入口信任链未做完整动态验证。
- 本轮不修改源码、Make、lib.mk、运行配置或产品命令。

## 9. Re-review result

- F-D01：fixed；
- F-D02：fixed；
- F-D03：fixed；
- F-D04：fixed；
- F-D05：fixed；
- minor asset SSOT：fixed；
- 新增 blocker/major：0。

## 10. Completion evidence

- 四份架构资产 frontmatter 均已检查：两份设计为 design-review-passed，两份审查为 pass，owner_approval 仍为 pending。
- 目标设计直接查询确认 P0–P10、D0–D8、DG-01 至 DG-18、AC-I12 与 AC-D10 均存在。
- 仅对两份目标设计查询旧 required_role、P0–P8/P0–P9 和 DG-01 至 DG-16，结果为空；审查报告保留这些词仅用于说明已修复历史问题。
- 四份文件行尾空白查询为空。
- 直接查询确认 immutable catalog snapshot、invocation lease、durable intent、required_permissions、MANUAL_RECOVERY、static catalog、bounded writer、source hash 和 fail closed 均进入规范正文。
- git check-ignore 确认仓库 .gitignore 第 37 行忽略 docs；因此本地文档不是可提交事实源，Knowledge Hub reviewing candidate 是耐久副本。
- git status 与 git diff --stat 仅显示进入本轮前已有的 pcr02/dep.mk 修改和未跟踪目录；本轮未修改源码、构建规则或用户已有工作区内容。

Negative/disproved paths：

- 一次包含 Markdown 反引号的批量 apply_patch 在参数解析阶段失败，没有写入文件；随后拆分为无歧义的小补丁并逐段复读。
- 一次基于不存在上下文 required_role 的宽补丁未匹配，没有写入文件；随后按实际 required_permissions 上下文修订。
- “当前已存在外部未授权漏洞”未被证据证明，未进入结论；只保留“已检查 dispatcher 路径不存在中央策略门禁”的静态事实。
- “i386 可兼容”未被证明，目标仍只承诺 Linux x86_64 Host；i386 仅在有明确业务需求和依赖证据后另行评估。

## 11. Final verdict

PASS。规范可按 status=reviewing、owner_approval=pending 归档。只有 DG-01 至 DG-18 和对应平台证据完成后，才能对实现使用“支持、通过、可发布”等结论。
