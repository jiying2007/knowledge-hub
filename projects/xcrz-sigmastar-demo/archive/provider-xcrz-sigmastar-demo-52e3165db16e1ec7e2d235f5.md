---
id: provider-xcrz-sigmastar-demo-52e3165db16e1ec7e2d235f5
title: v28 直接 SI 锥候选：实际回归拒绝
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-52e3165db16e1ec7e2d235f5.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:52e3165db16e1ec7e2d235f55717089edcd263d17ae46fe40e66ecac28aaa18b
  source_sha256: b050054aaa225c4f73aacc045a36295ae0146b6cbd2b528e3b4770dcbbee7678
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-52e3165db16e1ec7e2d235f5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-52e3165db16e1ec7e2d235f5.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 本轮累计 Token 预算已获用户批准提高到 150000000；累计时间预算于 2026-10-10 14:57:59 UTC 按用户回复提高到 129600 秒（36 小时）。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 52e3165db16e1ec7e2d235f55717089edcd263d17ae46fe40e66ecac28aaa18b
---

# v28 直接 SI 锥候选：实际回归拒绝

本轮累计 Token 预算已获用户批准提高到 150000000；累计时间预算于
2026-10-10 14:57:59 UTC 按用户回复提高到 129600 秒（36 小时）。

模型 9e61a8b56b1fd6843db81114ffe006ed0980951a9bab541ef16f6a621b3ed431
使用冻结 136 开发样本、原生 AGC、前一帧 shadow DTD guard 和 phase 特征。
直接 SI 锥只对冻结仿射 PCM 模型提供准确保护几何，整数输出另行验证。
训练收敛，172 个量化语音保护约束通过，预测 far 平均改善 0.719735 dB。
98 个 Python 测试通过；实际 C ASAN/UBSAN 合同测试通过；guard 不匹配编译按预期拒绝。

实际 184 对 C 回归的远端 ERLE 差值加权平均为 +0.6937445652173914 dB。
九个 cohort 的 far_mean/far_worst、target_worst、near_exact、clips 和
agc_internal_saturation 均通过；七个 cohort 全部通过，另两个双讲最差保护失败。
regression24 中 fileid 530 和 907 的三位小数双讲 SI 差值为 -0.127 和 -0.513 dB；
exposed-independent24 中 fileid 531 为 -0.122 dB。

仅对这两个失败 cohort 做实际整数 PCM 精度复核，复核原始指标与观察器完全一致，
全部非输出轨迹与 native 保持一致。regression24 的精确最差双讲差值
-0.5127437623819304 dB，far_mean +0.6086890664008647 dB；
exposed-independent24 的精确最差双讲差值 -0.12164934119212134 dB，
far_mean +0.6314239148205208 dB。均为真实质量失败，不是四舍五入边界。
原门槛双讲 >= -0.1 dB、target >= -0.2 dB、far_mean >= +0.5 dB、
far_worst >= -0.1 dB 均未放宽。

候选 actual C SHA 9fafd2106eed2395ad246c874abebff43cbdb57ac2936e47cc59aeb8548adc93；
control SHA 24bfd0a9cc4f9c13ae18600b697100feb15515c2dadb7b3c8e90c4641462d87b；
ASAN/UBSAN 合同 SHA 3a4e03c31ab793cb28c43fc981b2d7b8c8a78e78187dfbb62217d8dc24f7ad8f。
证据为同目录 tail-pcm-*-v28.json、tail-pcm-*-qualified-v28.json，
pcm-precision-regression24-v28/precision.json 与
pcm-precision-exposed-independent24-v28/precision.json。

结论：v28 拒绝生产采用，shipping_approved=false。未改变生产默认、上层生命周期，
未 commit/push/deploy。新 1996 独立 24（SHA
1996a5159241ac016122e53772998b862bfdf6289e43ff0bd61841bc7b94fffb）仍未评分、未拟合。
离线结果不证明设备听感或 CALL 严重回声已解决。

下一步可显式将已多轮暴露的两组 48 样本重新分类为开发，形成冻结 184 开发集，
保持新 1996 独立 24 在训练外。原 136 路径必须继续拒绝这 48 样本，
184 路径必须明确选择、精确校验九个 split SHA 和完整基数；不得把原回归改称独立验证。
