---
id: provider-xcrz-sigmastar-demo-d84c0672b9057650a42861f4
title: v41：完整收益拟合未建立可行性，小幅候选通过首次新24例
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d84c0672b9057650a42861f4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:d84c0672b9057650a42861f48759aa2a4e68e94a9f6ebd6b9d27b87a23713e95
  source_sha256: fa007ef609ac840c5b98802d4d262e74ea0794c21799c8ede499117454a49a20
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d84c0672b9057650a42861f4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-d84c0672b9057650a42861f4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 全部184例、9组PCMC38数值映射已通过并合并。 合并统计SHA 2d23dd793b80dbfabffeb112c041f1d0ff2d82def311861032abf1179a286470。 正式映射绑定冻结v37实际C指标、二进制、音频和轨迹；不使用无冻结指标绑定的诊断统计。
  窗口及非输出轨迹相同，最终指标映射误差均低于0.05dB上限。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: d84c0672b9057650a42861f48759aa2a4e68e94a9f6ebd6b9d27b87a23713e95
---

# v41：完整收益拟合未建立可行性，小幅候选通过首次新24例

全部184例、9组PCMC38数值映射已通过并合并。
合并统计SHA 2d23dd793b80dbfabffeb112c041f1d0ff2d82def311861032abf1179a286470。
正式映射绑定冻结v37实际C指标、二进制、音频和轨迹；不使用无冻结指标绑定的诊断统计。
窗口及非输出轨迹相同，最终指标映射误差均低于0.05dB上限。

完整收益拟合从/tmp dry-run成功后固定一次执行。
Phase I九阶段均收敛，最终slack 0.03489378048559832，大于零，
未建立九组0.5025dB收益和固定语音保护的严格可行性。
仅产生tail-coherence-fit-model-v40/feasibility.json，没有model/header。
这是固定几何、固定v37切线及当前约束下的数值结果，不是全部AEC方法的不可行证明。
首次dry-run读到了仍在写入的合并文件而JSON解析失败；等待merge退出0后重跑成功，
该时序错误没有进入声学统计，没有更改模型或保护条件。

随后在评分前写入SELECTION-v41.md，冻结v39模型、3:1强度、二进制和原保护门槛，
首次评分speaker-disjoint-balanced-holdout-v40的新24例。
原实际C和最终整数PCM独立复核均完成；按轨迹重算precision_delta严格匹配precision报告。
新组等权clip平均残余能量降低3.9242695709597157%，平均far增加0.17574654658524005dB。
最差clip能量改善0.32719213933003477%，精确far最差+0.014233071527385732dB；
DT最差-0.047146345729252914dB，target最差-0.0814304636295855dB。
near原指标精确一致，削顶/IFFT/OLA/output gain和native AGC内部饱和未增加。
完整0.5dB mean收益门禁仍FAIL，qualified=false；独立1%研究候选门槛通过。
该24例在本次首次评分前未暴露；之后永久按已暴露回归报告。
官方train partition、NN预训练独立性未知，不是官方挑战或设备资格。

没有生产默认、ARM库、app、上层reader/订阅/lease、设备或发布变更。
持续远端自回声尚未完全解决，不宣称全局最优或听感改善比例。
下一阶段按用户允许的次级目标，单独资格的优化拟合见PLAN-v42.md；
完整验收及所有原语音保护继续独立保留，不能把小幅候选资格写成完整通过。
