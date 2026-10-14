---
id: provider-xcrz-sigmastar-demo-7a101780867bc5c6b67fa3df
title: CALL 阶段归因与两个候选的资格审查 v7
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-7a101780867bc5c6b67fa3df.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:7a101780867bc5c6b67fa3df5756648faf7bc5349ff38e4d01fecb8e3e2c7bd2
  source_sha256: 2f1046fe19d1c8d6268f7a2ad106954e5c1eef472ea1d01ec13a412b7ba34a0e
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-7a101780867bc5c6b67fa3df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-7a101780867bc5c6b67fa3df.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 结论：完成实际 AEC/AES/NN/AGC 的离线阶段取证，两个新增候选均未通过双讲保护。本轮没有采用产品参数，也没有解决持续远端自回声。默认主链、上层reader/订阅/协议保持现有行为。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 7a101780867bc5c6b67fa3df5756648faf7bc5349ff38e4d01fecb8e3e2c7bd2
---

# CALL 阶段归因与两个候选的资格审查 v7

结论：完成实际 AEC/AES/NN/AGC 的离线阶段取证，两个新增候选均未通过双讲保护。本轮没有采用产品参数，也没有解决持续远端自回声。默认主链、上层reader/订阅/协议保持现有行为。

状态：diagnostic milestone completed / main objective needs-fix / device qualification not performed。
执行范围：本地Host算法与诊断工具；没有部署、重启、commit、push或image/OTA更新。

## 1. 可靠的阶段测量

新增 `tests/sevc_call_stage_probe.c` 和 `tools.codex_assets.call_stage_probe`。

- AES原地修改输入，因此只使用回调时已经保存的乘增益前后功率，不读取整帧结束后的AEC输出作为线性残差。
- NN在Feed结束才旋转FIFO；回调时 `ppLastX[0]` 才是实际输入。明确要求R=1，将输入窗口对应到下一帧输出。
- AGC输入是IFFT后的S16 PCM。回调在overlap-add覆盖输入之前比较输入/输出，不能把它当成频谱增益。
- 回调总是继续原有函数，退出前恢复原函数和userdata；传输有界、完整帧、LE Host限定，拒绝截断、额外数据和未稳定窗口。
- 对冻结v6 MDF库使用其绑定的内部类型快照与MDF完整宏；默认库用当前默认类型，避免内部结构错位。

两轮设备原始录音共16份，七文件/PTS/seq/epoch及输入哈希验证成功。
最终观察器对两后端共32组CALL输出逐份确认：观察PCM = 无观察PCM = 冻结重放PCM，完全逐字节一致。
AES/AEC统计只覆盖AES实际处理的参考帧（远端四场景约73.4%）；NN/AGC覆盖完整评分窗口。
阶段能量比不是纯ERLE，录音也没有独立近端真值。FFT窗边界与MDF额外16点延迟使两后端阶段统计不是严格样点对齐，不能精确相加还原最终衰减。

## 2. 四份远端录音的阶段结果

数值为阶段衰减dB；AGC列为放大dB，最终列为相对原始MIC1的总能量衰减。

| 录音 | 后端 | AEC | AES | NN | AGC放大 | 最终总衰减 |
|---|---|---:|---:|---:|---:|---:|
| rpm240 far | 原生 | 12.2974 | 4.1627 | 7.6653 | 5.9913 | 18.4561 |
| rpm240 far | v6 MDF | 8.1339 | 1.8946 | 1.5203 | 5.9995 | 5.5087 |
| rpm240 far-motion | 原生 | 11.4348 | 4.2396 | 7.4073 | 5.9937 | 17.1758 |
| rpm240 far-motion | v6 MDF | 6.7678 | 1.4718 | 1.1356 | 5.9729 | 3.4018 |
| rpm480 far | 原生 | 12.0114 | 3.8695 | 7.5530 | 5.9932 | 17.7115 |
| rpm480 far | v6 MDF | 7.9367 | 1.2585 | 1.3655 | 5.9839 | 4.5619 |
| rpm480 far-motion | 原生 | 10.9483 | 3.6183 | 7.6432 | 5.9945 | 16.2547 |
| rpm480 far-motion | v6 MDF | 6.9551 | 1.9486 | 1.8555 | 5.9996 | 4.7091 |

MDF相对原生不只是线性残差较大：AES少衰减1.670～2.768dB，NN少衰减5.788～6.272dB。不能只靠强压尾链补救这次替换。
原生NN地板对应的输入能量占71.3～74.4%，MDF为16.3～25.3%；这是模型响应差异，不是近端真值分类。
原生四份远端录音AGC仍放大约6dB，近端录音同样约6dB。这给出了增益控制的优化方向，但没有提供可以安全识别弱近端的运行时判据。

## 3. 新候选与拒绝理由

固定公共24对真值，split SHA256 `4274aeeabbc0a2de54f0afcda789d821468f5558b3a7bf5a10f8f9a799a395bb`，所有输入、二进制哈希配对，既有音频与scale不改变。

| 测试候选 | 远端相对原生平均dB | 远端最差dB | 双讲SI-SDR最差变化dB | 双讲目标投影最差变化dB | 结论 |
|---|---:|---:|---:|---:|---|
| 连续参考且NN低VAD时取消固定AGC +6dB | +0.051792 | 0.000 | -1.023 | -0.574 | 拒绝 |
| 原生CALL双麦延迟16点 | -0.000208 | -0.345 | -1.050 | -0.302 | 拒绝 |

第一项通过测试NN回调暂时将实例T2_gain置0，保留真实AGC平滑及低输入曲线；不宣称将所有输入的AGC增益封顶为0。近端独立SI-SDR变化0，仍伤害弱近端双讲，因此不能作为产品增益策略。
第二项参考不变、原生所有算法不替换，评分CALL延迟明确为528点，VOICE仍256点，不追加EOF填充。它没有公共远端平均收益，近端独立SI-SDR最差-0.284dB。虽然针对原始录音中回声相对使用参考提前的关系提出假设，也不能根据该假设忽略公共真值回退。
两项都是Host测试适配器，限制同步、固定场景；延迟适配器最多两个实例。没有纳入产品ABI、实时资源或切换生命周期验收。先验门禁失败后未扩大设备录音候选重放，未继续扫描阈值/延迟。

## 4. 当前默认和验证

- `fresh-default-v7-final`：69编译单元、172源码/头绑定项，无来源漂移。43 SEVC/bridge项与v6精确一致。
- shared SHA256 `1f0dbcbda5db2f377d8eba1b0a161c7f6ccdfb4a7513a1def39dd61f892a73fe`；static SHA256 `cc9561d29c93d00948eb90c1a59b0a0f28f8d59a01ca3895107c798a9a807532`，均与v6相同。
- 实际阶段观察器ASan/UBSan检查通过：有参考/无参考PCM不改变、统计计数和8种非法传输拒绝；仅观察器编译为sanitized，静态算法库未整体instrument。
- 34项Python检查通过，无skip；根及独立AISpeech子仓 `git diff --check` 通过。
- 最终两个观察器重新编译并重跑16份录音，与初轮所有record字段一致；AGC候选以最终评价器源码重编后执行文件SHA完全相同，无需重复同一24对实验。
- CLI从 `/tmp` 完成help/dry-run，dry-run不生成文件。没有本轮新ARM性能、设备安装身份或设备听感证据。

## 5. 冻结证据和来源绑定

以下均为本地缓存中的新文件，未覆盖v6证据；Provider归档只取本文的脱敏结论，不复制原始录音、日志或二进制。

| 文件 | SHA256 |
|---|---|
| call-stage-captures-v7-final.json | 6bec144235c4e215309128f664aed8c251662f4a2f52cbb621dd01f38a3bcc32 |
| supervised-agc-ref-boost-v7.json | 4f73534a0c62a290421d6a63ef7a3a564d1fa1b602f5b9d234f1e6ed4054c437 |
| supervised-native-mic16-v7.json | 77bfc5c46bcae22f70dd5c7f841933ed62170bcd3da03d064be35a35d3411bb0 |
| fresh-default-v7-final/build.json | c79572da77b55bad6e7e8822eea8a1ee61268108afddbc525339f4670028e5bd |
| call-stage-native-v7-final | 3e17815f0f0dfbaf6175ec4cd8daef3351c975d751fa1b1cf80240679ba3331f |
| call-stage-mdf-v7-final | 3c955275a1c599a2c4b0fdc9c4e6f4b168fefc5c784072d42cc5c5e05cd1504d |
| challenge-agc-ref-boost-v7-final | e7b71b862429c90638c50edec0e1de16a5f9e378dd141ee3f67730684ef03ed1 |
| challenge-native-mic16-v7 | 2cc9b8a2c10fac3acaeff098026357640f0a44a788f748568be3dc78dfb7fc7b |
| tests/sevc_call_stage_probe.c | 645a991db01f4c75d1207fbbfbabb97037257376a2b084bb4f6bb1c80cef1436 |
| tools/codex_assets/call_stage_probe.py | ab1ee399418726579011a4ed1e37c9b74855a49aff88f0e70d2cea571d34621b |
| tests/sevc_agc_ref_boost_adapter.h | 61854e913525afecb6045c5fc105f6438092614e8f41337d7abf58c13cba671d |
| tests/sevc_native_mic_delay_adapter.h | d449269aca7afd9394bac3c4fa2078e7260391537b5e84a3706bd1eafc5ea553 |
| tests/sevc_aec_challenge_evaluator.c | 0b2186493cbf794671a110d7f0c06951299326081496512e50401e9f159aa79f |

观察器编译用 `AISPEECH_FIXED/NN_FSMN/SEVC_MULTI_CORE/SEVC_COMMUNICATION` 和各自静态库。MDF还使用 v6 类型快照与 `SEVC_TEST_MDF=1/MIC_DELAY=16/MU_PERMILLE=800/GLOBAL_NORM=1/TWO_PATH=1/ZERO_GUARD=1`。评价器用相同原生静态库和 `SEVC_TEST_TAIL_MODE=1`，分别 `-include` 两个测试适配器。均 `-O2 -Wall -Wextra -Werror`。

## 6. 下一步边界

优先对原生SEVC的权重更新、参考激励归一化及双讲期间的目标相关梯度污染取证，评估保留其主链的权重保护方案。参考活跃、NN VAD、当前瞬时DTD都不能单独充当安全的近端判据；先在公共真值上验证漏检/误触发，再接完整链。
不重复MDF整段替换、AGC低VAD阈值扫描或麦克风/参考延迟扫描。远端效果、近端双讲、ARM资源、设备听感仍为独立开放项。
