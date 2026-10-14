---
id: provider-xcrz-sigmastar-demo-6d1596fda156ad137fd38ddc
title: CALL AEC v66 资源、v67 幅度占比与 v68 首次验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6d1596fda156ad137fd38ddc.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:6d1596fda156ad137fd38ddc04cf4ac4f2b36e9d77785f67ecfad0a200dad86b
  source_sha256: ba433c96ddfd199c8b54034cb452f847e0a8561eaf6fe9801290b26d45faa183
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6d1596fda156ad137fd38ddc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-6d1596fda156ad137fd38ddc.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 主目标持续远端自回声完全解决仍UNSOLVED；当前证据支持v67作为优先接入候选，不是全局最优或设备/电话放行。用户明确提高预算后累计Token300000000，时间172800s/deadline2026-10-11T14:56:57Z不重置。原goal
  active/open1，revision104，运行门禁新鲜取证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 6d1596fda156ad137fd38ddc04cf4ac4f2b36e9d77785f67ecfad0a200dad86b
---

# CALL AEC v66 资源、v67 幅度占比与 v68 首次验证

主目标持续远端自回声完全解决仍UNSOLVED；当前证据支持v67作为优先接入候选，不是全局最优或设备/电话放行。用户明确提高预算后累计Token300000000，时间172800s/deadline2026-10-11T14:56:57Z不重置。原goal active/open1，revision104，运行门禁新鲜取证。

v67唯一机制变化是线性频率输出修正强度从v66功率比改成幅度比：alphaQ20=floor(.5*sqrt(min(1,pe/pm))*Q20)。使用父已有平滑1/8与8帧暖机，invalid->0native，旧DTD/ref/phase保护、native AGC driver、uint64端点能量上限/native floor原样；没有新NN/AECcallback/rawqueue或未来标签。冻结4新Host源码、candidate/identity/ASANcontract三制品见BUILD-v67-pre-score.json，评分后没有调整。native/default/prod/上层reader订阅lease均未改变。

完整352/16组保护PASS，远端输出能量均值2.575509539425482%；最差far-.00021129610794403815(fileid1262)、double-.027862035086912762(215)、target-.055172159628925715(1088)。near所有指标exact、frontend/AGC/clip PASS，704 trace和1408输入绑定fresh。原比较v62/v63/v66同352分别1.509139/2.459945/2.016646%，DT最差-.044629/-.079602/-.030502。完整每组mean far>=.5dB仍FAIL。

新v68数据在评分前固定24例，排旧352及speaker/sourceclips，四组各6、SER±各3，official pinned6c633d0a9d2a143a0e364899b91b06f127315b18，96 LFS SHA/size/WAV格式/frames与remote metaPASS。train分区，只独立于本项目fit/已评估集合，NN预训练独立性unknown，非官方challenge资格。SELECTION-v68.json先freeze排352无旧304标签错误；PLAN-v68-validation.json及四候选参数sealed，无评分后retune。新24目前已暴露不得再称blind。

新24四候选全部保护PASS：v62 energy1.3422251000406964%、DT-.04450624212017473；v63 2.1859663134986014%、DT-.07475652606039507；v66 1.9913338883942666%、DT-.03754662349140281；v67 2.4460468875507613%、DT-.057469997468510226。v67在这组比v66更大双讲损失，但仍过-.1门槛，不能声称全面dominate。四组fresh192trace/384input绑定PASS。

合并376均值和最差DT：{"62":{"pairs":376,"energy":1.4984852324319122,"worst_double":-0.044629001981391525},"63":{"pairs":376,"energy":2.4424571748517194,"worst_double":-0.0796023880658634},"66":{"pairs":376,"energy":2.0150303731576193,"worst_double":-0.03754662349140281},"67":{"pairs":376,"energy":2.5672459659015634,"worst_double":-0.057469997468510226}}。因此按远端收益优先且逐例保护，当前四候选中优先v67；v66较保守候选保留。主要回声未解决。

v66原16×双profile执行与native库PCMexact；VOICE16、CALL quiet/near/motion/near-motion8全PCMexact、clips不增。四far输出energy变化-.515868/-.624969/-.400745/-.354622dB。v67同范围全部保护PASS，四far-.5246575539982656/-.6467755310674856/-.40968363936247093/-.36988303017863844dB。没有干净echo/near目标，不将输出总能量下降称ERLE/双讲保真，未做phone听感。v67128PCM/WAV文件绑定fresh；输入和native库已实际重放验证。新包装/capture制品身份绑定说明基础modelSHA是v52，不误称本次候选等于canonicalv52。

实际sizeof v66/v67 arena308308、parent31064、own64、slots16；Host包装父状态使用heap，非native端资源。v67五轮serial交错native/v63/v66/v67，每轮80warm+2000frames，线程耗时中位CALL206.575/240.282/243.469/241.054us，v67相对原生+16.69%，VOICE中位104.891/95.630/96.381/108.036us且波动，不声明VOICE耗时不变或SSC305达标。完整20执行stdout、PCMhash见RESOURCES-CAPTURE-v67.json。上一v66三候选五轮数据独立保留，不混用本轮均值。

3次-Werror构建成功，20k full-int32 math、sqrt count/invalid/NaN/Inf/zero/tiny/ratio>=1、ASANUBSAN两实例/thirdreject/identityPCM/AGC/CALLref-loss/VOICE/Reset/releasePASS，仅包装层插桩。全Python195/6.981s/exit0noskip，负fixture拒绝日志不算测试失败。新tool非repohelp/dryPASS(writesfalse)，首次dry复用已存在audit目录被正确拒绝，随后新目录dryPASS。无需无故重复全测试。

当前未做v67完整32指标identity回归(native逐点identity生命周期已PASS)、native接入/ARM运行/设备安装/电话连续echo验证。既有v54原生v52开关仍默认关闭，其旧304通过不能覆盖644新失败。v66audit.kind旧v63字面量erratum原样保存，v67kind/version/sqrt机制正确。

证据：REGISTRY-v67-352.json、VALIDATION-v68-four-candidates.json、RESOURCES-CAPTURE-v66/v67.json、PLAN-v67-amplitude.md、PLAN-v68-validation.json、BUILD-v67-pre-score.json。无commit/push/deploy/restart/cleanup，dirty/raw/旧冻结source/bin不改。Provider归档仅reviewing候选，成功回执后才宣称记录，不替代owner或release。
