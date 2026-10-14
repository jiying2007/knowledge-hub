---
id: provider-xcrz-sigmastar-demo-da6450a639df9a0b35b1b6e9
title: 参考独立 aec/src 的 CALL AEC 对照与修复
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-da6450a639df9a0b35b1b6e9.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:da6450a639df9a0b35b1b6e92f36db4796225c03615ddae8202c010c003d7c63
  source_sha256: 86aa007df06106c04b8ae8b232fa887c8c09f7d01d4fbc137b9462988a318ea4
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-da6450a639df9a0b35b1b6e9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-da6450a639df9a0b35b1b6e9.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 状态：reviewing / needs-fix。源码参考与本阶段实验已完成；持续明显回声的总目标未完成。未修改现有主链默认参数、上层协议、reader、订阅、profile 生命周期或设备参考延迟。未部署、未重新链接
  ARM 应用、未提交或推送。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: da6450a639df9a0b35b1b6e92f36db4796225c03615ddae8202c010c003d7c63
---

# 参考独立 aec/src 的 CALL AEC 对照与修复

状态：reviewing / needs-fix。源码参考与本阶段实验已完成；持续明显回声的总目标未完成。未修改现有主链默认参数、上层协议、reader、订阅、profile 生命周期或设备参考延迟。未部署、未重新链接 ARM 应用、未提交或推送。

## 实际链路与可借鉴机制

当前 SEVC 主链调用 SEVC_AEC_New/Feed，没有调用独立 aec_api_*。旧 AEC 实际构造入口 sspe_aec_config_Init 的参数与 aec_api_paramSet 不能混用。其 frame=512、FFT=1024、4 个分块对应128ms，具有预加重、参考协方差、约束梯度及 NAES/NLP。当前 SEVC frame=256、FFT=512，VOICE2/CALL1，直接在窗口化频谱上更新权重。

可以借鉴长尾建模、因果覆盖检查、约束更新和残余回声估计的机制；不能直接搬运旧实现的 Q 格式、FFT尺度、窗、正则项和权重。当前是单参考，双参考解相关不是本阶段优先方向。旧 AEC 的分块卷积约束与 SEVC 的窗口化频谱滤波不等价。

## 对照方法与结果

固定两轮16组设备原始采集的七文件哈希、全部24组公共四轨真值、nearend_scale和评分窗口。每组有配对基线。设备采集实际为VOICE；CALL为真实算法离线重放。设备指标是整链输出总能量衰减，包含噪声、NLP/AES、NN、AGC，不能称为纯线性AEC ERLE。公共ERLE也使用完整候选输出，阶段指标按实际统计边界解释。

| 实验 | 四个设备远端单讲相对原CALL的总衰减变化 | 公共远端ERLE平均变化 | 公共纯近端SI-SDR最差变化 | 公共双讲SI-SDR最差变化 |
| --- | --- | --- | --- | --- |
| SEVC权重硬因果投影 | -14.105 / -11.953 / -13.880 / -11.360 dB | -1.550 dB | 0 | -12.834 dB |
| 旧AEC，关闭NLP | -19.466 / -17.915 / -19.089 / -17.280 dB | -3.965 dB | -1.453 dB | -13.773 dB |
| 旧AEC，修复后开启NLP | -1.509 / -0.439 / -2.756 / +0.539 dB | +0.373 dB | -1.453 dB | -12.039 dB |
| 旧AEC+NLP，麦克风延迟16点 | +3.400 / +4.158 / +5.767 / +4.163 dB | +0.502 dB | -1.341 dB | -9.915 dB |
| 旧AEC，无NLP，麦克风延迟16点 | -8.973 / -9.174 / -5.745 / -7.690 dB | -3.461 dB | -1.341 dB | -13.548 dB |

四个设备场景顺序为rpm240 far、far-motion、rpm480 far、far-motion。所有有效候选均完成24真值和16场景两profile；输出削顶为0。硬投影已撤回。旧后端只保留Host适配器，没有晋升产品。

16点补偿的假设来自原始麦克风相对usedREF主相关峰领先3～6点：旧因果滤波器可能缺少这部分覆盖。实验只在Host内延迟mic1，未改原文件或参考；C和Python评分延迟从1280明确增加至1296点。VOICE仍直接使用原主链，16个输出完全相同。

在关闭NLP的配对对照中，16点补偿较同一旧后端无补偿提高10.493 / 8.740 / 13.344 / 9.591dB；开启NLP又较补偿后线性版本增加12.372 / 13.332 / 11.512 / 11.853dB。因此时序补偿有明确关联收益，最终衰减还强烈依赖额外抑制；不能据此宣布当前SEVC的时序是回声根因，或把能量下降都归为线性滤波提升。之前原SEVC参考delay=0/16对照没有稳定收益，HDI20点设置保持不变。

所有旧后端都未通过近端/双讲保护。旧NLP+16点的公共双讲目标投影电平最差还下降4.587dB，不能仅看远端平均收益。当前不采用整条旧后端，也不继续同类盲调。

## 两个实际缺陷与最小修复

1. 独立旧NLP原版在公共fileid4和完整顺序设备重放中发生SIGFPE。完整顺序GDB回溯定位aec_emdProcess的误差归一化，参考功率和+正则项可能为0。两条实现分支增加正分母判断；无效分母的参考消除贡献置0，正分母保持原式。强制无参考NLP回归通过，修复后完整顺序不再发生该异常。
2. 旧FFT仅编译一个长度对应的旋转表，512点构造在当前1024点配置下原先返回了twiddles=NULL的engine，第一次FFT会SIGSEGV。构造入口提前拒绝非编译长度，返回NULL；已校验1024点正常构造与512点拒绝。这是旧独立AEC的API安全修复，不是当前设备主链的故障归因。

保留的产品改动只有aec/src/aec.c和aec/src/AISP_TSL_fft32.c中的上述保护。旧AEC其它数值边界、Reset的VAD hangover和全局内存池没有获得完整产品资格；本报告不作全面安全声明。

## Host适配器与证据边界

适配器使用旧AEC单麦mic1/单参考，再送入SEVC CALL尾链，原生参考置零。旧AEC512点延迟+256点分块+512点尾链合计1280点（80ms）；16点补偿后为1296点（81ms），现有CALL为512点（32ms）。这不是无成本替换。

SEVC arena默认旧适配器为311412字节，不包括独立的1024000字节全局内存池和其它旧堆分配。frontend stats描述之后的SEVC，不能把其AEC零值解释为旧AEC消除量。新增显式diagnostic backend、memory/stats边界和mic延迟字段；未知诊断行、失败子进程、错误后端或多份JSON仍拒绝。内存地址在持久化诊断中脱敏。

具体结果：supervised-causal-weight-call.json、supervised-legacy-aec-linear-call.json、supervised-legacy-aec-nlp-guard.json、supervised-legacy-mic-delay16.json、supervised-legacy-linear-mic-delay16.json；对应replay目录中的results.json绑定全部原始输入和输出。无效配置、最初JSON诊断解析失败和SIGFPE中断目录不当作成功质量证据。

## 新鲜默认构建与验证

- fresh-default-v4-final：默认宏为空，69个Host编译单元；source_identity全部169项核验无漂移。
- shared SHA256：`1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe`。
- static SHA256：`cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532`。相对v3静态库存在两处旧AEC对象修复，不宣称整个库恢复为旧hash。
- build.json SHA256：`6f0eb1f6af8acba76579d64d545bc5013fb0170f1f534488e9295a1066815cec`。
- fresh-default-v4-final-replay完成16场景×VOICE/CALL共32输出，与v3默认基线PCM SHA256全部相同；配对七文件输入全部相同。当前主链sevc C/header相对v3恢复锚点无变化。
- 当前25项Python工具契约通过。Makefile新增run-legacy-aec-calibration和run-aec-fft-probe；无参考NLP、错误FFT长度、旧AEC脉冲512点/9998电平、mic延迟环与FFT往返512尺度校准通过。FFT脉冲最大误差1536/2^24。
- arm-legacy-safety-v2使用明确的SigmaStar glibc11.1交叉gcc和实际模块recipe，两处修改各生成ARM EABI5对象，退出0。已有PSHR64重复宏警告仍存在。首个只指定ARCH=arm的目录实际使用cc生成x86对象，已排除，不作ARM证据。
- 根仓与独立AISpeech仓git diff --check通过。前序1000次切换、Reset/ABI的记录见REPORT-v2，本段不声称重跑这些未受影响的生命周期测试。未链接ARM库/应用，未做设备/HIL或CPU/资源资格。

工具身份：device_replay.py `5b53e90a9742dda796841e267ab3dc5055599171e062a8eeaedfe0a0ae085e67`；supervised_compare.py `7c7352e6984b5347177a42eb98d70055198af8876be4e3a6e68447fd007a98f9`；isolated_build.py `b80414abd3216ddacf25ae5ba5e419e624dbc91e83a711555c4bed6be5f51441`。

## 后续重排

本阶段证据支持参考aec/src继续设计，而不支持整条替换。下一原型应将低延迟分块滤波、参考因果覆盖与现有AES/NN边界分别验证：先确保原始mic、线性residual、echo estimate同源、同窗、同尺度，再评价近端/双讲及资源。完整旧后端可作方法参照；当前不能以其额外NLP衰减取代双讲保护门禁。持续回声总目标继续保持needs-fix，不伪标完成。
