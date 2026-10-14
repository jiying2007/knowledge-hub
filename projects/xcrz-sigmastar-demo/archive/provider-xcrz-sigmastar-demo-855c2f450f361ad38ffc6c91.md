---
id: provider-xcrz-sigmastar-demo-855c2f450f361ad38ffc6c91
title: v27：固定双讲保护新几何未达到远端收益
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-855c2f450f361ad38ffc6c91.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:855c2f450f361ad38ffc6c91bad1cff578a8984ae1e5a5b28752ecb02564f518
  source_sha256: 555c8b97641b8f7b660ce9dc777e19cf7bf1dd1d311cdc744268292d57c5ea93
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-855c2f450f361ad38ffc6c91.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-855c2f450f361ad38ffc6c91.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 主声学目标仍open，shipping_approved:false，无最优/完成声明。 七组同136开发数据272次原生/控制运行的原始评分与冻结v26-observed完全一致。 全部guard映射通过，最差评分映射误差0.0004333599965633539dB(原门槛0.05)。
  新统计SHA53989f43418cd7b2dd6c584a2a4ee3a5b44c8eaea706913a0fee0e1fcd4fd391。 固定guard/NN特征/原生AGC/.01prior/.08保护/.0025far数值余量/实际质量门槛。
  九阶段Newton收敛，但预测far mean0.29
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 855c2f450f361ad38ffc6c91bad1cff578a8984ae1e5a5b28752ecb02564f518
---

# v27：固定双讲保护新几何未达到远端收益

主声学目标仍open，shipping_approved:false，无最优/完成声明。
七组同136开发数据272次原生/控制运行的原始评分与冻结v26-observed完全一致。
全部guard映射通过，最差评分映射误差0.0004333599965633539dB(原门槛0.05)。
新统计SHA53989f43418cd7b2dd6c584a2a4ee3a5b44c8eaea706913a0fee0e1fcd4fd391。
固定guard/NN特征/原生AGC/.01prior/.08保护/.0025far数值余量/实际质量门槛。
九阶段Newton收敛，但预测far mean0.291887882/min-0.097495747dB，资格false，未生成候选header。
模型SHA917c59cf100ba75a5e2ff19d960990d50a647d04cdf6c0be8d4ccab1949a6eb4。
没有把此不合格表用于实际C或新独立集评分。新1996独立24例仍未评分。

首次计算在JSON导出时因资格false为numpy.bool_失败；bool转换修复仅影响序列化，
相同统计/参数重算一次并保留失败说明，没有修改门槛或反馈调参。
负资格JSON控制已通过(22项局部测试1.052s)，train源码更新为
af35fed478bf661f111e60630a04653aa7bad21661a488887e8c055b8df2b351。
修复前完整96 Python tests通过8.462s；新增C上一Feed shadow快照/允许帧时序
ASan/UBSan检查通过，原无ref/VOICE/Reset/FIFO/AGC检查仍通过。
contract C85c109851c4284080ddd156a8d991bfd479ce2e701e6d98d922618e2782aae21；
setup binaryf88a41199de32cb5045e646aa9dcc4e8b62077bcbfc42256e3669634c0a4dee5。
无生产默认、库或上层业务改动，无ARM/设备听感证据。

当前保护约束是固定原生alpha处残差界加目标内积不下降，它比实际SI/target门槛更强。
下一轮评估直接SI正投影锥约束，保留SI训练余量.08及实际-.1门槛，
target训练-.1975保留.0025余量，实际-.2门槛不变；不保证可达到far收益。
