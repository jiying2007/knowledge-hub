---
id: provider-xcrz-sigmastar-demo-cd7b25f3679b651b2a34c81d
title: 当前最优已验证候选：固定半强度v46，仍为次级优化
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cd7b25f3679b651b2a34c81d.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:cd7b25f3679b651b2a34c81d72d994b810d86f048b6665d58fb7076fdf9888e0
  source_sha256: f5584232e97d1c75c7e71510de3349c8630b1ef709aea01f4104db9948267049
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cd7b25f3679b651b2a34c81d.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cd7b25f3679b651b2a34c81d.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 当前选择保留v46：原生AEC/AES/NN主链、固定native-anchor表系数中点、连续回声相关置信度混合、 上一Feed双讲保护、原生AGC驱动。相同256回归及评分前冻结的新24均比旧v39有更高平均残余能量收益，
  并满足所有原人声/target/far/削顶/AGC保护。这里只对已验证安全候选作选择，不宣称全局最优或完整解决。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: cd7b25f3679b651b2a34c81d72d994b810d86f048b6665d58fb7076fdf9888e0
---

# 当前最优已验证候选：固定半强度v46，仍为次级优化

当前选择保留v46：原生AEC/AES/NN主链、固定native-anchor表系数中点、连续回声相关置信度混合、
上一Feed双讲保护、原生AGC驱动。相同256回归及评分前冻结的新24均比旧v39有更高平均残余能量收益，
并满足所有原人声/target/far/削顶/AGC保护。这里只对已验证安全候选作选择，不宣称全局最优或完整解决。

| 数据 | v39残余能量平均下降 | v46残余能量平均下降 | 原保护 |
|---|---:|---:|---|
| 相同256例、12组已暴露回归 | 3.9384752811380035% | 4.939928292330836% | 两者通过 |
| 评分前冻结的另24例首次评分 | 4.596562733602055% | 5.316671156513844% | 两者通过 |

首次新24中v46远端均值+0.24450488929741dB，双讲最差-0.029832021557693267dB，
target最差-0.05519591249817557dB；原双讲/far最低-0.1dB、target最低-0.2dB保护不变。
完整每组far平均至少0.5dB门槛仍未达到。能量平均按逐clip能量比的算术平均计算。
全强度v44在前一次新24中双讲最差-0.13807983091313902dB，超限，因此拒绝晋升，
没有以更高平均回声收益取代人声保护。详细身份与数据角色见REPORT-v47和SELECTION-v47。

## 现有设备原始录音重放与试听

复用用户给出的rpm240/rpm480共16份录音，七文件/session/PTS/seq/epoch及参考delay严格验证。
新Host C桥不添加预热、补零或参考调整，分别在VOICE/CALL按原始双麦和参考逐帧运行。
全部32个原生控制输出逐样点匹配冻结原生Host共享库；16个VOICE候选与原生逐样点一致。
quiet/near/motion/near-motion的CALL也逐字节一致。全部场景内部/最终削顶不增加。
共64份原生/候选WAV在capture-listening-v48，不覆盖原始录音；可直接配对试听。

| 原始录音场景 | CALL候选相对原生输出总能量变化 |
|---|---:|
| rpm240 far | -0.601885181186984dB |
| rpm240 far-motion | -0.7878981775204185dB |
| rpm480 far | -0.46751913260856043dB |
| rpm480 far-motion | -0.4260548354495125dB |

四份双讲/双讲运动场景总输出能量变化-0.047034至-0.094969dB。
这里含噪声且没有独立近端/纯回声真值，不能将它们称为ERLE、纯回声消除比例或人声质量资格。
没有本轮设备实时处理/持续远端听感证据；所有重放均为Host离线算法执行。
capture-listening-v48/results.json SHA407375a3b6bda13c2f4a2d8f9fc893bb40259efbb3be387f3be4307d509f8ffc。

## 构建、运行成本与验证

149项Python回归全部通过，无skip，6.891秒；其中新增有界传输、延迟窗口及C桥负控制。
独立ASAN/UBSAN桥覆盖完整零帧、坏magic/长度/截断/额外字节/超限输入和禁止覆盖输出。
原生archive未整体ASAN插桩，不由这些合同推导原生库完全无缺陷。
初次C桥候选编译缺少PCM_DESIGN默认宏，补充默认0后编译通过，未改变原推理流程。
help/dry-run从/tmp执行，验证16份输入后writes=false；实际工具随后完成全部16份重放。
164个非tests原生源码/头对冻结native build仍完全一致，新增Host工具和C桥另行绑定身份。

按当前项目configs/current.configs及实际build/build.mk的ARM dry-run提取68个原生编译单元，
SigmaStar glibc arm-linux-gnueabihf GCC11.1全部编译成功；在独立证据目录归档静态库，
候选/原生控制录音桥和候选/原生性能程序均完成ARM链接。
ELF32 ARM little-endian EABI5 hard-float、ARMv7/VFPv4/NEON属性已核验，未执行板端测试。
首次未传项目config的dry-run产生空CHIP shell警告，仅作失败intake，未用于构建；
补充实际config、ALKAID_PROJ及SHELL=/bin/bash后无该错误，并绑定完整编译计划。
当前没有qemu-arm，未宣称ARM运行或PCM跨架构资格；也没有设备安装和运行证据。

五轮交错Host性能，固定每profile2000帧：native CALL单帧thread CPU中位数208.960us，
candidate240.786us，增加15.230666156202144%。VOICE PCM哈希五轮均一致。
native API arena308308字节不包含Host adapter额外分配，不能把它报成候选总内存。
Host时间不能推导SSC305实时裕量；保留两个ARM性能程序用于后续受控测量。
performance-host-v49.json SHAd34426f027e0187daae3cc3b08cae90995afe6a63c188e2ec8cf8a848d64646e。

ARM archive SHA59a2a63b3bd73d276c21e22ff5fab0764673fa805ff067d8c1f757219949fbdd；
ARM candidate SHA d7c73d3d7bec20a01c20426c2337d920c3d0c6f61dc538d972dc8e98b5c4ac45；
ARM native SHA12e1a80827a609ef751828f822ae7605bdfa57e5f9f57c9b35d505d77d8252eb。
ARM性能candidate SHA30efa0cbbb079dbe3e5f6c987b541a5b291badf24c6f997cf1516cedb72c57d4；
native SHAd7131a7a96fb1ae9967e53c7a458862a85875df2be5f2a4a33b6e518426dfb0f。
ARM编译计划SHA25cec5c3d3f4da405eab7c1769de2ceba3b301f2ef8f334b6e83c684cba3c2dc。
BUILD-v49.json SHA1326c6c48af60bce0390340212543be004d249b13028a5846fb2fe4eeabe4f72。

## 当前边界与下一阶段

主目标仍为严重CALL远端持续自回声，状态active/open；完整解决和shipping均false。
本阶段只形成已验证优化候选、试听材料及ARM测试程序，没有修改产品默认/安装库/app或上层reader/订阅/lease。
代码、对象、Host重放、ARM链接和板端/持续听感资格分别报告；不以其中一项替代另一项。
下一阶段先把固定候选接入受控CALL实际运行，核验CPU/内存、切换与Reset，及远端持续/双讲听感；
进一步提高消回声收益需要独立机制证据，不能继续靠放宽门槛或强压AGC/人声。
原始数据、WAV、库和二进制不归档到知识正文或Git；仅本文脱敏可复用结论可形成reviewing候选。
无commit/push/deploy。累计预算250000000Token/129600秒未重置，截止2026-10-11T02:56:57Z。
