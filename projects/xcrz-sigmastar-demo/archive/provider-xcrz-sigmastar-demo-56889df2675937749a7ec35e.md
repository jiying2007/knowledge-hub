---
id: provider-xcrz-sigmastar-demo-56889df2675937749a7ec35e
title: v47：当前选择固定半强度候选，主目标尚未完全解决
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-56889df2675937749a7ec35e.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:56889df2675937749a7ec35e558933df93735c015bec1f673016a220350ba0b2
  source_sha256: df4c7b2e11c496da1d696a315b109b00cd0ac8a6a650ca76f770f8a76ed075aa
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-56889df2675937749a7ec35e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-56889df2675937749a7ec35e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 当前选择v46固定native-anchor表系数中点，保留原生AEC/AES/NN及native AGC推进、 连续coherence beta和上一Feed的shadow DTD。它在全部已验证安全候选中收益高于旧v39，
  不声称全局最优、产品资格或设备持续远端自回声已经消除。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 56889df2675937749a7ec35e558933df93735c015bec1f673016a220350ba0b2
---

# v47：当前选择固定半强度候选，主目标尚未完全解决

当前选择v46固定native-anchor表系数中点，保留原生AEC/AES/NN及native AGC推进、
连续coherence beta和上一Feed的shadow DTD。它在全部已验证安全候选中收益高于旧v39，
不声称全局最优、产品资格或设备持续远端自回声已经消除。

v44原完整强度在232例开发集平均残余能量下降8.532057902953209%，保护通过；
首次新24的平均下降9.712024317546918%，但1734双讲变化-0.13807983091313902dB，
超出原-0.1dB保护，明确拒绝晋升。该组后来进入已暴露回归，未继续称未评分。

固定半强度v46不重拟合，不继承v44拟合或声学资格，保持原全部保护。
相同256例/12组全量实际C、精确整数PCM和来源登记完成：
v46平均下降4.939928292330836%，各组4.100841261178623%至5.957312270621305%；
v39平均下降3.9384752811380035%，各组3.3115556708359932%至5.216719193348707%。
v46双讲最差-0.03396474973826713dB、target最差-0.09819482163737359dB，
逐例far最差-0.04289666040136808dB。原双讲/far -0.1、target -0.2和全部削顶/AGC/near保护均通过。
收益以逐clip残余能量比的算术平均计算，未用平均dB代替该比例。
首次登记命令的重复nargs参数只纳入最后24例，已保留该文件且更正参数，
candidate-registry-256-v46.json才是完整256例审计证据，未把首个文件升级为全组通过。

评分前SELECTION-v47冻结两方案和新24 split身份，排除全部256已暴露speaker/clip。
首次新24实际C、精确PCM和来源登记均完成：
v46平均残余能量下降5.316671156513844%，far均值+0.24450488929741dB，
far最差+0.001725934442220023dB，双讲最差-0.029832021557693267dB、target最差-0.05519591249817557dB；
v39下降4.596562733602055%，far均值+0.2122760741591699dB，
far最差-0.007605128957067109dB，双讲最差-0.03608292781599687dB、target最差-0.04504559971152444dB。
两方案全部原保护通过；按冻结规则，v46通过保护且收益更高，选择它为当前优化候选。
该24首次评分后永久按已暴露回归报告；来源官方train partition，NN预训练独立性未知。
本项目表拟合独立性不替代官方挑战资格或设备资格。

v46已在256+24共280例分别验证；没有将两段证据冒充一个重算过的280例登记文件。
原完整每组far均值至少0.5dB门槛仍未达到，complete_solution=false、shipping_approved=false。
约5%的残余能量下降不能解释为回声消失比例或可听明显回声已经解决。

模型SHA395809bb725db9bc91897743b147d470e3833cf3d2094bd85eb5314bb2dda778。
全256登记SHA7120e24b9d03482b30b906edcefa2b62965802ec5a341eec31b5be362220799d；
同256旧登记SHAa7e0ff11c972072f8cf961d73cfd2d5a786980fafbf283feafb531bb5151e6a0。
评分前选择记录SHA8199659049f34bb392c5820244ff364565a36a1d2f3f3283f66e62c3c2c58822。
新24 split SHA47ad78e5490f5e8ec6dd82d6d21c5868ccc6df9eb9a3d3549608bd0471f95880。
Host四目标编译、独立ASAN/UBSAN合同和142项回归通过；非tests原生164项SHA无漂移。

用户已批准累计250000000Token，保持累计129600秒，主目标保持active/open。
未修改产品默认、安装库/app、上层reader/订阅/lease或设备，无commit/push/deploy。
后续仅用现有16份原始录音固定重放，生成可试听输出，不要求新增端侧采集。
设备制品、SSC305实时性能和持续远端听感尚无本阶段新证据。
