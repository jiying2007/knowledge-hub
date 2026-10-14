---
id: provider-xcrz-sigmastar-demo-e005268fa28eea1afdec9982
title: CALL 逐例保护、AGC交互及独立验证 v13-v16
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e005268fa28eea1afdec9982.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:e005268fa28eea1afdec9982590abda250fe1ab772d4b502823a5c07942cbc7a
  source_sha256: aaee5646cc3b967ca828032d927b7ca7ccde86d771c0027a04926c9c3a816365
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e005268fa28eea1afdec9982.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e005268fa28eea1afdec9982.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 日期：2026-10-10。源码根为当前PCR02 source；aispeech独立Git root，branch dev/audio_process。 本轮逻辑目标仍为改善持续远端自回声并保护近端/双讲与上层业务，completion_claim=false。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: e005268fa28eea1afdec9982590abda250fe1ab772d4b502823a5c07942cbc7a
---

# CALL 逐例保护、AGC交互及独立验证 v13-v16

日期：2026-10-10。源码根为当前PCR02 source；aispeech独立Git root，branch dev/audio_process。
本轮逻辑目标仍为改善持续远端自回声并保护近端/双讲与上层业务，completion_claim=false。

## 结论

v16首次通过全部32个开发样本联合门槛，但首次独立24例未通过双讲门槛，不能推荐生产采用。
远端收益在独立数据上存在，但三个双讲样本退化：202 -1.303、215 -0.338、263 -0.170dB。
近端音量/局部MSE保护不等于最终PCM SI-SDR保护；不把平均收益、无削顶或模型可行当作产品资格。
开发选择的固定半强度在独立集前已冻结，独立结果之后没有重训/调比例/修改AGC参数。
默认生产源码/参数/库及Sensor/API/proto/reader/订阅/lease保持原状，没有提交或设备部署。

## 方案及单变量实验

v13仅改变训练目标。保持v12的8×8×4设备特征、EMA1/8及原floor0.2..1，训练观察器
按上一帧两个hop的纯far/near/DT统计，混合窗口不进入约束，标签不进入推理。
32例全部原指标以及旧all-window Gram/RHS/target/native error与v12精确相同。
far误差逐例归一等权目标，near/DT每例MSE不高于native+1ppm、target dot不低于native。
固定rho1、1024步ADMM；两例保护未满足、local far平均+1.10458/min-0.14622dB，qualified=false，
不生成推理header。此为数值未可行负结果，不证明方法不可行或数学最优。

v14补足逐例far误差约束，对应最差-0.1dB并留1ppm量化余量。rho仍1，最多32768步，
每64步检查primal/dual max<=1e-8。实际到达上限，primal2.50e-7、dual1.52e-5，未收敛。
量化后32个DT约束通过，local far平均+1.27503/min-0.0999961dB，允许一次完整链；
不宣称全局最优。没有自然near纯窗口的eligible训练统计；near-only由原守卫和完整链控制保护。
冻结模型SHA 6c38149139f0e87bf654b4c0b1b257c8b42643ea3cbdb15882a4c9bf12b4f6be。

匹配时域观察用独立scratch/history/counter调用原生OLA，保留native IFFT和AGC/OLA原状态。
相同CALL512点延迟、相同最终窗口、同一target/mic；24例观察器不改变任何原指标。
v12 file18 pre-AGC DT+0.623405而final-1.197dB；file7 far+5.052214变+0.492dB。
变化落在AGC处理及其与OLA的交互，不能单凭此认定AGC实现bug。

v15用原生NN输出的独立IFFT驱动原生AGC Feed，增益计算与参数不变；将原gain按原round/clamp
施加到候选信号。Host link-wrap只识别两个显式owner，未注册plain走原Feed。
原生gain轨迹hash与identity完全相同，driver不读clean-near标签；额外IFFT未验证ARM成本。
v12表的24例far平均从+2.1165至+2.55075，但file18 DT仅由-1.197变-1.175dB，
因此“新抑制改变gain轨迹是主要双讲退化原因”被此对照否定；不据此继续调AGC参数。
v14表与此driver组合只剩file18 DT-0.170未过门槛，其他所有开发门槛通过。

v16不重训，只做一个固定收缩：effective_gain=floor((native_gain+predicted_gain)/2)。
所有stable CALL/ref/quiet/native-gain-FIFO匹配守卫、历史清理及原生状态推进不变。
该比例基于开发负结果选择，只有这一候选，没有比例扫描；不称独立资格或数学最优。

## 完整链结果

相对原默认，单位dB；far为ERLE，DT为SI-SDR变化。

| 候选/数据 | far平均/最差 | DT平均/最差 | target最差 | 联合门槛 |
|---|---:|---:|---:|---|
| v14开发24 | +1.25075/+0.227 | +0.37892/-0.317 | -0.021 | false |
| v14开发8 | +1.62488/+0.033 | +0.47325/+0.064 | -0.052 | true |
| v15开发24 | +1.50433/+0.529 | +0.40508/-0.170 | -0.006 | false |
| v15开发8 | +1.73575/+0.033 | +0.48550/+0.062 | 0 | true |
| v16开发24 | +0.78513/+0.292 | +0.24833/-0.013 | -0.003 | true |
| v16开发8 | +0.91063/+0.033 | +0.30963/+0.085 | 0 | true |
| v16独立24 | +0.75000/+0.065 | +0.17883/-1.303 | -0.057 | false |

全部near-only原指标精确一致，内部IFFT/OLA/output及最终clip均未增加。
门槛未变：far mean>=+0.5/min>=-0.1、near/DT min>=-0.1、target min>=-0.2dB，near-only相同且clip不增。
v16独立失败只在double_worst，不能由其他通过项抵消。

## 独立边界

v11预先冻结的24例96轨，speaker/source均与32开发例分离，四组各6例。
exact Microsoft revision 6c633d0a9d2a143a0e364899b91b06f127315b18；split SHA
f7429c362fdaee14a2be5c47da789500672e14c5e6f3cd552188ce6045254b34。
本轮首次且唯一评分v16，96轨SHA/size已再次验证；评分前冻结RECIPE-v16。
该集现已曝光。不得称未来按其结果修改的候选仍在同一独立集做首次资格验证。
没有新设备CALL处理数据、真实远端电话听感或正式Challenge资格声明。

## 新鲜检查及默认身份

- 68项Python检查一次完整运行通过且无skip；凸投影解析/旋转/退化/不可行控制及观察器身份负控制通过。
- risk统计与训练ASan/UBSan通过；same-hop/独立Gram/RHS、NN FIFO/ref/no-ref/Reset/错误历史覆盖。
- PCM unity-AGC逐样本/native OLA一致、scratch/history/counter隔离、Reset及错误尺寸通过。
- sidechain两实例/未注册plain/VOICE/no-ref/Reset/原生AGC状态/容量拒绝/slot复用与缺driver负控制通过。
- 半强度推理ASan/UBSan通过；24对O2/sanitized共48 records完全相同。vendor库未sanitizer插桩。
- 32开发+24独立的identity全部原指标一致，driver逐样本匹配且candidate gain hash与identity相同。
- 原v12无新宏推理二进制与旧冻结二进制逐字节相同，旧兼容路径不变。
- 非仓库cwd Python完整检查、CLI help及PCM/资格check dry-run通过；未为重新求解而重复32768步训练。
- fresh-default-v16-bound：69编译单元、181来源项哈希再次核验，164非tests来源项与v12相同。
- 默认so SHA 1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe；
  默认a SHA cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532。
- 父/aispeech子仓diff --check通过；既有dirty、原始录音、预编译库删除等不清理。

## 核心证据身份

| 项目 | SHA256 |
|---|---|
| RECIPE-v16 | 61ec159f25c481a73834ef1cf36765287aa63971facc8c4e65d4071c93ed02f8 |
| fresh-default-v16 build | e1674b86d2824e6d9fcc8196aa65b25be7417a4c087c97b76d91fbe4590b1770 |
| v13未可行模型 | c7181c756d95e56aa534fc1efbf1022074b494e3b9078c4fee763ad071155049 |
| v14冻结模型 | 6c38149139f0e87bf654b4c0b1b257c8b42643ea3cbdb15882a4c9bf12b4f6be |
| v16候选binary | c5d222ed8949034100b47135caea1f50f329e7f0ade3d07ebc1413f034f388b3 |
| 开发24 | 44c5668fe3634cb48491cf9f66ad1f56d7de25d4045e371fd15f01ae69d612a4 |
| 开发8 | 9408b3727e920b4a72547fc3f8c3edb8dd94660f2887132825920a13521e3b27 |
| 独立24 | 30bb484d5485c6dbf37f5727841aa012d30ad31f056b73667773c7969deb1bf3 |
| 独立资格false | 929cb97b8138b571c86e8e409a1c6e44059a0108df1b9ab0567926a493e19a79 |
| 同窗归因 | 375b6ce0c6d1c826583e49c444344a3ce961736e6d82977d36fb922e53fec443 |
| sanitized24 | a65925c7ea3081f2b7dea58a3f13bb35fc197d3b16e2ea0aa0d332c5ce844cd8 |

## 下一阶段提案与风险

停止同一表/比例调参。下一假设应针对最终PCM投影残差，区别于当前对单位clean-near的局部MSE。
若n为同窗clean-near，y0为baseline PCM，alpha0=<y0,n>/||n||²，约束
||y-alpha0*n||²<=||y0-alpha0*n||² 且 <y,n>>=<y0,n>，在正投影下可保护SI-SDR；
当前保护使用alpha=1，不能替代这一条件。此为代数设计提案，尚未实现或实验验证。
原生AGC driver固定时可研究PCM映射的线性近似，但整数IFFT/round/clamp/OLA误差须单独量化。
新模型保持32开发或明确新的开发边界，并在评分前重新冻结未曝光的speaker/source分离验收集。
ARM定点化/额外IFFT/状态内存、BF同源、制品链接、设备电话与运动噪声仍属独立验收线。
现有累计100m预算内仅收口已完成实验；下一长期阶段需要新预算决定，不伪装成设备回声已解决。
