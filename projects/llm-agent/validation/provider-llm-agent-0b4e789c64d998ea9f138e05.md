---
aliases:
- 使用记录驱动的M5试点候选筛选与采集边界
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
id: provider-llm-agent-0b4e789c64d998ea9f138e05
title: 使用记录驱动的M5试点候选筛选与采集边界
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-0b4e789c64d998ea9f138e05.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:0b4e789c64d998ea9f138e0595f5e2db866ae4ec8eed37f1d536778ee513520e
  source_sha256: 721ef2c53902fa8af5d794b07b04e88477674579bbe57a1aa75d8eb5569a3063
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/llm-agent/validation/provider-llm-agent-0b4e789c64d998ea9f138e05.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-0b4e789c64d998ea9f138e05.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 日期：2026-10-10。状态：reviewing candidate，资格 NEEDS_REVIEW。范围：llm-agent 当前 M5 候选输入准备；不修改被观察项目或 Provider registry。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: llm-agent
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 0b4e789c64d998ea9f138e0595f5e2db866ae4ec8eed37f1d536778ee513520e
---

# 根据使用记录筛选当前候选试点的审查提案

日期：2026-10-10。状态：reviewing candidate，资格 NEEDS_REVIEW。范围：llm-agent 当前 M5 候选输入准备；不修改被观察项目或 Provider registry。

## 已验证的观察

对 2026-10-07 至 2026-10-10 更新的 15 个主会话有界筛选；只读会话索引和首条 session_meta，不复制提示词、会话正文、认证、模型正文或 raw 日志。使用频次用于候选排序，不证明实际 ADK 执行或人类身份。

优先观察候选 GROS：2 个主会话，跨 2 个更新日期，独立 Git root，观察时源码提交 2205fe6fd210eaef4447edc6a8cc33d284f60a0b。备选 A123X sdk_demo：2 个主会话，1 个更新日期，独立 Git root，观察时提交 6e4d7f45b77e893769dc2965ea375129bd777941。HEAD 只是观察时仓库身份，不证明历史会话执行过同一源码；未确认完整 dirty、嵌套锁和制品身份。

Provider 的两次 GROS 查询分别返回 ambiguous 和 unresolved，A123X 查询 unresolved。GROS 的搜索结果存在 reviewing 工程记录，但搜索命中不是 cwd route 解析，更不是当前候选 field。路由仍需 Provider 治理入口处理，不能从目录或文档路径推断项目归属和主体。

llm-agent 当前候选 ADK 为 8.0.5 / ef5384305421700ca01e89b3df3b3f7878a70265。最终 main 为 48059590c52178c309003600773770b580f4d549，run 38038590082 成功；main 签名回执已用固定实体 Cosign 独立验证。现有历史 field 使用不同 ADK identity，不重标。完整 M5 资格仍未通过。

## 拟采用的采集契约

先由 Provider 解析或治理登记候选项目路由，再核验完整 repository/source lock 和采集入口。真实使用开始时必须捕获 exact ADK execution identity、当前试点 repo/pin/path、显式 human operator、事件时间及证据摘要，并关联实际任务结果和失败记录。候选项目不是 Root 的 reference pin，不自动改 Root registry 或搬入工作区。

仅在同一 hash-bound 真实证据满足现有消费者合同后，才计入当前候选 field。owner review 单独由人类记录；模型请求配置不替代受信 observed model。工程构建、主会话标题、使用次数、软件测试和 main CI 不替代 field/owner/runtime。

若现有消费者合同需要支持 workspace-external pilot，应先审查新的受管身份契约、路径安全、fixture 隔离、候选/source freshness 和回归，再实现；不通过将本机路径塞入 reference pin 或放宽历史校验规避门禁。

## 当前裁决和后续动作

候选发现完成，可消费 field 资格候选为 0。路由、执行身份、真实人类事件及 owner review 缺项保持 NEEDS_REVIEW。本提案允许后续执行准备和只读验证，不是 pilot_started、生产资格或 owner 批准。尚未执行新增模型调用、板端/设备操作或后台任务。

下一步：Provider 路由治理；受管 workspace-external pilot 身份契约审查；显式人类主体与新鲜真实事件采集。当前没有足够证据自动启动正式试点或关闭 M5。
