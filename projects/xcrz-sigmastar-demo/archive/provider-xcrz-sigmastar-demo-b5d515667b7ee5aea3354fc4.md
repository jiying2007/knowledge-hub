---
id: provider-xcrz-sigmastar-demo-b5d515667b7ee5aea3354fc4
title: CALL AEC v60 独立反例与 v61 保护实验
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b5d515667b7ee5aea3354fc4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:b5d515667b7ee5aea3354fc44904121a79062682d2607e0a26947942a77e447a
  source_sha256: b941ed80972e4d36c4e9943945036de22f0b09ab63ff82d728a86d36702e2fdb
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b5d515667b7ee5aea3354fc4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b5d515667b7ee5aea3354fc4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 持续明显远端自回声仍未解决；未找到可称为最优的最终方案。本轮新数据使原v52/v59保护资格不能推广到全部328例。v61修复反例，但增益太小，不采用。 评分前冻结24例，四组各6，排除之前14组304 fileids及所有其说话人/源语音片段，新增24也相互隔离。96四轨WAV格式/LFS
  SHA/size/length一致，固定官方Microsoft AEC-Challenge revision6c633d0a9d2a143a0e364899b91b06f127315b18，meta SHA6b867aa68f510e4bafc9ffa05202930ffc1bb54bb0cffe66aa
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: b5d515667b7ee5aea3354fc44904121a79062682d2607e0a26947942a77e447a
---

# CALL AEC v60 独立反例与 v61 保护实验
持续明显远端自回声仍未解决；未找到可称为最优的最终方案。本轮新数据使原v52/v59保护资格不能推广到全部328例。v61修复反例，但增益太小，不采用。
## 独立样本与身份
评分前冻结24例，四组各6，排除之前14组304 fileids及所有其说话人/源语音片段，新增24也相互隔离。96四轨WAV格式/LFS SHA/size/length一致，固定官方Microsoft AEC-Challenge revision6c633d0a9d2a143a0e364899b91b06f127315b18，meta SHA6b867aa68f510e4bafc9ffa05202930ffc1bb54bb0cffe66aa1ec3bcc606f3e5；split SHA573c01f8e59e23951f46f7f5c42bc92149777ad54b182152fb614e745f67bd90；intake SHAeda5e973dd06996f504970bd890f3007d2e3b4ae755b2e057a806377cbea1141；pre-score SELECTION SHA4eee55681b7aa4177d4025d11f5c30c8cb5910eb4b4d07ba1d17a559d13ab536。
来源train partition，仅对项目拟合/之前评分独立，NN预训练独立性未知，不是官方挑战测试资格。评分后新24已exposed，后续修正以该反例开发，不能称新盲测。
## v60 配对实际输出
同样24四轨/原生baseline，v59与v52分别实际执行，实际整数PCM精度审计：
|版本|远端残留输出能量平均降低|远端改善均值|双讲最坏变化|保护结果|
|---|---:|---:|---:|---|
|v52|5.9250700767%|0.2692186228dB|-0.3427457910dB|FAIL|
|v59|5.9717636048%|0.2713918090dB|-0.3427458355dB|FAIL|
反例fid644，v52 far+0.1972052230dB/DT-0.3427457910/target-0.0681597223；v59 far+0.2012469770/DT-0.3427458355/target-0.0681597191。双讲门槛>=-0.1dB；两者差约4.45e-8dB，额外H投影没有修复原模型此问题。新24所有near-only指标/clip/native AGC保护保持；v52侧逐样本PCM轨迹审计，v59侧逐帧整数能量与target dot审计。
原304 PASS仍是其固定集合事实；发现独立反例后，不得再说v52/v59对全部328安全，或称最优。不改写原冻结记录。未做原计划v59 raw16/资源/native接入，因为保护失败。
## v61 实现与结果
四个独立Host文件：sevc_tail_base_reference_guard_adapter.h、sevc_tail_base_reference_guard_regression.c、base_reference_guard_audit.py、test_base_reference_guard_audit.py。只对原v52修正加因果raw麦克风/播放参考相干性，和NN平均增益功率导出的1-sqrt(fVad/Q24)限制。fVad不是语音概率。没有v59 H投影，未改原生NN/AEC/AES/DTD/AGCdriver、模型或上层音频订阅/lease/reader。
alpha1/8/count8；先决策再更新；参考在完整AEC回调后提交，与上一mic/echo做实际身份检查；DTD veto/参考丢失/非CALL/Reset清历史。Q20向native凸组合，uint64整数floor/端点energy保护，异常回native。identity对照原v52严格保留原全部metrics/metadata。
冻结源码/制品后，首56例实际评分及精度审计：
|组|数量|平均远端能量降低|双讲最坏变化|保护|>=1%增益|
|---|---:|---:|---:|---|---|
|development24|24|0.1688433063%|-0.0062227479dB|PASS|FAIL|
|development8|8|0.4324724183%|0dB|PASS|FAIL|
|new exposed24|24|0.3245246746%|-0.0041139540dB|PASS|FAIL|
56例等权平均能量降低0.2732251944%，worst far-0.0019883025/DT-0.0062227479/target-0.0218995196dB。fid644退化收回到约0dB。pure-near全部指标exact、clips不增加、原生AGCdriver/gain/state轨迹保护PASS。没有逐样本archive的v61 all56 nearPCM资格；生命周期合同比较了实际输出PCM。增益低于次级候选每组1%门槛，选择replan，未扩大剩余272，也未做v61 raw16/CPU/native/ARM。
## 构建、回归与fresh review
实际三次Werror构建(identity/candidate/sanitized contract)exit0。ASAN/UBSAN包含20000整数凸组合/floor/边界/NaN/端点及实际两实例3循环CALL/noRef/VOICE/Reset/DTDveto/AGC/错帧负控/owners释放，PASS。库内部为冻结未插桩原生；不声称全库sanitized。
identity32例全部原metrics及metadata严格exact，would_change_bins1628528，alignment_failures0。181项Python回归实际exit0/8.479s/无skip，新增3个负合同测试；旧桥接/阶段观察入口使用原环境制品，没有因可选env缺失跳过。/tmp --help与--dry-run实际exit0/writesfalse。
本轮末fresh rehash：60个旧冻结/新身份；原生host启用/关闭/ARM三个build各185源码头与shared SHA未变；208条新trace绑定和416次input绑定PASS。父仓/aispeech独立子仓diff--check exit0。原native v52开关默认仍为0，未部署/重新链接用户应用。构建/Host结果不代替设备听感。
早期只读错误：猜测tail_capture_bridge.py路径不存在，后确认实际tail_capture_replay.py；恢复的identityCmd59是数组，初次误用.replaceAll在发出命令前报错，改按数组生成v61新命令。没有覆盖旧输出、改变冻结实验身份或遗留失败进程。所有最终构建/实际评分/精度审计入口退出0；审计结果的质量保护FAIL如上独立保存。
## 取舍与下一步
新PLAN-v62只冻结计划，尚无代码或制品：native+3/16*(v52-native)的固定有界修正，风险预算由新反例提供但没有线性安全保证；必须实际56→328保护+每组>=1%，不扫描强度、不加入v59或v61。满足后再16原采集/资源/native默认off及ARM验证。无法达到门槛时继续保留负证据，主目标不关闭。不存在现已验证的全328有效最优增强版本。
累计250M Tokens/48h不重置，Runtime在context_ratio0.532221要求host compaction；checkpoint后接力v62，不因本地Runtime conformance推导AEC产品PASS。无agents/commit/push/deploy/restart/删除/新增设备采集。

