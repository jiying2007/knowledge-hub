---
id: provider-xcrz-sigmastar-demo-a98cedb3e1b28a343ca8499c
title: v40 接力：安全小幅候选已保留，置信度几何仍待完整拟合
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a98cedb3e1b28a343ca8499c.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:a98cedb3e1b28a343ca8499cc9ad46612a6de75ab003cdebece2b3fa3f6784d2
  source_sha256: 6664adf2b68fb3de4cd813744f82c7387a102bf8af7ac2f39d1f73c7562d877b
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a98cedb3e1b28a343ca8499c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-a98cedb3e1b28a343ca8499c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: v39已保留小幅优化候选：208例全体平均残留能量降低3.934548332929564%， 10组各3.3115556708359932%～5.216719193348707%，全部原保护通过。 精确指标、完整原门禁未通过的状态及二进制身份见REPORT-v39.md/BUILD-v39.json。
  最终持续回声未完全解决，不改产品默认，不宣称听感或设备通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: a98cedb3e1b28a343ca8499cc9ad46612a6de75ab003cdebece2b3fa3f6784d2
---

# v40 接力：安全小幅候选已保留，置信度几何仍待完整拟合

v39已保留小幅优化候选：208例全体平均残留能量降低3.934548332929564%，
10组各3.3115556708359932%～5.216719193348707%，全部原保护通过。
精确指标、完整原门禁未通过的状态及二进制身份见REPORT-v39.md/BUILD-v39.json。
最终持续回声未完全解决，不改产品默认，不宣称听感或设备通过。

本轮追加了PCMC38格式：明确逐频点beta，旧PCMD17仍拒绝新格式。
原有工具默认路径与旧统计入口仍拒绝新几何；新入口必须显式选择并验证控制、来源和格式。
v37只作冻结数学/数值控制，不继承声学资格。
184开发允许例已全部取得native/control新轨迹，1996旧v27暴露24仍排除拟合。
4组80例的正式映射已通过：development24/development8/exposed24/expanded24，
全部原始汇总指标与冻结v37一致，窗口和非输出轨迹精确相同，最终指标映射误差<=0.05dB。
另外5组104例尚未分析。初次development24未绑定冻结evaluation的统计仅作诊断，
合并入口要求frozen_evaluation_sha256，正式改用statistics-audited版本。

新tail_pcm_coherence_fit入口实现固定一次参考切线、正投影SI-cone、cohort Phase I及量化保护。
新模型契约与旧v37变体区分；失败可行性不输出模型/header。
当前没有完整184合格映射、没有启动新拟合、没有新模型或新声学PASS。
新fit入口的实际求解/新模型C header路径仍待执行，help和负控制不能替代它们。

最新130项Python回归全部通过，无skip；最新quarter C contract在ASAN/UBSAN通过。
contract SHA 475f419bd7c6d303c127ccb55fed98ae2526b64c9659e95fc0e7d15f4f492dcf。
164项非测试原生源码对冻结v20 build identity无漂移，静态库未重建/未覆盖；
ASAN不覆盖原生静态库全体。diff --check通过。

新的speaker/clip分离24例已取得96轨，split SHA a348b11708e5d27b9b6bdf06d685b31d641d937009af3971018b884c93db27aa。
它来自pinned官方train partition，NN预训练独立性未知；尚未评分，不是官方挑战或物理设备验收。
后续先完成184映射、固定一次拟合、全部208实际C/精确保护，再首次评分新24。

Runtime于2026-10-11T00:59:10Z要求compact（context ratio 0.555449），不是预算耗尽。
已完成已启动任务，无残留实验进程；保留goal active，最终目标未完成。
未commit/push/deploy/覆盖库，未修改上层reader/订阅/lease。
