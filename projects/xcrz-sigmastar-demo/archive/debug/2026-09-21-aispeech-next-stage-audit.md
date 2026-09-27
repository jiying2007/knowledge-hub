---
id: aispeech-next-stage-audit-20260921
title: AISpeech非AGC环节审查与下一阶段重点
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-next-stage-audit.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 77561c5bdf8b42e048e7cd27da7b9227cab65b6d764a12d6c3012f4aba35d861
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-next-stage-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-next-stage-audit.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 核验BF消费者输出余量VAD语义，区分已确认问题与设备待验方向
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech AGC以外的下一阶段审查重点

本次只读核验当前源码，结合本会话已有Host证据，不把已经修复的数值缺陷重新列为现存缺陷。
早期全链路归档中的旧公开头/预编译库绑定和BF Reset描述已经被后续工作更新，不作为现状引用。

优先1：输出电平。当前INTERACTION outGain=40960(Q15即1.25)，输出headroom limiter默认0。
此前Host样本4已观测输出增益阶段限幅106次、IFFT/overlap为0。是已复现的离线现象，
不证明设备同场景必然发生。应单独复验输出余量候选、波形/唤醒/响度取舍，不全局加增益。

优先2：BF消费链。当前双麦配置BF默认1、GSC/BF_POST为0；sevcGscCbFunc在AES分支
消费pLastAec，SEVC_NR_Feed参数SPP为NULL。BF三波束音频不进此分支AES、SPP不进当前NR。
属于可疑冗余计算，非直接声学故障。此前BF关闭对照有相同PCM及Host内存减少证据；
本次不重用旧内存绝对值或宣称SSC305算力收益。下一步核验诊断消费者，再测板上CPU/p99与RAM。
不建议为让BF发挥作用直接把输出接到AES：AEC残差/回声配对与35mm全向需求须重新验收。

优先3：VAD语义与用途。当前VadStatusGet仅CALL且NN/AGC可用时有效；INTERACTION为NONE/valid0。
CALL数值来自AGC平滑NN增益代理，已观测全零可偏高；不是校准的语音概率。
现有参考VAD也不是近端speech detector。产品如需断句/静音停传/唤醒前置门控，应先定义独立契约和数据。

NR/NN：当前NR增益floor0.75、NN平方后floor0.20，弱语音保留与降噪强度有明确取舍。
此前NN/AGC弱尾段观测仍有衰减，不能单凭聚合电平定位为NN错误，也不能只降低floor。
后续需把NR噪声跟踪、NN mask和AGC分别做对照，使用真实低声中文/机械噪声/词首尾音。

AEC/AES：此前通道配对/数值/Reset等已修复不代表声学最优。当前HDI保留手工参考delay设置，
有活跃reader时拒绝修改。没有本次设备同步录音证明时延错误，下一步先做mic0/mic1/render同步，
再评估移动/音量变化/双讲、AES保持释放与词首，不能假定没有优化空间。

时序/产品：模式切换的NN历史延迟、预热、回调生命周期和实际设备制品仍需端到端验证。
Host局部测试不证明完整产品集成、设备实时性或中文QIVW命中率。
当前未启用分支（GSC/BF_POST/EQ/CNG等）不能因被读过而称已全面验证，也不应盲启用。

本次不改源码、不运行新音频矩阵、不宣称上述优化已实现。用户原目标是全面审查，
应把后续重心从继续微调AGC移到输出余量、BF资源、VAD契约及AEC参考链设备证据。
Runtime Control idle/null goal缺会话制品单列not_applicable。
