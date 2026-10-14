---
id: provider-xcrz-sigmastar-demo-cb4606d4a79c53923e6f7d0a
title: CALL 低延迟分块卷积的数学、接口及质量对照
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cb4606d4a79c53923e6f7d0a.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:cb4606d4a79c53923e6f7d0a764babf9d2c25df03f1baf6a2d433102c010c636
  source_sha256: 794e06379c7c81733c828cbf5f3222370978f33bf9082314e7ea603e97d50015
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cb4606d4a79c53923e6f7d0a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-cb4606d4a79c53923e6f7d0a.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 状态：reviewing / needs-fix。本阶段完成两个Host候选和默认恢复验证，持续明显回声总目标未完成。两个候选均拒绝；产品主链源码接入已撤回。上层profile、reader、订阅和业务未改，未部署、未重链ARM库/应用、未提交推送。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: cb4606d4a79c53923e6f7d0a764babf9d2c25df03f1baf6a2d433102c010c636
---

# CALL 低延迟分块卷积的数学、接口及质量对照

状态：reviewing / needs-fix。本阶段完成两个Host候选和默认恢复验证，持续明显回声总目标未完成。两个候选均拒绝；产品主链源码接入已撤回。上层profile、reader、订阅和业务未改，未部署、未重链ARM库/应用、未提交推送。

## 假设与原型

参考独立aec/src的因果分块约束思路，独立实现Host浮点FFT和普通MDF，不复制旧常量或第三方源码。256点hop、512点FFT、4个256tap分区，64ms因果建模范围，单麦mic1、单usedREF；没有旧NLP。残差与延迟mic分别通过相同SEVC sqrt-Hann/FFT，echo=mic-residual，同源同窗同Q格式，接入现有AES/NN/AGC。VOICE走原主链。

原型Host内mic延迟16点，未改原始采集或HDI20点参考延迟。CALL评分延迟明确528点（33ms），现有CALL512点（32ms）；不沿用旧后端1280点。原型state 78864字节，arena387180字节，较原308308多78872字节。使用double浮点和额外FFT，没有获得ARM CPU、栈或产品资格。

本轮变量：A为普通归一化MU=0.2；B仅在分母增加1%当前宽带参考均功率正则项。分母均包含前帧误差功率、四分区参考功率及固定epsilon，梯度IFFT后保留前256点再FFT，逐分区更新。不使用AES DTD冻结，也没有前后台保护或可变学习率；不是完整Speex实现。

机制参照边界：[SpeexDSP 1.2.1官方mdf.c](https://raw.githubusercontent.com/xiph/speexdsp/SpeexDSP-1.2.1/libspeexdsp/mdf.c)使用AUMDF、可变学习率和前后台滤波；本轮只验证基础分块机制，不据此宣称其完整鲁棒性已经移植。

## 独立数学与无参考接口验证

- FFT往返最大误差5.55111512313e-17；已知31点/401点双径因果IR，训练600帧后最后100帧ERLE为A 73.927380dB、B 73.941036dB。两者内部削顶0。
- 新构造无参考脉冲确认16点mic延迟及10000电平正确。
- `mdf-interface-v5.json`：153600点调制近端语音/噪声、全零参考，候选完整CALL与显式延迟mic后的原生完整CALL逐点相同；PCM SHA256 `a87dece603fc9f1af69becb66490c3c897a38e5e890e9e4883cf4cbf6aacc004`，内部削顶0。
- 上述只证明受控因果IR计算及无参考接口；不能覆盖有参考的自适应稳定性，也不构成真实语音质量通过。

## 固定输入配对质量

每个候选都完成24组公共四轨真值和16组设备场景×VOICE/CALL。split、nearend_scale、四轨hash和评分窗保持原值，split SHA256 `4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb`。设备实际采集profile全部VOICE；CALL是真实算法Host重放，不能当作设备CALL听感。设备总能量衰减包含AES/NN/AGC及噪声，不能称纯AEC ERLE。

| 候选 | 四个设备远端整链衰减相对原CALL变化 dB | 公共远端ERLE平均变化 | 公共纯近端SI-SDR最差变化 | 公共双讲SI-SDR平均/最差变化 |
| --- | --- | --- | --- | --- |
| 普通MDF A | -3.0781 / -2.0083 / -1.8973 / -2.9564 | -1.452292 | -0.284 | -4.266750 / -36.184 |
| 1%正则MDF B | -2.2786 / -1.3945 / -1.0187 / -2.2389 | -1.491125 | -0.284 | -4.082917 / -33.085 |

四远端顺序rpm240 far、far-motion、rpm480 far、far-motion。设备线性频谱阶段相对变化：A -2.7247/-2.5438/-2.6099/-3.2713dB；B -2.0840/-1.9100/-2.0042/-2.6812dB。该频谱量包含实录近端噪声，只按其实际边界报告。

两个候选各16个VOICE PCM SHA均与原生相同。B设备16个CALL原型内部PCM削顶均0，所有有效完整输出的削顶也为0。但这不代表公共数据内部没有异常。

## 最差样本局部分诊与证伪

公共file0 B的绝对指标：原生远端ERLE -0.070dB、双讲SI-SDR improvement11.439dB；候选远端-10.006dB、双讲-21.646dB。因此对应变化为-9.936dB及-33.085dB，不能混淆绝对值和配对变化。

增加计数的同库clipprobe表明file0混合序列原型内部削顶24317点，而完整输出削顶0。AES/NN掩盖了原型内部异常；最终输出削顶不能替代线性AEC内部稳定性检查。A未在完整公共/设备记录中测量内部削顶，不补造其计数。

进一步只对file0把两边参考延迟都改为0作诊断：原生远端ERLE-4.707dB、双讲0.459dB，B远端-10.314dB、双讲-16.428dB，内部削顶21131点。原始正式24组配对未改；该诊断不进入选择成绩。它证伪“只要取消主相关峰对齐即可修好该候选”，没有证明当前SEVC时序是根因。

复核候选原二进制与clipprobe的重复调用，主指标一致；一度怀疑复现差异，最终确认是把变化量与绝对值混用，未发现新初始化缺陷。不把这次误判记作产品问题。

参考模型/弱激励归一化、自适应保护及非线性回声仍需进一步隔离；现阶段不归因于单一根因。已知IR校准高ERLE不能覆盖非线性/噪声/双讲数据。

## 恢复与新鲜验证

临时产品接入涉及sevc_func.c/sevc_types.h，Host bridge/evaluator也有临时分支；已逐处撤回，保留本轮接入快照于本地`mdf-host-source-v5`供核查，不进入Provider正文。数学原型、接口probe与旧实验库读取支持保留在tests/tools。

- 当前SEVC绑定及bridge等43来源项与v4相同，没有v5产品算法变化。
- `fresh-default-v5`默认宏为空，实际Makefile 69编译单元，170来源项全部无漂移。
- shared SHA256 `1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe`；static SHA256 `cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532`，两者均与v4相同。
- build.json SHA256 `d55748304cc081d9317c2ca70f4ded4de10eccfb9a4b86d8a95edfdf7f16dae3`。
- `fresh-default-v5-replay`16组七文件输入配对和32个VOICE/CALL PCM SHA均与v4完全一致。
- 26项Python契约通过；新增MDF延迟合法/非法输入检查。数学C校准A/B和无参考完整接口probe通过；非模块cwd help通过。根及AISpeech git diff --check通过。
- 未修改ARM产品源码，不新增ARM构建或设备/HIL声明；前序旧AEC两项保护与ARM对象证据仍以v4为准。

候选库A shared `42c2ba336bb69bc975c9c6ea201c040b82fd4c922f6407c0b2f2106d5de4712d`，B shared `a2f43aab4ea68add41674e98d7f8ec3dc5670222198435d6c651822c5d642852`。正式公共结果：supervised-mdf-mu200.json SHA256 `e9adfe0a00e3c62c15acadfd6eb6f6eeb3349e39f7734f5897ffa6dad401413f`；supervised-mdf-reg10.json SHA256 `61e9e5ec323730efdc86c170a319be45c00cd37be6d6d0d99b77976c6e3250d3`。相应replay/results.json绑定16组原始七文件和全部输出。

## 后续边界

停止同类MU/分区盲调，重排为独立线性AEC稳定性、弱激励/非线性条件及前后台滤波保护。先在Host证明有参考时不会内部削顶或错误增益，再接回同源AES/NN接口并过24真值保护。保留当前默认主链；上层音频业务、HDI参考和profile协调不改。

持续明显回声未解决，近端/双讲及实际设备听感仍是开放项，Runtime目标保持active/open_items=1，不能将本阶段实验完成当作产品目标完成。
