---
id: provider-knowledge-hub-c7c483680173c6870d96c7a1
title: Knowledge Hub 第三轮优化验收记录
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-c7c483680173c6870d96c7a1.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:c7c483680173c6870d96c7a1b7519ba5f78d7ac0b83265bd8518ab055b6d3a23
  source_sha256: dd4318a6a54c7ad7925427f605250bbd1bc6c0ded31bd9baa9357bd31334b4f6
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
- governance/product/validation/provider-knowledge-hub-c7c483680173c6870d96c7a1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-c7c483680173c6870d96c7a1.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 日期：2026-10-06。范围为第三轮只读审查提出的八组建议，仅维护 Hub 工具、测试和契约文档。保留既有工作区改动，未替代 owner review、active promotion 或生产资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 第三轮优化验收记录
related:
- indexes/obsidian-home.md
---

# Knowledge Hub 第三轮优化验收记录

日期：2026-10-06。范围为第三轮只读审查提出的八组建议，仅维护 Hub 工具、测试和契约文档。保留既有工作区改动，未替代 owner review、active promotion 或生产资格。

## 实现结果

- 修复真实 CI transport 的环境传递；增加低成本 contract/schema/transport 预检，完整失败摘要保留退出码与 predicates，确定性失败不自动重试。
- 活动事实先解析完整修订链，再按报告日期投影；缺前驱高版本标记 lineage-unknown。
- Provider 操作日志执行合法转换、重复阶段幂等和终态保护，unknown 不盲重试。
- 制品目录公平扫描不同类别，优先受控 Provider 操作；摘要暴露预算溢出、分类计数和扫描完整性。新增类别只报告，不自动删除。
- 工程快照使用独立 Git 对象；失败副本私有保留，绑定源码、host 输入和路由；回放验证逐文件身份并使用临时私有副本，保留目录不留 host 正文。
- 审查消费增加有界 metadata-only 事件及期间指标；修复旧事件重试覆盖新决定和不确定写入误报；pending outbox 支持恢复，不自动 owner approval。
- 检索诊断区分候选召回、authority、评分、返回窗口和 top-k。开发与独立冻结评估分离，未调整默认排序或既有 gold。
- 源码 QA、Provider 候选元数据和 Runtime conformance 分列；工程辅助结果逻辑按模块职责拆分，保留接口及原门禁阈值。

## 身份和验证

基线 HEAD：f5d172c7deb59af4e305ce02390978b880354b1c。
冻结源码签名：79e721f6acfe4c21a9a83edbf5f9225209ccaeb23b804915f6351e1c73cd8e47。
独立代码复审：pass-with-limits，无 open major；最新模块拆分独立 53 tests 通过。
完整工程：13/13 checks PASS，errors=0；父测试 exit0、158.928秒；full regression 133/133 PASS、482.508秒；包级覆盖率77%，原阈值75%。全部检查 attempt=1，无自动重试；源码、live、snapshot 前后签名一致，host identity match=true。
工程报告 SHA256：cc014504dd5b9aad22889c5a8f13f1680786b2cbfdffc443de5ef1a001bb7fa4。
快照 manifest SHA256：7c5b3db88d67daef2cf5e1f841e03cea1780c41b75ae9c24d35a017a97c0c8a2。
SBOM SHA256：282fcc4ffaf038160a4d91d2793aa7e9a26ebf7deab94878a76b1fd64db741cf。

独立冻结检索：10例，hit=.9、MRR=.875、NDCG=.875、authority recall=.875；quality-gate FAIL/exit1，shadow也FAIL。失败为 independent-llm-readiness，安全完整性PASS，源码前后 unchanged=true。未改变规则或gold以追求通过；此负结果是检索效果的真实限制，不否定协议反例和工程检查通过。
独立数据集 SHA256：c81377808ccea104c4ffcf0766949c22cbd51cdaa7553289ec584cac07feec77；cases SHA256：97c4e89e6b7bbefaaf9b92541cb1ea47666a3119b01bec1ceb9ae4549fc4efa6。

## 限制

开发检索样本 12 例 hit=.9167，质量门禁仍未通过；不能据诊断实现声明效果达标。独立样本由另一审查者仅根据 curated registry 和 README 冻结，不作为调优材料。
本记录不代表真实生产采用、人工 owner 批准、团队 active 发布或远端 Git 发布。失败快照与新制品分类继续 report-only。
协议改进已完成本轮验收；检索效果仍需独立后续开发实验及新冻结集验证，不能宣称全部质量门禁通过。
