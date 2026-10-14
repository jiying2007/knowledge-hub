---
id: provider-xcrz-sigmastar-demo-e818d33540ae257957f7e50e
title: CALL 原生 AEC 权重因果取证 v8
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e818d33540ae257957f7e50e.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:e818d33540ae257957f7e50e551ccd61aec1935143c54ab54e60732fcae3ed5d
  source_sha256: ecc864e972e4ff0f289dafe9febad8f0d2b6667de18f03cc652af1eda07cae42
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e818d33540ae257957f7e50e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-e818d33540ae257957f7e50e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: '日期：2026-10-10。主目标仍为改善持续远端自回声，同时保护近端、双讲和现有业务音频生命周期。 completion_claim: false completion_allowed: false verdict:
  needs-fix / replan root_cause_status: unknown product_candidate_adopted: none'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: e818d33540ae257957f7e50e551ccd61aec1935143c54ab54e60732fcae3ed5d
---

# CALL 原生 AEC 权重因果取证 v8

日期：2026-10-10。主目标仍为改善持续远端自回声，同时保护近端、双讲和现有业务音频生命周期。
completion_claim: false
completion_allowed: false
verdict: needs-fix / replan
root_cause_status: unknown
product_candidate_adopted: none

本轮新增的是可复跑 Host 诊断与负结果。评分窗口实际权重没有触发越界清零、整数溢出或非正分母；不能认定源码中的清零保护造成当前回声。即使用真实近端标签冻结更新，或使用独立纯回声轨学习权重，完整 CALL 也没有得到稳定的远端收益及近端双讲保护。不能宣称设备回声已经改善。

## 范围与实际实现

- 新增 `tests/sevc_aec_weight_observer.h`：AEC 回调中、AES 修改残差前，独立重建最后一路麦克风当前梯度与上一权重的固定点更新；记录清零、数学不一致、溢出、分母、权重及更新能量。保留两个分配 tap 的历史，当前不活跃 tap 不参与 active 系数统计。公共类别切换的 FFT 混合边界归 unknown 桶，仍参与总数和错误检查。
- 修改 Host 阶段探针和公共评价器，显式开启观察器才输出权重统计。默认不写任何算法状态；删除前恢复原始回调及 user 数据。`SEVC_TEST_NATIVE_ORACLE_FREEZE=1` 是另一项真值冻结诊断，使用当前或上一帧 clean-near 类别。
- 新增 `tests/sevc_clean_echo_weight_oracle.h`：第二个原生 CALL 以 clean echo 轨驱动；主帧在 shadow 前进前复制其上一帧权重。主实例继续接收真实混合音频并使用原有 AEC 残差、AES、NN、AGC。没有当前/未来真值权重泄漏。相同混合输入控制先逐帧确认权重与 PCM 相同。
- 新增实际 C 生命周期回归和 Makefile 入口 `run-native-weight-contracts`；增强实际 Python 阶段测试，要求观察器覆盖评分帧及系数，并检查错误计数。
- 本轮不修改生产 SEVC、API、HDI、Sensor、reader、订阅、协议或默认 BF/尾链配置。当前独立 aispeech 子仓及父仓的其他 dirty 保留；没有 commit、push、部署或设备重启。

真值冻结与 shadow 纯回声都依赖设备不可得的独立真值，只用于诊断。shadow 额外 arena 为308308字节，两主实例 arena 合计616616字节；评价器还会短时创建独立 near-only 实例，不能把该合计解释为进程峰值资源。没有 ARM 或设备资格。

## 输入与透明性

沿用 rpm240/rpm480 共16份七文件采集。采集实际 profile 是 VOICE；CALL 是本机实际 SEVC 重放。校验输入 hash、seq/PTS/epoch、窗口和冻结重放；没有改录音、应用参考延迟或补 EOF 尾数据。原始数据没有独立 clean-near 真值。

公共数据使用冻结24对四轨、既有 nearend_scale、参考延迟和 CALL 512点对齐。split SHA为`4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb`。输入类别由clean echo及clean near能量确定，混合FFT边界单列；这些标签不能直接成为设备判据。

16录音观察/无观察/冻结CALL PCM全部逐字节一致，评分窗口22749帧、5846493个当前配置tap系数：数学不一致、清零、梯度/求和溢出、非正分母均为0。
公共24对所有原有指标与未观察基线完全相同；16910个回调帧（含每实例80帧预热）及4469230个当前配置tap系数，上述错误计数也全为0。观察对象是最后一路麦克风，不能称为两个麦克风全部权重的证明。

原始四远端窗口实/虚权重最大约1.38～1.65，公共最大约17.4，未越过20阈值。这里仅排除已观察输入和窗口内实际发生的清零/溢出；未覆盖设备所有音量、启动、环境或长跑。

## 两项因果实验

以下均为24对 candidate-baseline 的完整 CALL 指标差，dB 越高通常越好；目标投影单独保护，不能用平均SI-SDR代替。

| 诊断 | 远端平均差 | 双讲平均SI-SDR差 | 双讲最差SI-SDR差 | 近端目标投影最差差 | 结论 |
|---|---:|---:|---:|---:|---|
| 真值近端存在时冻结更新 | -0.001708 | -0.030292 | -1.658 | -0.760 | 拒绝作为保护方案 |
| clean echo持续学习上一帧权重 | +0.004208 | +0.254292 | -0.177 | -0.767 | 没有稳定完整链收益，不可部署 |

显式near-only指标差都为0，最终削顶计数差都为0。真值冻结会停止路径跟踪，负结果不能证明不存在近端权重污染。clean-echo 对照保留持续学习，但其本身也不代表理想滤波器或绝对理论上限；结论限定为这组数据和这个原生实现。

相同混合输入 shadow 控制的24对每帧PCM、权重以及全部原有指标都与基线相同。它验证实验装置，不认证回声效果。两个 shadow 对照的ASan/UBSan版本完整records与各自O2版本完全相同。

clean-echo 权重对照的线性阶段远端 mic/AEC 能量比平均仅+0.020583dB，双讲平均+0.038167dB；这些阶段比值不是纯ERLE或近端真值质量。file27双讲目标投影从+0.145到-0.622dB，SI-SDR改善从2.124到1.947dB，说明较小的AEC功率变化仍可伴随完整尾链目标损失。当前数据不足以把损失唯一归因于AES或NN，下一轮需要单模块控制。

## 实际验证与制品身份

| 命令/检查 | exit | 结果 | 证据 | 层级 |
|---|---:|---|---|---|
| `tools.codex_assets.call_stage_probe`，native观察器与冻结CALL配对，两个runs | 0 | 16组全部PCM精确相同 | native-weight-captures-v8-final.json | Host真实录音 |
| `tools.codex_assets.supervised_compare`，native权重观察器 | 0 | 24对全部既有指标完全相同 | native-weight-public24-v8-final.json | Host公共真值 |
| 同入口，truth冻结 | 0 | 上表负结果，未晋升 | native-weight-oracle24-v8.json | Host公共真值 |
| 同入口，shadow相同输入及clean echo，各O2/ASan | 0 | identity逐帧PCM一致，clean echo未达保护；sanitizer records相同 | clean-echo-identity24-v8.json、clean-echo-oracle24-v8.json及各sanitized版本 | Host装置/真值 |
| `make -C tests -o host-lib HOST_LIB=<v7-static> AEC_WEIGHT_TEST_BIN=<cache> CALL_WEIGHT_TEST_BIN=<cache> run-native-weight-contracts` | 0 | 720帧VOICE/CALL/Reset与原API PCM相同；观察历史损坏负控制被检出；3实际传输测试通过 | tests/sevc_aec_weight_observer_regression.c、tests/test_call_stage_probe.py | Host测试，测试代码ASan/UBSan |
| `SEVC_CALL_STAGE_PROBE=<v8-final> SEVC_EXPECT_WEIGHT_TRACE=1 python3 -B -m unittest discover -s tests -p test_*.py -v` | 0 | 34项通过，无skip | 当前tests | Host工具/实际传输 |
| `python3 tools/codex_assets/isolated_build.py --output <fresh-default-v8-final> --jobs 4` | 0 | 69单元，174源码头绑定项；43主链项与v7精确相同 | fresh-default-v8-final/build.json | Host源码/制品 |
| 父仓与独立aispeech `git diff --check` | 0 | 无空白错误 | 当前dirty | 源码 |

以上所有shell经rtk。新C观察器、评价器使用与真实库匹配的`AISPEECH_FIXED/NN_FSMN/SEVC_MULTI_CORE/SEVC_COMMUNICATION`宏和私有头，`-Wall -Wextra -Werror`编译。oracle为CALL专用，明确拒绝与其他后端、权重观察器及MIC延迟适配器组合。ASan/UBSan仅覆盖新增测试/观察器代码，静态算法库未整体instrument。
新增生命周期测试首轮使用不存在的VOICE枚举名编译失败exit2，已改为实际`SEVC_TAIL_INTERACTION_NR`，最终构建和回归通过；保留这一失败边界，不能把首次失败记为通过。

shared库SHA：`1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe`。
static库SHA：`cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532`。
两者与v7完全一致。实验O2链接v7冻结库，sanitizer shadow链接v8新鲜库，二者库字节相同。没有替换产品预编译库。

证据SHA：

- build：`0a8764550a505e9b7360b9c3ce7f6d08fbb4f48d421917c723d7d8970e116c0b`
- native public：`f1c4cb33b7dc3aa532d2f71a6b7aeae41293fec2bc215f5de9d365ba568ec87d`
- native capture：`31470ab95ba11dc30c44468ec36e2a342eec91373fd23d702b54e53784d3a60a`
- truth freeze：`1063b6e9e028e7b435e75b9edc308b7b560b4265dbefdef5926bc62de6d954a4`
- identity O2：`165bebb0ff5fa496181968423d469f422151daf6ff7a5c3def0f2de0a416f8c9`
- clean echo O2：`9685cf0247438a198fa7f202e8632f731a3072a7d7e71f0fb2723b4ca9e13246`
- identity sanitizer：`7832124ec3b0692da22b3f5a98f670cfe8c801518a9714a7dc7d28f8893b0906`
- clean echo sanitizer：`39b2c7ad694b49daed179138ad3595e70c8210d640b9c30290e604b51701468c`
- weight observer头：`e756b3cfe45d742b3da64cc0a7226857f3e3daa736d7040871245d639047dcf5`
- observer C回归：`0dde349e3da6822b02d19fd7ce3cd1d254fc20d93aa358d7389a3960fae3b9b1`
- clean echo头：`26edb6d875fd123075b4dc7024506bf2e362c8bea738c7ca968763a9ee33e99b`
- public evaluator：`e36777d3b23b92c3602d90b1b3e8b36fc9dcabb4ee6c33de87d9b824152cd168`
- stage probe：`170e6944fe9f51b9f7b8f93cd87e002effdb21e971fff2d3a53688d9ab5988b1`
- Python阶段测试：`07cca824d4acba1cca61e9ac3fed51efed75a0e462f98995960fc75b6348e0a1`
- Makefile：`5b73181b834f33ed789ccf133945e254ddef14b45d463343d1ae98405f92862f`

## 审查与完成声明

primary_skill: adk-systematic-debugging
supporting_skills: adk-planning-execution-loop, adk-verification-before-completion
claimant: root
verifier: 独立固定点数学重建、真实未包装API、混合输入identity负控制及冻结真值配对评价。
reviewer_independence: 自动数值控制独立于候选意图；没有独立人员审查，不冒充owner review。
completion_guard: 新增诊断和默认Host验证通过；主声学收益、ARM资源及设备听感缺失，整体needs-fix。
Subjective Feature Proof: 设备远端听感未采集，本轮不能确认改善。
Replayable Evidence Bundle: JSON绑定输入、split、二进制hash，build绑定源码和库；不将录音、会话原文或客户信息写入知识正文。
breaking_change: none；仅Host测试分支，不改产品ABI或协议。
runtime_control_plane / browser / external_standards: not-applicable；没有修改模型、权限、连接器或外部规范。
rollback_path: v7不可变证据与相同主链/库保留；所有oracle宏默认关闭，不存在生产候选需要回退。

reusable_pattern: 在真实回调原地修改前重建算法实际更新，先检验装置identity，再进行真值因果控制。
promotion_candidate: false
next_task_friction_reduced: 已排除观测窗口内清零/溢出，区分暂停学习与纯回声持续学习，提供有界可复跑工具。
reduced_by: 权重重建、720帧生命周期和24对identity控制。
reduction_evidence: 上述绑定JSON和源码测试。
do_not_promote_reason: 两项控制均未形成合格产品收益，真值不可部署，缺ARM/HIL。
owner_review: pending

## 后续与预算

用户本轮明确把当前累计预算提高至100000000，已更新真实thread既有goal；成功条件与open_items没有变更。
thread：`01a0f1a9-4067-7321-8619-5672b5b68343`；goal：`task-2ed1fe6b0672da063403f369`，仍active/open_items1，`call-residual-protected`未满足。

下一轮在公共真值上受控旁路AES或NN，逐一核验callback/FIFO/算法延迟与近端投影，定位完整尾链目标损失；只有确定机制后才尝试不依赖真值的产品保护。禁止继续扫描冻结门槛、AGC增益或MIC/REF延迟。四原始远端仅配对观察，不能用总能量下降代替近端质量。
不覆盖v7；本报告仅通过Knowledge Provider请求脱敏reviewing归档。Runtime final只核本地conformance，不能替代声学或产品验收。
