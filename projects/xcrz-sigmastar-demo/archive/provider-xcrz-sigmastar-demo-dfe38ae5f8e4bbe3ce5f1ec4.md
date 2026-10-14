---
id: provider-xcrz-sigmastar-demo-dfe38ae5f8e4bbe3ce5f1ec4
title: AISpeech 离线优化续办核验
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-dfe38ae5f8e4bbe3ce5f1ec4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:dfe38ae5f8e4bbe3ce5f1ec4d67331f69b2a553dd30a22a9d9f530a8c0d8394a
  source_sha256: 09c1bb881b67a53b9effc9600fd643c4c64ef113ed58a160406f9a7690f12e6a
  temporary_source_retained: false
review_after: '2027-01-07'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-dfe38ae5f8e4bbe3ce5f1ec4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-dfe38ae5f8e4bbe3ce5f1ec4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-09'
updated_at: '2026-10-09'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-09'
manual_validation_pending: true
summary_zh: 用户要求：继续推进。范围：修复 BF=0 测试兼容性、补齐阶段/尾链 sanitizer、复核既有制品和输入；不调整已否决的算法候选，不提交或部署。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: dfe38ae5f8e4bbe3ce5f1ec4d67331f69b2a553dd30a22a9d9f530a8c0d8394a
---

# AISpeech 离线优化续办核验

用户要求：继续推进。范围：修复 BF=0 测试兼容性、补齐阶段/尾链 sanitizer、复核既有制品和输入；不调整已否决的算法候选，不提交或部署。

## 已解决

- 阶段契约测试按 `SEVC_SWITCH_BF` 分支：BF=0 检查实际配置和两个实例的 BF engine 均为空；BF=1 保留构造函数空配置拒绝检查。未删减检查或重新引入默认 BF。
- BF 专项数值测试显式编译 BF 源码及私有 SPP 消费者，避免依赖默认禁用的内部符号；主产品仍保持 BF=0。
- 尾链测试使用项目已有 sanitizer 编译参数；临时汇总脚本额外 `-Werror` 造成的 vendor unused 警告编译失败已排除，未修改算法源码或运行检查。
- README 补充与本次隔离静态库配合的复跑命令。

## 新鲜验证

| 命令或入口 | 退出码 | 结果 | 证据层 |
|---|---:|---|---|
| `run_regressions.py`，链接 final-host/libaispeech.a | 0 | 19 个检查全部通过，记录在 regressions.json | Host |
| `run-stage-contracts`，BF=0，直接编译 VAD/NN/AGC/AEC/AES/BF 阶段并启用 ASAN/UBSAN | 0 | 11 项检查通过 | 阶段 sanitizer |
| BF=1 隔离库 + stage-contract bf-null | 0 | 空配置拒绝检查通过 | 可选配置 |
| `run-tail-transition`，直接编译 NR/NN 并启用 ASAN/UBSAN | 0 | 噪声阶跃、增益界、FIFO 对齐、静音尾部、Reset 等价性通过 | 尾链 sanitizer |
| `run-bf-numeric`，BF 单元显式开启并启用 ASAN/UBSAN | 0 | 8k/16k normal/extreme/config/reset 全部通过；SPP 125 个功率判定通过 | 可选 BF 单元 |
| `run-device-replay-contracts` | 0 | 14 个输入/身份/对齐契约测试通过 | Python |
| 1000 轮尾链 smoke（包含在 19 项汇总内） | 0 | 2000 次切换、40013 个回调，memory=308308 | Host 生命周期 |
| public-header check + 父仓/AISpeech diff --check | 0 | 公开头无漂移，空白检查通过 | 源码 |

19 项汇总：尾链 smoke、公开 ABI、AEC/AES 通道一致性、Reset、评分对齐、参考延迟共 6 项；BF=0 阶段契约 11 项；尾链 sanitizer 1 项；BF=1 构造异常 1 项。Python 和 BF 专项数值测试分别报告，不重复计入这 19 项。

sanitizer 只对命令中直接编译的阶段源码生效，链接的其他普通 archive 成员没有因此自动获得完整插桩；不声称整个产品库全路径 sanitizer 通过。异常参数/短内存测试出现预期错误日志，与退出码 0 的拒绝行为一致。

## 最终配置与证据回读

保持 BF=0；VOICE taps=2/MU=0.8；CALL taps=1/MU=0.4；DTD 条件释放、AGC 低输入限幅/静音保持仍为 0，参考延迟 20 点。

本轮仅变更测试和说明，最终 Host/ARM 库源文件与头文件哈希仍符合既有 build.json，无需重复构建未变化的产品源码。16 组原始输入七文件 SHA256 全部再次核对一致；VOICE 与设备输出一致的采样点仍为 7,715,328。旧原始重放结果没有冒充本轮新增算法收益。

- regressions.json SHA256：98ee293acdec12cb20c8fba9d5380e0b40571748348ab65834cbc4cbf88ccd73
- stage-contract test SHA256：6b04dff58f59f9f6a331c1779409a0e83497566cf631cf6f58ad9669c1ced694
- Host replay library SHA256：2046a19b5c02a9308653e1938306ba223a68630e3c68ae78efd6d48817a789f0
- ARM static SHA256：adeae5dbfddafffe31cd16c6d315d4404c40586dedc56cfde204fb76b7fe849a
- ARM shared SHA256：2f2468cc6502958e63bc8926e3c96196d971b3408c8c787dbb8e26ea469d9be2

## 定向核验与验收边界

R1（BF=0 内部符号链接失败）关闭；R3（BF 专项数值入口随默认关闭而失效）关闭。BF 开关两分支均有实际测试，未通过跳过来伪造通过。公开接口与库身份稳定，产品算法源码本轮没有修改。核验是本次执行者的源码回读，不代替独立人工声学验收。

CALL 两抽头有监督双讲最差下降 0.647 dB，继续保留候选而不提升默认；不放宽已有指标，不把总输出能量减少解释为纯回声 ERLE。正式手机通话听感和设备 CPU/延迟验收仍不具备本轮证据，不列为已通过。

当前可确认的是本地测试缺口已修复并完成验证。Host/ARM 隔离库没有自动进入主应用、image、OTA 或设备；没有进行主应用重链接、设备部署或 commit/push。

## 可复用候选

- reusable_pattern：关闭可选算法模块时，同时验证 disabled 实例不持有模块资源，并保留显式 enabled 单元测试。
- promotion_candidate：false；仅作为本项目 reviewing 候选，不提升团队规范。
- next_task_friction_reduced：后续 BF=0 构建能继续运行阶段契约与可选 BF 数值测试。
- reduced_by：条件分支与显式编译被测源码。
- reduction_evidence：此前 undefined reference，当前对应测试真实退出码 0。
- do_not_promote_reason：缺少独立 owner review 和目标设备声学资格；本项目 test harness 不能推广为产品链路保证。
- owner_review：pending，不推断 owner 身份。
- rollback_path：仅反向移除本轮阶段测试、BF Makefile 和 README 的定向补丁；保留用户原有 dirty。
- verification_evidence：上述命令、regressions.json 和原始/库哈希回读。

Runtime conformance 独立报告；既有 goal 的预算已耗尽，用户继续指令未用于提高预算、替换旧 goal 或绕过门禁。此文档在 Provider 明确返回 persisted=true 前仅为本地候选。
