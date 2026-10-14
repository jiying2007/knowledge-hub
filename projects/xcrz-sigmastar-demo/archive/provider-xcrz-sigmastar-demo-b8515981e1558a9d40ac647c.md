---
id: provider-xcrz-sigmastar-demo-b8515981e1558a9d40ac647c
title: CALL AEC v55 因果复数残余原型：负结果
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b8515981e1558a9d40ac647c.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:b8515981e1558a9d40ac647cd303815dead030a3455363ab5333062420300646
  source_sha256: 8a64b8f88e0821be28cc06719c4858602d9ae6c8840baaf56999e987bda696cd
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b8515981e1558a9d40ac647c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-b8515981e1558a9d40ac647c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 日期：2026-10-11。logical_task_open=true，严重持续远端自回声仍未解决；best_verified_candidate=v52，candidate_registration=false，complete_solution=false，shipping_approved=false。本轮未修改产品v54原生接入、默认开关、上层协议/订阅/reader/lease，未commit/push/deploy。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: b8515981e1558a9d40ac647cd303815dead030a3455363ab5333062420300646
---

# CALL AEC v55 因果复数残余原型：负结果

日期：2026-10-11。logical_task_open=true，严重持续远端自回声仍未解决；best_verified_candidate=v52，candidate_registration=false，complete_solution=false，shipping_approved=false。本轮未修改产品v54原生接入、默认开关、上层协议/订阅/reader/lease，未commit/push/deploy。

## 结论

v55 固定因果复数残余抵消在开发32例及第一组24例中增加消回声收益，但第二组24例出现双讲损害，按原标准拒绝。80例均是已暴露数据，不属于新盲验收；因出现明确反例，未继续其余224例，也未运行新独立验证或原始16组录音。v52最佳候选仍以原280例6.990870128375964%和首次24例7.147363458997817%等量片段残余能量比例平均为依据；不能将v55已跑80例平均与v52全体结果混比，不能宣称全局最优。

## 实际机制与边界

只新增 Host 测试适配器：在冻结v52后，读取对应NN上一帧原AEC估计echo和post-AES X；H=EMA(X*conj(E))/EMA(|E|²)，固定alpha=1/8、历史至少8个允许学习帧、|H|≤1、固定1/2抵消、上一时刻模型先应用后更新。稳定CALL、当前/前参考都active、上一Feed原Activity DTD far/noncandidate/nonactive及原始mic/echo coherence≥8帧才允许，双讲禁止学习/应用，参考消失/场景切换/Reset清历史。保持原生NN IFFT的AGC driver和原gain轨迹。推理无clean targets、未来样本或在线重拟合。每bin浮点能量与范围检查拒绝增强或非有限输出，20,000个极端/随机数学合同通过；这是已测范围，不能视为整数域能量比较的穷尽证明，下一原型须用uint64比较量化后的能量。

## 验证

- 三个独立实际C构建：identity、candidate、ASAN/UBSAN合同，均exit0。实验链接冻结native static cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532，避免重复启用v52原生候选。
- 20,000数学边界；identity 3轮真实CALL/VOICE/无参考/Reset逐点PCM；candidate VOICE与无参考稳定段逐点PCM；原AGC参数及hash、owner释放通过。测试代码有ASAN/UBSAN，冻结native静态库没有全量instrumentation。
- 实际开发24+8例identity：除新增complex_residual元数据外，全部评分和原观察元数据严格一致；不是仅比较打印出来的六项delta。
- 新complex_residual_audit工具从现有评价器--trace-frames读取实际整数PCM的逐帧energy和target dot，按固定512样本延迟窗口重算未舍入far/双讲/target指标。每组绑定四轨、split、评价、binary与trace，复验native frontend和previous DTD逐帧状态完全一致、AGC gain hash与driver frames不变、显式near-only所有指标一致、原全部削顶计数不增。
- 新工具从/tmp运行help/dry-run；5个定向单测通过。完整Python回归166项，7.207秒，无skip，exit0；预期负测试的diagnostic不代表套件失败。
- 主仓与独立aispeech子仓git diff --check均exit0。
- v54 Host candidate、Host disabled、ARM candidate三个build各185项原绑定源码/头文件再次SHA复核无漂移，三个shared library完全保持原SHA；没有重新安装设备或真机性能/听感证据。

## 四组精确结果

| 已暴露组 | 例数 | 等量片段远端残余能量平均降低 | 双讲最差delta dB | target最差delta dB | 原保护 |
|---|---:|---:|---:|---:|---|
| development24 |24|8.801689270038223%|-0.01126882776386573|-0.0898591900163642|PASS|
| development8 |8|7.78976309661765%|-0.07718268936032135|-0.1476230984668717|PASS|
| exposed24 |24|7.251590518947364%|-0.07065926383084076|-0.1835613643319089|PASS|
| expanded24 |24|7.705574492251489%|-0.11362095169432962|-0.062040994416606356|FAIL|

双讲具体反例：fileid503 delta=-0.11072915185313725dB；fileid554=-0.11362095169432962dB，均低于-0.1dB。远端最差保护≥-0.1、target≥-0.2、near-only与clipping/AGC其余规则通过。这四组far mean分别0.4263615910058515、0.3690481974915435、0.3370855281881236、0.35956519669130366dB，均未达到原完整门槛0.5dB。平均收益不能覆盖个例人声退化，禁止降低门槛接纳。

## 可复跑与证据

BUILD-v55-development.json 保存三个完整编译命令、开发identity/evaluation/audit命令及源码/模型/冻结库/binary SHA；最终BUILD-v55.json增加已跑四组完整审计、输入与trace绑定、166测试和v54新鲜复核。原型candidate SHA70ff9779ace3a11f6cc3e13f363fbbf57a3878b7c8b6d5c35acd4bbe93455724。元数据明确version55与独立复数机制，不借用旧固定标量model的registry资格。全部raw audio、trace、binary仅为本地证据；知识归档只包含此脱敏结论与身份摘要。

## 下一步

PLAN-v56.md冻结一个独立几何假设：保留现有输出相位，只扣除H E在X方向上的非负投影，仍固定alpha/半强度/DTD/coherence和原AGC driver，增加精确整数能量检查与原floor约束。当前只有计划，尚未写代码/构建/评分，不声明反例已修复。必须先合同与开发32例，再复验503/554所在完整已暴露组；失败停止该机制，不扫阈值，不启动盲验收。只有全既有304例保护通过后才组织新的冻结独立验证与原16录音回放。

