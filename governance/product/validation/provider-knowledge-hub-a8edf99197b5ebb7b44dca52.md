---
id: provider-knowledge-hub-a8edf99197b5ebb7b44dca52
title: Provider 候选归档与 Runtime intake 自动化验证
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-a8edf99197b5ebb7b44dca52.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:a8edf99197b5ebb7b44dca5227898d0ca297448a5f3b66afe154d14a54b898c2
  source_sha256: 984df3c531d6eee23b08ea91987a026d0614ffee45f14221d84f6cad3a857922
  temporary_source_retained: false
review_after: '2027-01-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-a8edf99197b5ebb7b44dca52.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-a8edf99197b5ebb7b44dca52.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-05'
updated_at: '2026-10-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-05'
manual_validation_pending: true
summary_zh: 本次根据用户“全面优化落地，自动处理，减少人工干预”的明确要求，实现并启用了本地 candidate-only 自动归档，同时将真实任务 intake 纳入 Agent 日常执行约定。实现与运行资产更新已验证；归档本身的成功仍以
  Provider 回读回执为准。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Provider 候选归档与 Runtime intake 自动化验证
related:
- indexes/obsidian-home.md
---

# Provider 候选归档与 Runtime intake 自动化验证

本次根据用户“全面优化落地，自动处理，减少人工干预”的明确要求，实现并启用了本地 candidate-only 自动归档，同时将真实任务 intake 纳入 Agent 日常执行约定。实现与运行资产更新已验证；归档本身的成功仍以 Provider 回读回执为准。

## 已落地的行为

- Provider 新增 archive 操作，复用 Hub capture 公开包装和事务机制。依照显式 registered project route 自动确定目标、使用 host policy 中已登记 owner；不从 Git、路径或聊天推断主体。
- 允许的低风险结论自动形成 reviewing 候选，同步正文、registry、lifecycle、核心索引与 Obsidian 视图。保留 AI 来源、待复核状态、复核日期和 promotion=none。
- 回执绑定 operation、item、source SHA256 和保存正文 SHA256；首次 ARCHIVED，相同输入回读后 ALREADY_ARCHIVED，重复请求不再写入。正文或镜像字段漂移时阻断。
- 服务端验证类型、路由、owner、文本大小、secret、私有路径/地址和输入元数据边界；不允许输入伪造 lifecycle、人工或 owner 复核字段。
- Runtime 增加 execution-policy ensure，读取真实请求临时文件，结合实际规则文件摘要、任务模式与验收项生成本地 codex-project-routing/v1 intake，并绑定当前准确线程。
- intake 初次登记返回 REGISTERED；同一任务重试幂等，请求/路由冲突不覆盖 active goal。前一个任务终结后，新任务追加到 journal 并保留历史。
- canonical ADK engine、source blobs、策略阈值和管理权限未放宽。未完成目标及缺 evidence/artifact 仍阻断 final。

## 验证证据

| 验证 | 命令或入口 | 结果 |
|---|---|---|
| Hub 全量测试 | Hub 根目录：rtk python3 -m pytest -q | 1296 项，退出 0 |
| Hub 知识门禁 | rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --summary-json | 0 错误，109 个既有 warning |
| Codex 隔离 pre-apply 检查 | rtk bash scripts/check.sh --pre-apply --no-build --offline-hermetic --target <隔离目标> | 329 项测试及四配置 smoke，退出 0 |
| Codex 真实 source-to-live | build(team-collab) → doctor → plan → apply dry-run → Execution Policy apply gate → apply → check | 完整闭环；真实 apply 仅改变 AGENTS 和受管清单两项 |
| Codex 真实 post-apply | rtk bash scripts/check.sh --no-build --offline-hermetic --plan <已应用计划> | 329 项测试，四配置 smoke，退出 0 |
| 真实 Runtime intake | execution-policy ensure，准确当前线程与实际用户请求 | REGISTERED，persisted=true；重复调用识别同一任务 |
| 运行态一致性 | doctor/live、diff、drift 与 source/hash readback | team-collab；errors=0，diff=0，missing=0，changed/stale/unmanaged=0 |
| 负路径 | 秘密文本、非法类型/路由/owner、伪造复核元数据、符号链接、超大输入、空 journal 和非法预算 | 阻断且不产生成功持久化声明；有效但未完成的任务 final 仍退出 3 |

## 设计调整与风险

原 proposal-route 保持 disabled/shadow/report-only；独立 archive policy 只授权候选登记，避免把审查建议误当成写入成功。为遵守工程预算，复用原有 capture wrapper，未增加 Hub shell 命令数量；AGENTS 保持 4500 字节限制，操作细节进入 Codex 文档。

初始 Runtime 默认预算在真实长会话的累计输入计量下不足，apply 前 gate 返回 stop。暂停 apply 后，按实际计量重估任务预算、登记真实 source/plan/dry-run 哈希并再次运行 apply gate，通过后才应用。预算重估不改变 canonical 阈值。后续长任务应在启动时依据上下文量和预计轮数显式估算预算，不能反复盲目使用默认值。

秘密模式扫描不是对所有敏感信息的完备识别；调用者仍必须只传脱敏可复用结论。自动化由 Agent 执行，未安装后台定时任务，未声称 app-server 会自动创建 journal。

## 权限、回退与复用

- 自动登记权限来自本次用户明确要求，执行身份为 Codex；owner 是 host 配置中的责任字段，不是人工审批签名。
- active 提升、owner decision、memory、源项目修改和远端发布继续独立控制。本次无 commit、push、merge、memory 写入。
- 关闭 registry/provider-archive-policy.json 的 enabled 可暂停新归档；已写入内容使用 capture 事务 before/journal 按具体事务恢复，保护无关 dirty 内容。
- 运行资产更新有 apply 备份与 source/build/target 绑定回执；只按两项变化回退，不重置整仓或其它运行数据。
- reusable_pattern: 显式路由与 candidate-only 权限，内容绑定的幂等回执，任务入口先登记并回读。
- promotion_candidate: false；do_not_promote_reason: reviewing 候选和本地 Runtime conformance 不等同于团队 active 或产品放行。
- next_task_friction_reduced: 常规候选保存和摘要计算无需逐项人工确认；reduced_by: Provider archive 与 ensure；reduction_evidence: 已通过首次/重试/冲突测试及真实运行验证。
- owner_review: 尚未进行人工或 owner 复核，保持候选状态。

## 下一步

日常非平凡任务先执行 ensure，完成后自动调用 Provider archive 保存合格结论；高风险类型继续进入审查路径。当前已有的复核日期 warning 与 session-wrap 上游缺 LICENSE warning 单独治理，不能用自动归档关闭这些复核项。
