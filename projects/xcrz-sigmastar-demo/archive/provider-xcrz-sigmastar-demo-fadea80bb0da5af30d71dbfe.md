---
id: provider-xcrz-sigmastar-demo-fadea80bb0da5af30d71dbfe
title: CALL AEC v56：保留相位原型未通过双讲保护
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fadea80bb0da5af30d71dbfe.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:fadea80bb0da5af30d71dbfed27bcbf1745398fb21c07aeeb87a307e868a4cd6
  source_sha256: 81ed3bbc9d394a4a09cc5910d98ea9e9bd0bc70c8fd27eb895905d0284b5864f
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fadea80bb0da5af30d71dbfe.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-fadea80bb0da5af30d71dbfe.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 主目标仍开放：严重、持续的远端自回声没有完全解决。当前最佳已验证部分候选仍为 v52；默认关闭的 v54 原生接入、上层协议/reader/订阅/lease 未修改。v56 不进入原生链路、不替换已有候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: fadea80bb0da5af30d71dbfed27bcbf1745398fb21c07aeeb87a307e868a4cd6
---

# CALL AEC v56：保留相位原型未通过双讲保护

主目标仍开放：严重、持续的远端自回声没有完全解决。当前最佳已验证部分候选仍为 v52；默认关闭的 v54 原生接入、上层协议/reader/订阅/lease 未修改。v56 不进入原生链路、不替换已有候选。

## 决策与结果

v56 冻结为 v52 + 因果残余传递估计，应用上一估计后再学习当前帧；alpha=1/8、最低8帧、H模≤1、固定半强度。变化是用 HE 在 X 方向上的投影得到标量 lambda，沿旧输出方向减少幅度，整数舍入后用 uint64 严格保护功率上下界。它不使用 clean truth 推理，不改旧模型/产品默认。

已实际评分并按整数 PCM 每帧能量及目标点积重新审计 **136例、7组**，不是完整304例。所有已有数据已暴露，不能称blind。

| 分组 | 例数 | 远端单讲输出能量平均降低 | 最差双讲 SI-SDR 变化 dB | 保护 |
|---|---:|---:|---:|---|
| development24 | 24 | 8.769130% | -0.010842553 | 通过 |
| development8 | 8 | 7.740442% | -0.065367524 | 通过 |
| expanded24 | 24 | 7.698772% | -0.091171876 | 通过 |
| expanded8 | 8 | 6.192813% | -0.020449119 | 通过 |
| exposed-failed24 | 24 | 8.538542% | -0.062502427 | 通过 |
| exposed-new24 | 24 | 6.628198% | -0.110957453 | 失败 |
| exposed24 | 24 | 7.271107% | -0.066306628 | 通过 |

fileid **508**：far +1.2074855641810178 dB、double **-0.11095745273832414 dB**、target -0.00344044324157923 dB；越过原冻结 double ≥-0.1 dB 门槛，v56被拒绝。已排队的同批 exposed-failed24 完成后停止，其余168例未运行；没有更改门槛或扫描强度来挽救结果。

上一轮v55失败的503/554在expanded24组本轮已回到保护范围（最差-0.09117187620690892dB），但不能仅根据修复原反例宣布新方案通过。所有7组完整far均值≥0.5dB门槛也未满足。

## 验证与边界

3个实际Host构建退出0；ASan/UBSan合同覆盖20000极值/相位/整数floor/因果warmup数值案例，以及每种模式1500帧 CALL/VOICE/reference-loss/Reset/owner清理和原AGC状态。插桩只覆盖新增适配器/合同，旧静态库未插桩。透明模式32例的所有原指标及旧观测元数据逐项相同，would-apply 366767 bins证明路径实际工作。新增审计负例3项、全部Python回归 **169项/7.691秒/0 skip/exit0**。从/tmp的help与dry-run成功，dry-run writes=false；父仓和独立AISpeech仓diff --check均exit0。

7份实际审计的全部binary/evaluation/split绑定、272份trace与544份输入轨绑定在收口时重新验证；trace是实际整数PCM每帧统计，不是逐sample PCM存档。新4份源码、3个binary、计划与证据均绑定SHA256。v54的Host开启/关闭及ARM三份build各185份source/header、共享库与静态库身份重新检查无漂移；不表示v56已经ARM构建或设备运行。

原v52仍以同一280例6.990870128375964%、另24例首次验证7.147363458997817%的既有结果为最佳部分候选，两份registry身份本轮重新核对。它们不是新评分，也不能证明完全消回声。原录音16份无独立干净近端目标，设备持续听感仍未具备。

## 下一步假设

508实际trace中，offline标注为double的237帧有34帧的previous-DTD valid/far且无candidate/active保护。仅作离线诊断，不证明每个bin误抑制，不把truth用于算法。保留相位并不足以保护全部双讲；现有 DTD + mic/estimated-echo 相关性可能在近端存在时仍允许额外衰减，这是待验证假设。

v57计划增加独立原始播放reference相关性：参考频谱与NN同源上一帧严格对齐，以因果历史连续相关置信度限制额外投影，不新增hard阈值、不扫比例、不更改v52或native默认。先验证不改变输出的identity和时序/AGC/Reset，再开发32例、完整136反例及全304；全保护通过才进入新的独立验收/原16paired replay/资源/原生接入。具体冻结契约在PLAN-v57.md，尚未实现。

本报告只记录本项目Host负实验和可复跑证据；complete_solution=false，shipping_approved=false。不执行commit/push/deploy。
