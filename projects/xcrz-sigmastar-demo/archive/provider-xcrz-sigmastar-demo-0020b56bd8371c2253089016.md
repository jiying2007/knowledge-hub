---
id: provider-xcrz-sigmastar-demo-0020b56bd8371c2253089016
title: CALL 回声继续优化：配对实验与恢复复验
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-0020b56bd8371c2253089016.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:0020b56bd8371c2253089016fb9522a027254e628cae79fbd63266a613e10134
  source_sha256: 6c0cb047943280d9054bebd392bac9ff0f4bd9ff16db75c3a29e7353bc41d321
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-0020b56bd8371c2253089016.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-0020b56bd8371c2253089016.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 状态：`needs-fix`。用户授权提高预算并继续算法优化。本轮进一步验证独立滤波器、共享尾链、参考时序和 AES 倍率；没有通过近端保护要求的新产品默认值。设备上的持续明显回声尚未闭环，不能用离线能量下降宣称解决。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 0020b56bd8371c2253089016fb9522a027254e628cae79fbd63266a613e10134
---

# CALL 回声继续优化：配对实验与恢复复验

状态：`needs-fix`。用户授权提高预算并继续算法优化。本轮进一步验证独立滤波器、共享尾链、参考时序和 AES 倍率；没有通过近端保护要求的新产品默认值。设备上的持续明显回声尚未闭环，不能用离线能量下降宣称解决。

## 输入与验收边界

- 两轮 `vocaltest_rpm240` / `vocaltest_rpm480` 共 16 场景，原始 MIC、原始 REF、实际使用 REF、设备 output、PTS/seq/epoch 和文件哈希均经过验证。这些采集实际为 VOICE；CALL 是实际 SEVC 算法离线重放。
- 公共四轨真值采用 `evaluation-split-v1.csv` 的全部 24 组与原定 nearend_scale，固定 CALL 512 点算法延迟。输入音频、近端目标和评分窗口不随候选调整。
- 原始设备数据的远端总输出能量下降同时包含噪声、AES、NN、AGC 影响，不等同纯 AEC ERLE。近端及双讲质量以独立真值结果另行约束。
- 保留上层接口、reader、订阅和已有 profile 生命周期；本轮未部署设备、重链 ARM 应用、提交或推送。没有新增端侧采集作为前置条件。

## 本段新增实验

| 候选 | 四个设备远端场景相对基线的总能量衰减变化 | 24 组真值双讲最差 SI-SDR 变化 | 结论 |
| --- | --- | --- | --- |
| 独立完整基线/两抽头尾链，基线 DTD + attack + 最近两帧保护、PCM 一帧渐变 | +0.446～+0.659 dB | -0.026 dB | 保住强双讲反例，但公共远端均值仅 +0.016 dB，且运行两套 NN；仅 Host 诊断 |
| 两套 AEC、单 AES/NN/AGC，在 AES 前按独立基线控制状态选残差 | +0.580～+1.087 dB | -0.353 dB | 额外内存 35168 字节；共享尾链历史仍退化，撤除 |
| 独立 AEC/AES、单 NN/AGC，NN 特征始终来自基线 AES | +0.340～+0.591 dB | -1.083 dB | 保住 fileid 27/112，但弱双讲 fileid 18 失败，撤除 |
| AES CALL 单讲倍率由 2 改 1.5，保留 floor/DTD | +0.043～+0.329 dB | -0.264 dB | 弱近端代价明显，撤除 |
| 原算法，参考由 raw ch0 重建为 delay=0 | -1.036～-0.485 dB | 不改变公共输入，未作跨输入质量比较 | 设备远端全部退化，保持 HDI 配置 |
| 原算法，参考由 raw ch0 重建为 delay=16 | -0.180、-0.115、-0.116、+0.213 dB | 同上 | 无稳定收益，保持原 20 点配置 |

独立候选分支的校准对照使用两抽头旧构建，24 组公共远端 ERLE、近端单讲 SI-SDR、双讲 SI-SDR、相关性及削顶的差值均为 0。旧 evaluator 缺少新增投影电平字段，使通用比较脚本在显示 delta 时返回 KeyError；该次记录仅用于上述共有指标的校准，不能称整个比较工具通过。比较工具现已将完整指标计算放在成功结果文件写入前，缺字段不会产生成功报告。

其余前序候选（复数相干、中心化功率包络、Activity 限时冻结、NN 前后 NR、AEC 当前误差归一化、较快 diag 衰减、Speex AEC/RES）详见同目录 PLAN.md，均未采用。旧证据文件没有覆盖。

## 已建立的事实及局限

1. 默认 `SEVC_AEC_DTD_FREEZE=0`；默认冻结不是已经证实的根因。
2. 原始使用参考是 raw channel 0 延迟 20 点。四组一秒窗口主要相关峰位于 MIC 相对 used REF 的 -3～-6 点，说明主要路径比 used REF 早；但原 SEVC 的 delay=0/16 对照不带来稳定改善。因此不能把 Speex 对时间参考的敏感性直接推广为当前 SEVC 的 HDI 默认修改。
3. 基线 AES DTD 对 fileid 27/112 双讲覆盖为 1.0，但对多数公共远端单讲也持续触发，对弱双讲 0/16/18 又有漏检。它不能单独承担新的单讲强抑制或长滤波器选择策略。
4. 完整独立分支的保护效果不能直接替代共享 NN/AGC 分支的验收。共享尾链候选的反例说明，回退前端输入后，历史状态仍影响当前输出；本轮尚未将 NN、输出重叠与 AGC 的各自影响进一步单独归因。
5. CALL/VOICE 的设备主观回声、实际安装制品身份、SSC305 CPU 和调度未在本轮核验；这些不由 Host 重放或 Host 构建替代。

## 恢复与新鲜复验

- 实验产品代码、宏、私有字段全部撤除。逐项核对实验前 `restored-host/build.json` 的产品 C/header SHA256，与当前源码全部一致；只有 Host replay bridge 的预期诊断功能有差异。
- 当前重新构建 `fresh-restored-final`：69 个 Host 编译单元（68 产品 C + 1 测试桥接），实际 Makefile flags，shared link 使用 `--no-undefined`。
- 新静态产品库与实验前静态库 `cmp` 完全一致。SHA256：`70b002d6eb55236abf9f4183e8061dc43e36a2288b840803a307c48b27683c28`。
- Host replay shared library SHA256：`b397789f60060ebe7dc5ee172ffc76be19011a5adbbd46bef465e644d71423f7`。
- 新 `build.json` SHA256：`b65b0036253b9845ea8b4c409b1ef9708412e48db317535ad1ac5173511d3fec`。
- 全部 16 场景 × VOICE/CALL 共 32 个输出 SHA256 与实验前基线完全相同，配对输入的 7 文件哈希一致，削顶和 ready 状态回归保持原行为。
- 1000 轮切换：2000 次 committed transitions、40013 次 callback、generation=2002，PASS。
- CALL Reset 返回 INTERACTION、清全部 AEC 抽头：PASS；公开投影头/现有 SEVC ABI：PASS。统计 ABI 232 字节，默认内存 308308 字节。
- Capture/replay 契约 16 项、echo-model probe 4 项：共 20 项 PASS，包括反事实 delay dry-run 不改输入/不写输出、非法 delay 在加载库前拒绝。
- AISpeech `git diff --check` 通过。所有本轮构建与重放写入隔离证据目录；根仓现有库、镜像、其他模块 dirty 状态不作本轮来源声明。

## 留下的源码产出与运行环境修复

- Host-only 双尾链 adapter 和独立 replay 入口用于复跑上述保护假设；默认构建没有双引擎或 Speex 依赖。桥接统计明确为基线控制状态，不能当作混合输出的全部阶段统计。
- `device_replay.py --reference-delay` 显式记录反事实和实际采集延迟，默认不修改参考；反事实模式禁用与设备 recorded output 的等价比较。只更改内存输入，原始采集七文件不写入。
- 前序只读归一化观察、原始 held-out 可预测回声分析和系统 Speex 对照工具保留，作为诊断入口。
- 用户明确授权“清理 tmp”后，删除当前用户拥有、无打开进程的六个旧 pytest 临时目录，释放约 1GB；没有清理其他用户文件、现有音频证据或 raw 数据。根分区可用空间由 0 恢复，Codex SQLite 与运行策略读取恢复。

## 下一条可验证的实现路径

优先保持基线完整输出状态，再研究独立候选的低成本输出分支：基线 AEC/AES、NN 特征与延迟、输出重叠及 AGC 历史均需要保持；候选不能只回退当前残差而共用已经改变的历史。先用 Host 独立输出对照验证弱双讲 18、7、35 和强双讲 27/112，再扩展全部 24 真值与 16 原始场景，并评估计算和内存代价。不得将双 NN 诊断的保护结果直接认定为单 NN 产品通过。

该方向是待验证方案，不是已证实的设备根因或已完成的优化。当前状态保持 `needs-fix`，没有产品默认值变更。
