---
id: provider-xcrz-sigmastar-demo-fedf6467f331651fdc2c6922
title: CALL AEC 当前最佳验证候选 v52 与原生受控接入
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fedf6467f331651fdc2c6922.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:fedf6467f331651fdc2c692227a0ad7ff6c14a7c4b4b093df613ef9c42211c69
  source_sha256: 7120d32d03451748208afebab2fb89cd70af857dcb34dac6b520c48154efdfd2
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fedf6467f331651fdc2c6922.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fedf6467f331651fdc2c6922.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 状态 reviewing / needs-fix。严重持续远端自回声仍未完全解决；完整方案和 shipping 均为 false。本轮只选择已测安全候选并完成原生受控接入，不宣称全局最优。累计授权 250000000 Token、172800
  秒，起点没有重置，截止 2026-10-11T14:56:57Z。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: fedf6467f331651fdc2c692227a0ad7ff6c14a7c4b4b093df613ef9c42211c69
---

# CALL AEC 当前最佳验证候选 v52 与原生受控接入

状态 reviewing / needs-fix。严重持续远端自回声仍未完全解决；完整方案和 shipping 均为 false。本轮只选择已测安全候选并完成原生受控接入，不宣称全局最优。累计授权 250000000 Token、172800 秒，起点没有重置，截止 2026-10-11T14:56:57Z。

## 同组比较与首次验证

固定 v52 表由已冻结 v44 与原生 Q20 anchor 按 3:1 派生，逐系数 ties-to-even，不扫描比例、不改变保护阈值。其模型 SHA256 e5cac3253810541f48a937542c9df86cf4c32e1d71d48af95115631dc099f30f。不是把实时 NN 增益简单乘 0.75。旧 v46 派生仍字节一致。

| 数据 | v46 远端输出能量平均下降 | v52 远端输出能量平均下降 | 原保护 |
|---|---:|---:|---|
| 相同 280 例、13 个已暴露 cohort | 4.972220537832237% | 6.990870128375964% | 两者通过 |
| 评分前冻结的另 24 例首次验证 | 5.116837134371296% | 7.147363458997817% | 两者通过 |

百分比按逐 clip 能量比的等权算术平均，不是总能量汇总比例，也不是已听感证明的回声消除比例。280 例 v52 每 cohort 收益 5.742135836375272%～8.302648987892068%；新 24 四声学组 3.878687555723428%～13.9479989178147%，均超过预冻结次级优化每组至少 1% 规则。新 24 现在已经暴露，不能再次称盲测或未评分。两份 registry 分别审计 280 和 24，没有伪称新建完整 304 registry。

v52 在 280 例中的 far / double-talk / target 最差变化分别 -0.0687596189432611 / -0.06485060496218376 / -0.147717777088068 dB；新 24 分别 +0.020510819263947155 / -0.06133656188417724 / -0.15727219974897944 dB。原 far 和双讲逐例最低 -0.1 dB、target 最低 -0.2 dB、near-only、内部/最终削顶、AGC 保护全部保留。新 24 far mean +0.3525589050137666 dB；完整每 cohort far mean 至少 0.5 dB 规则仍失败，不能宣布完全解决。

Public 数据使用固定 Microsoft 官方 train partition；本轮 speaker/clip 排除 280 暴露例，96 轨/WAV/hash 全核验。底层 vendor NN 预训练独立性未知；不是官方挑战成绩或设备声学资格。

## 设备原始录音上的离线结果

用户两轮 rpm240/rpm480 共 16 份原始录音继续保留，七文件/PTS/epoch/reference 延迟身份严格核验。v52 重放生成 64 份配对 WAV；所有 32 个原生控制与旧原生库逐点一致，所有 16 个 VOICE 候选也一致。CALL quiet/near/motion/near-motion 共 8 份逐点不变，削顶没有增加。

| 场景 | CALL v52 相对原生总输出能量变化 |
|---|---:|
| rpm240 far | -0.8051521315006531 dB |
| rpm240 far-motion | -1.0786214171369248 dB |
| rpm480 far | -0.61167058168516 dB |
| rpm480 far-motion | -0.5641651547213733 dB |

四份双讲总输出能量变化 -0.05524416515044234～-0.1259324018326125 dB。录音含噪声且缺独立近端/纯回声真值，这些不是正式 ERLE 或人声损伤比例。没有本轮持续远端人工听感、设备安装或实时运行证据。capture-listening-v52/results.json SHA256 4a75b3115c15542633a12d7c1c933b0a5cc67f41f017db1d63e5ca47ab691fba。

## 原生受控实现与接入一致性

新增 SEVC_CALL_RESIDUAL_CANDIDATE 宏，默认 0；开启后固定模型静态编译，echo/rawmic1 与 NN 前一帧 FIFO 对齐，保留 reference/稳定 CALL/quiet bypass/Activity DTD gate。状态由每实例 arena 分配；没有训练、文件 I/O、逐帧 malloc、新线程或全局 owner 表。原生 NN/VAD 驱动原生 AGC，候选 PCM 使用同一原生增益；没有改上层 reader、订阅、lease、协议或请求方式。

新原生开启构建在 304 公共例的实际整数 PCM 与 16 原始录音上逐点匹配冻结 v52；全部公共显式 near-only 逐点匹配原生，AGC gain trajectory 与非 clip 前端状态一致。新关闭构建与旧原生原始重放的 PCM/stats/gain 一致。原生 parity 报告 SHA256 1f288c27af93b92132f5758857bbaf95816c2a5af85e2eac6a8871dea08a7d93；输出后重新核验所有绑定身份通过。

12 轮 CALL→VOICE→Reset 的 5520 帧前端/AGC 状态比较通过；2592 帧 VOICE 和 840 帧 reference 消失后的 CALL 逐点一致。默认 Reset 保留旧 overlap，VOICE 明确等待两帧历史排出，未将首帧旧 CALL 历史误报为缺陷或强行清掉既有行为。原生 Reset 测试另逐字节核验候选状态清零；独立 NR/NN transition 和公共 API smoke 通过。lifecycle 报告 SHA256 04c36a558345ffa687fc76ae27f919d932902916a2d31efe84fb96c55d7a6cec。

20000 组极值/随机特征及历史运算与冻结 Host 数学实现逐项一致，ASan/UBSan 无失败。161 项 Python 回归通过，无 skip，7.566 秒；旧可选 stage/capture 测试使用显式冻结二进制，新原生测试分别执行。原生 vendor archive 未整体 sanitizer 插桩，不由测试代码插桩推导全库无缺陷。

## 构建与成本

Host 开启/关闭、ARM 开启均按实际 build/build.mk/lib.mk 各编译 69 单元（68 原生+测试 bridge），静态库只含原生 68 单元。每份 build.json 绑定 185 源码/头身份；本轮结束再次核验现有身份全部匹配。

ARM 实际 configs/current.configs SHA256 23687bf8378205c614e49740428bb7d259585504659da3cd49b1c21f99da7890，SigmaStar glibc arm-linux-gnueabihf GCC 11.1.0。初次未指定 config 的 dry-run 与工具链别名预检拒绝都排除；正式构建指定已核实绝对编译器，shared/static 成功，readelf 确认 ELF32 little-endian ARM EABI5 hard-float。只证明 ARM 编译/链接，没有 ARM 运行或跨架构 PCM 资格。

Host candidate arena 336092 字节、native 308308 字节，增加 27784 字节。五轮交错测量每 profile 80 帧预热+2000 帧：CALL 线程平均耗时的五轮中位数 216.555→254.266 us/帧，约 +17.4141%；VOICE 103.333→118.608 us/帧，但各轮范围显著重叠且波动，不宣称成本完全不变。首次批次与生命周期重放并行，已排除；报告采用其退出后批次。Host 不证明 SSC305 实时余量。performance-native-v54.json SHA256 dba42f9811a1f9ad6f08d3910658299a5dc5ba98f8310f5c7502bdceb48372c6。

Host 开启 shared SHA256 fd2524fa91ac497b45bb5c66b01aa3463d7958eed8b2763ef015157090dfbb03；static d4a4f9ce753cc32b370a647b4a073bd7c3f3389a0c26f53aa44216b4f5ba8950。
Host 关闭 shared ca84fec264124ef2ebb1770b2147bf8a5be8282602939b120d977e14f742d67e；static bd74a4acd22062dd74845e02c69941ab9827525156b732e623cd0da2fae66e8e。
ARM 开启 shared 587e34c3a602270236a3b43e15cf01fb928a813bd81960deac1fddd65b6abf50；static 6558510cad000c4163fd4c604b4cba43d72fe716d986968833884a7459ed8f6e。

## 当前选择和剩余目标

在相同已测安全集合及首次新 24 验证中选择 v52 作为当前最佳次级候选，替代 v46。主目标 active/open；禁止把原生接入一致性、ARM 编译或 Runtime conformance 当作完全消回声、设备/HIL 或产品放行。

新库未覆盖产品库、未重新链接/安装应用；生产默认仍关闭。所有原 dirty、录音、冻结旧实验保留，没有 commit/push/deploy。源码运行说明在 modules/aispeech/tests/README.md；原始音频、轨迹、库和二进制不进入知识正文或源码提交。

后续优先寻找有独立机理的新改进，同时保持当前 v52 冻结结果和所有人声保护。已拒绝的 DTD freeze、整条旧 AEC、MDF 替换、硬因果投影、压 AGC/弱 VAD 和双原生 PCM 混合不做同类重复盲调。
