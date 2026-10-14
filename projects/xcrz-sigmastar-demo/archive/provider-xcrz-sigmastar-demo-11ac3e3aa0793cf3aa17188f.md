---
id: provider-xcrz-sigmastar-demo-11ac3e3aa0793cf3aa17188f
title: v36：实际 raw mic / estimated echo 归一化复相干性观察
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-11ac3e3aa0793cf3aa17188f.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:11ac3e3aa0793cf3aa17188f6fca2bf6ce160c49f8d5b1fda9f6df6b3ff67f3e
  source_sha256: ddadf1abae9938ed20d84c27e760b258046b9059f7520640776d653ff0dfc4a7
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
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-11ac3e3aa0793cf3aa17188f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-11ac3e3aa0793cf3aa17188f.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: 固定 v31 实际输出，observer 在 Feed 前读取上一帧 raw mic1 FFT 和缓存 AEC removed echo， 计算复相干性，EMA1/8、至少8有效帧；并在本次 NN callback 已完成后只统计原表
  eligible 频点。 18、206、550、831、540、556 六例的所有原始指标与冻结 v31 actual C 精确一致。 帧完整唯一，NN lookahead 和 raw FFT 两 hop 真值稳定区域对齐，混合边界排除。
  数学 C ASAN/UBSAN 控制通过独立EMA展开、复相位/幅值不变性、Reset、INT32边界和20000随机控制。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 11ac3e3aa0793cf3aa17188f6fca2bf6ce160c49f8d5b1fda9f6df6b3ff67f3e
---

# v36：实际 raw mic / estimated echo 归一化复相干性观察

固定 v31 实际输出，observer 在 Feed 前读取上一帧 raw mic1 FFT 和缓存 AEC removed echo，
计算复相干性，EMA1/8、至少8有效帧；并在本次 NN callback 已完成后只统计原表 eligible 频点。
18、206、550、831、540、556 六例的所有原始指标与冻结 v31 actual C 精确一致。
帧完整唯一，NN lookahead 和 raw FFT 两 hop 真值稳定区域对齐，混合边界排除。
数学 C ASAN/UBSAN 控制通过独立EMA展开、复相位/幅值不变性、Reset、INT32边界和20000随机控制。
六个 Python 控制通过；非仓cwd help/dry-run通过，原 DTD 诊断功能保持。

MSC>=.75 桶占原表校正能量的比例（仅固定分布桶，不是分类阈值）：
18 far99.17%/double18.91%；206 far95.12%/double25.06%；
550 far94.24%/double41.41%；831 far70.93%/double39.41%；
540 far62.59%/double51.02%；556 far13.99%/double16.47%。
550/831 有一定分布差异，但556远端也大量处于低相干；不能据此宣布可靠近端检测。
上述能量不是最终语音损失的因果证明，不能代替实际PCM验收。

observer binary SHAb9dc5405fe1dea53832c2003136cdcc5858e0a3c93e7a6f0f98f71ca04aa3bd1。
来源只用于设计参考：Benesty/Gansler2001频域归一化互相关，Ghose/Reddy2000麦克风/估计回声相干判据。
公开HTTPS主来源：https://www.iwaenc.org/proceedings/2001/main/data/benesty.pdf
https://www.sciencedirect.com/science/article/abs/pii/S0165168400000499
本简化MSC观察不是上述完整论文实现，无第三方运行代码导入、无凭据/设备操作。

下一步固定连续置信度混合，不能用当前分布挑阈值；先实际C回归，不继承旧几何预测资格。
仅Host观察，无生产默认/库/协议/reader/lease变更，无commit/push/deploy/restart。
主声学目标未完成，累计200M/36h有效。
