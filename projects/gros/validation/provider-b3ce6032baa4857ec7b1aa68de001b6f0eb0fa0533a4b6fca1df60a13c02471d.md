---
id: provider-b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d
title: AISpeech 两小时 N08 独立验证与测试候选结果
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d
  source_sha256: 4d04c4cb592ebb9d1f52081053f0bc5513e1b070f64d16ed38e909ac25f3912b
  temporary_source_retained: false
review_after: '2027-01-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/gros/validation/provider-b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 状态：reviewing；隔离测试候选，不是设备或生产放行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: b3ce6032baa4857ec7b1aa68de001b6f0eb0fa0533a4b6fca1df60a13c02471d
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- AISpeech 两小时 N08 独立验证与测试候选结果
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# AISpeech 两小时候选迭代结果

状态：reviewing；隔离测试候选，不是设备或生产放行。

本轮从 2026-10-23 14:59:57 UTC 开始，硬截止 16:59:57 UTC。在八个单机制候选中，N08 angle-projected 是唯一通过本轮完整质量、兼容性、资源和独立验证的候选。保留原生产 v70/v72 默认；没有提交、推送、部署或替换父仓预编译库。此次有界候选研究完成，不代表持续对讲回声问题已解决。

## 方案与收益

N08 在独立合成的增量修正上增加当前输出方向误差保护：量化后与最佳标量拟合的 RMS 误差超过原生输出 RMS 的 2^-12 时，当前帧保留 v70 输出，同时继续推进私有历史。既有前端、主 AGC 驱动和上层接口保持原契约；没有新增前视或帧延迟。

原 400 例全部通过，包括 2,834 个起音和尾音窗口。相对 v70，平均远端单讲指标增加 0.0058048754 dB，按文件等权平均的残余输出能量下降约 0.1334053%。该能量结果不是 ERLE，也不足以解释为明显可听的消回声改善。

最差双讲变化相对 v70 为 -0.00319337 dB，相对原生关闭候选版本为 -0.09727808 dB，接近 -0.1 dB 保护线；最差目标指标相对 v70 为 -0.00540785 dB。所有窗口仍按未舍入值判定。

唯一赢家冻结后才读取独立 24 例，24/24 通过，四类场景的平均远端单讲增益如下：

| 场景 | 平均增益 dB |
| --- | ---: |
| 线性、无噪声 | 0.0101167492 |
| 非线性、无噪声 | 0.0065310588 |
| 线性、有噪声 | 0.0050611053 |
| 非线性、有噪声 | 0.0029742184 |

独立集总体平均为 0.0061707829 dB；以 24 个独立源为配对单位、固定 seed 20261023、10,000 次 bootstrap 的 95% 区间为 [0.0040473466, 0.0084002203] dB。独立集与本项目旧 400 例的说话人和源片段不重叠，但来自公开数据的 train 分区，神经网络预训练独立性未知，不构成官方挑战赛资格。独立集已曝光，后续不得用它调参后再宣称盲测。

## 淘汰记录

| 候选 | 最终处理及依据 |
| --- | --- |
| N01 quantum-gate | file58 尾音窗口失败，淘汰 |
| N02 coherent-projection | file655 起音目标保护失败，淘汰 |
| N03 coherent-mask | file58 尾音窗口失败，淘汰 |
| N04 post-OLA-delta | 开发集 file29 尾音窗口失败，淘汰 |
| N05 post-OLA-projected | 全回归第 395 例 file3290 尾音窗口失败，淘汰 |
| N06 spectral-projected | 全回归第 146 例 file539 起音窗口失败，淘汰 |
| N07 slew-projected | 零修正静音负控制复现状态偏置，设计否决；不是通过项 |
| N08 angle-projected | 完整 400 例和冻结后的独立 24 例均通过，保留隔离测试候选 |

中途根据 N05/N06 的真实失败重新规划，从六个机制、两次完整回归扩展到八个机制、三次完整回归，仍使用同一个两小时边界；没有继续新增候选。

## 验证与资源

- 267 项 Python 测试通过，0 跳过；12 个正向 ASan/UBSan 数值程序通过，另一个程序明确复现 N07 缺陷。未对供应商整个库做 sanitizer 插桩。
- 完整 400 例的 CALL 前端状态和原生 Q24 AGC 轨迹核验通过；400 例 VOICE、400 例无参考近端 CALL 的完整 PCM 恒等；同模型静态库与动态回放的完整 PCM 恒等。预检查已与最终完整回归逐例确认。
- 两轮设备原始双麦的 16 组离线回放通过兼容性检查；12 次生命周期循环通过。原始录音缺少干净近端目标，不能据此证明设备消回声收益。
- Host 独占资源测试：arena 增加 12,320 bytes，另有只读模型系数 208 bytes；median 耗时增加 9.4121%，p99 增加 13.6124%。没有外部 heap 或静态实例状态；这些数据不能外推为 ARM CPU 性能。
- 独立验证首次下载了 96 条音轨并逐条校验；Python 3.8 的 Executor.shutdown 参数不兼容造成评分前技术中断。新增单独适配层沿同一次曝光恢复，原冻结评分器、模型、阈值、样本和随机种子均未修改。
- 原生产源码、配置、上一轮 35 个研究文件及父仓库库文件保持锁定身份。父仓既有脏改仍保留，不能声明父仓干净。

## 制品与复查入口

所有一次性音轨、PCM、二进制和完整运行记录保留在源码根 `.cache/aispeech-twohour-20261023-145957Z/`，不提交到 Git 或写入知识正文。

隔离 ARM 测试库：`candidates/n08-angle-projected/arm/libaispeech.so`，大小 1,360,772 bytes，SHA256：

`dea6888d12c661df49ce366ae5854a04384ea0b060c57fc18b20ea86253cc076`

这是 ELF32 ARM hard-float 产品库，Host/ARM 归一化算法源码和模型相同，不含 replay bridge；尚未在 ARM 执行、未部署到设备，手机回声未解决，生产放行为 false。原生产隔离库 SHA256 仍为 `1069c8440a117bc8015bf7892120d6e1f8187b3db14f0a826f2e4f5f2037eb5d`。

核心证据入口：`n08-full400-native.json`、`n08-driver-confirmation.json`、`n08-resources/resources.json`、`n08-raw.json`、`n08-lifecycle.json`、`independent-winner.json`、`independent24/validation.json`、`final-regressions-v2/tests.json` 和 `FINAL-EVIDENCE-v2.json`。最终清单重新核对冻结来源、各个否决、未舍入窗口、独立统计和新文件格式。

下一步优先对当前算法剩余回声的频段、参考相干性及非线性泄漏做分层归因，选择收益显著更大的新机制；N08 只作为微增益测试备选，不建议因这点收益直接替换生产默认。若进入设备测试，需要另行绑定安装制品身份、实时耗时及对讲听感，并单独验收双讲、弱语音、切换和长跑。
