---
id: pcr02-four-repo-ai-coding-team-knowledge-20260905
title: 四仓 AI 开发资产与团队知识协作候选
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/decisions/four-repo-ai-coding-team-knowledge-20260905.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: session-summary
  from: workspace://xcrz-sigmastar-demo
  source_sha256: 291446cd9ab211188b33e4dd67aa1bdc076c173bc7f31321c7d9fba05ee60402
  temporary_source_retained: false
review_after: '2026-12-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- decision
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/decisions/four-repo-ai-coding-team-knowledge-20260905.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/decisions/four-repo-ai-coding-team-knowledge-20260905.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-05'
updated_at: '2026-09-05'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-09-05'
manual_validation_pending: true
summary_zh: 四个独立模块仓通过自包含规则和技能接入团队知识库，分层验证并保留设备和团队发布边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 四仓 AI 开发资产与团队知识协作候选
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 独立模块 AI 开发资产与团队知识协作候选

- captured_at: 2026-09-05
- status: reviewing
- source: workspace://pcr02-hdi、workspace://pcr02-api、workspace://pcr02-app、workspace://pcr02-sensor 及团队知识库本轮工作树
- validation_boundary: 本地工具、源码规则、隔离 checkout 和技能发现；非 SDK 构建、非 Board/HIL、非团队发布

## 可复用决策

独立模块仓必须拥有自包含 AGENTS、原生技能、源码地图、验证矩阵和薄适配器。
共享能力从团队知识库解析，个人资产和个人 Hub 不能成为成员开工的硬依赖。
仓库 schema 与共享工具版本同时校验；错误团队路径、错误产品根和缺 SDK 返回明确阻塞。

技能使用 .agents/skills；历史技能源可由受管安装器兼容，但不建立同名双份。
安装器 dry-run 不写目标，重复安装幂等；普通文件/目录冲突不能由 force 覆盖。

验证分层为仓内文档与边界检查、对象构建、公开头同步、最终链接、制品身份和设备验证。
实际对象构建之前必须核对公开头镜像，防止旧头被优先包含产生错误成功证据。
ADB 探针除了退出码还需要有效 UUID、uptime、PID 和 MD5，避免错误文本被当成就绪。

## 验证摘要

- 团队候选及实际团队库运行 check-all，69 项测试及文档、链接、命名、Shell 和隐私门禁通过。
- 四仓默认入口检查通过，源码扫描分别为 135、202、54、166 个文件。
- 隔离 checkout、带空格路径、缺依赖负例、安装 dry-run/幂等共 39 项验收通过。
- 本机 Codex 原生 skills/list 发现四个仓内技能，均 enabled 且 errors 为空。
- 独立审查发现两个 P2，修复后双 verdict 通过；17 项共享工具定向测试通过。
- 22 个团队文件通过基线与内容哈希校验应用；已有业务脏改内容保持不变。

## 迁移边界

历史私人测试不能直接作为当前测试：部分 HDI pipeline 文件和 APP JSON、Sensor IR 接口当前不匹配。
将匹配的规则和方法提炼到仓内文档与团队工具，不为通过旧测试改动业务逻辑。
每仓 asset-map 记录吸收、保留与暂缓迁移原因。

## 风险与下一步

没有提交或推送，其他成员尚不能通过远端取得本轮新增内容。
新 runbook 保持 draft，成员真实任务验收和 owner 审阅后再决定成熟度。
未执行真实 SDK 构建、设备访问、部署、HIL 或 image/OTA 发布。
NAS 实体检查因未配置制品根而跳过，只完成元数据门禁。

## Codify Decision

- reusable_pattern: 独立仓入口加团队共享工具与分层验证。
- promotion_candidate: false；已提供团队 draft，当前不自动提升成熟度。
- next_task_friction_reduced: 缺私人目录的新成员仍能开始仓内检查和知识检索。
- reduced_by: 参数化知识路径、原生技能目录、schema 门禁及失败语义。
- reduction_evidence: 39 项隔离验收与四仓原生发现。
- do_not_promote_reason: 团队成员真实环境和 owner 验收待完成。
- owner_review: pending。
- rollback_path: 各独立仓按本轮 AI 文件范围审阅反向补丁；不得触碰既有业务脏改；不涉及用户配置或设备状态。
- verification_evidence: 团队 docs/governance/tests/test_module_ai.py、test_skill_assets.py 和模块 tools/ai.sh。
- memory_action: archive-only；不写个人 memory。
