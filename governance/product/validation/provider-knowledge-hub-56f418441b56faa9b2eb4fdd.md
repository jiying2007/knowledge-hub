---
id: provider-knowledge-hub-56f418441b56faa9b2eb4fdd
title: Knowledge Hub 第八轮检索边界与验收记录
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-56f418441b56faa9b2eb4fdd.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:56f418441b56faa9b2eb4fddce56bbe73641216ab0bbad5190e4710f15c71458
  source_sha256: 6ad35ff030e07a27e6d4684751df530ea34e73775c3b852691df3286286442c4
  temporary_source_retained: false
review_after: '2027-01-06'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-56f418441b56faa9b2eb4fdd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-56f418441b56faa9b2eb4fdd.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-08'
updated_at: '2026-10-08'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-08'
manual_validation_pending: true
summary_zh: 状态：Source验收闭合。本文件记录源码验收结论；Provider持久化及Runtime成功另以实际回执核验。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 第八轮检索边界与验收记录
related:
- indexes/obsidian-home.md
---

# Knowledge Hub 第八轮检索边界与验收记录

状态：Source验收闭合。本文件记录源码验收结论；Provider持久化及Runtime成功另以实际回执核验。

## 范围与目标

本轮维护Hub检索与本地验收工具，实际HEAD为f5d172c7deb59af4e305ce02390978b880354b1c。保留既有dirty overlay。默认策略generation为knowledge-retrieval-implementation-20261008-v5；不将旧generation交互重标为新策略样本。

本轮目标为源码修复及独立验收报告闭合。Provider reviewing归档、活动持久化与Runtime conformance分别核验，不代替Owner审阅、active提升或生产采用。

## 已发生的负结果

独立24例输入首次调用工具被中断，执行状态UNKNOWN。Root在同一输入及冻结源码上获得首次可读恢复测量，实际exit1、quality FAIL：hit0.625、MRR0.65、NDCG0.6113、authority0.5625，零答案正确2/4，P95 661.5ms。阈值未降低、gold未改变；该数据曝光后不再视为未见测试。

病例内容SHA256为07834be37bf5f390dcd1dc6ce0668c2dc861ad2fb883a8a5d879463537bfa3cd。冻结文件SHA256为e1c65d3c69a614caee80e1ccd9b1b585a9421a7f19a3cce9651bd77610f1b28b。实际测量冻结source为c3429a75376dc66e9f6fe8241976c73635bb6ec8914be34f400e3d3320696f08。

后续修复仅针对明确主体与排除列表的硬边界：在自然问句识别之前应用约束，同一有界主体语法贯通正向/否定head和连接列表，保留真实registry身份。修后两条已曝光负例只能作为回归，不回写首次FAIL。

## 待补充的新鲜证据

- signed主体修复及独立复审：PASS，MAJOR-BOUNDARY-1 CLOSED；327作者整批PASS，Python3.8兼容小补丁后121项PASS；非作者12反例+3控制PASS，真实Python3.8.10五种主体形式PASS；最终两已曝光负例零结果、retrieval-result-v3实例PASS。独立review SHA256=f63f294ca0b344325aa051763ffd6a8da312d142144dd194c5ffbe72c9853249，boundary regression SHA256=a78e0a462519bf3a84d2028bb111450ac6dd4c88a09cdea754a83ba7ea896c09。
- 首轮完整engineering：FAIL，11/13检查PASS，pytest失败及full regression失败；coverage report78%。source=c525193d74431699d14f7f562a7490ffe871726b36194c588762657c12fbf594，2017输入，live source/host与快照一致。完整回归130selected、133实际结果、0delegated、2fail；一项明确shared-unit-tests-failed，另一项保存细节不足以认证相同直接根因。首轮报告SHA256=d16d62362fd626440e8269077ad5305778ae149170283a31f3f71df2fd89a2ca。
- 逃逸pipe-holder夹具原先假定Python启动在150ms内输出，实际首轮超时输出为空。新增真实flush后ready握手，生产执行器与150ms deadline不变，输出/超时/incomplete/线程/FD断言保留。独立coverage定向5PASS、RuffPASS，测试增量审查PASS，review SHA256=a23c3760721d003a92014843d2bc7b31eeecf1d99196f162dac98e0e9bf48e19。
- 第二次完整engineering真实exit0/PASS，13/13检查通过；133回归全部实际执行并通过，0delegated，coverage78%，build/依赖审计/SBOM均PASS。QA SHA256=b29dbda8b9c75c0d8fae57213479ad092cbe7510bd6fd0b1d4e8e2862e4aa512。
- 最终被测source SHA256=7fba88220a7d2617720f78f4615f293aabb7029b76508a901732c12e0bf336de，HEAD如上、2017输入、完整dirty overlay，candidate_integrity unchanged=true；live_matches_snapshot=true、live_host_inputs_match=true。本结论认证归档前冻结源码，后续Provider元数据写入另做廉价复核。
- Provider reviewing归档、活动事实持久化、postwrite metadata及当前线程Runtime final在本源码结论之后分别执行。此文不预先声明其成功。

## 保留的验收缺口

- 独立24例首次quality FAIL及P95超限；没有本轮未见数据或生产验证证明整体检索已达标。
- 章节替换的第二相关文档缺少有界、经校验关系索引与companion准入契约，尚未实现。
- 109条Owner准备事项只是路由与元数据准备，没有真实签收或审阅确认。不得更改日期或代签关闭gate。
- 新generation没有足量真实使用样本，不宣称生产性能或采用资格。

## 复用与回滚边界

可复用模式：主体约束早于评分、正负实体语法一致、独立反例同时验证trace与实际返回；评估曝光后保留首次失败。next_task_friction_reduced=true，reduced_by=通用边界矩阵及测试就绪同步，reduction_evidence=独立12反例/两负例关闭及第二次133实际回归PASS。

promotion_candidate=false，owner_review=pending。不写memory、不操作源项目或运行时、不执行本轮Git发布。回滚以精确源码范围与输入身份审阅后生成最小反向补丁，保留他人dirty；不使用reset或清理工作区。
