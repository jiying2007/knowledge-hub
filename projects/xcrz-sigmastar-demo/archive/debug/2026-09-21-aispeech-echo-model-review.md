---
id: pcr02-aispeech-echo-model-review-20260921
title: AISpeech 回声覆盖区间与非线性留出对照
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-echo-model-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 862646af6e785736c89c0a71cf85e94fae0340633dcd797ed7b544618c2977eb
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-echo-model-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-echo-model-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 建立只读线性与三次项回声预测探针；fileid4正反留出显示参考起点及覆盖重要，不支持直接加长峰后尾部或引入本三次项扩展。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech fileid 4 回声覆盖区间与非线性对照

- captured_at / last_verified: 2026-09-21
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- HEAD: 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1；保留已有工作树修改。
- Reviewer Independence: author-self-review。
- 本轮新增只读离线探针、合成控制测试和复跑说明；未修改产品链路、默认参数、近端/mic 数据或算法库。

## 方法和边界

探针仅使用 far 与独立 clean-echo 轨，比较线性 FIR 和线性加三次项两个 FIR 分支。
第一个方向以前半段拟合后半段预测；第二个方向交换训练/预测半段。
同一次调用的模型共享 2048 samples 保护间隔、相同训练时刻和留出时刻。
训练每 8 点选一行，共 9744 行；均值、标准差、输入归一化仅由训练部分产生，ridge 固定为 0.001。
最终预测分数使用留出区间全部 77952 个采样，另保留抽样评分用于核对，不按测试结果调参。

分数为 10log10(clean-echo 能量 / 离线预测误差能量)，不是 SEVC ERLE、近端语音质量或 QIVW 指标。
模型采用独立 clean-echo 监督训练，不能直接用于产品参考延迟估计，也不能将其 FIR 长度直接等同于 SEVC 分区抽头数。

## 正反方向结果（全采样留出评分，dB）

| 起点 | FIR 长度 | 基函数 | 系数数目 | 前半训练、后半预测 | 后半训练、前半预测 |
| --- | --- | --- | --- | --- | --- |
| 0 | 512 | 线性 | 512 | 1.588 | 0.999 |
| 0 | 1024 | 线性 | 1024 | 13.080 | 12.574 |
| 0 | 2048 | 线性 | 2048 | 12.374 | 11.107 |
| 0 | 512 | 线性+三次项 | 1024 | 1.204 | -0.138 |
| 0 | 1024 | 线性+三次项 | 2048 | 12.171 | 10.432 |
| 405 | 512 | 线性 | 512 | 4.705 | 4.122 |
| 405 | 1024 | 线性 | 1024 | 6.097 | 5.527 |

## 推论与负结果

- “只需要延长当前峰对齐后的尾部”不足以解释结果：从 405 开始加长到 1024 仍明显弱于覆盖 0～1023 的线性模型。
- 405 之前的信息在该离线模型中有价值，最高相关峰不能直接当作响应起点。应优先检查参考起点与可建模区间。
- 线性模型从 1024 加到 2048 没有进一步提高留出预测；不能盲目增加抽头数。
- 本次三次项模型训练分数更高，但两个留出方向均弱于相同覆盖区间的线性模型。不支持据此引入该非线性扩展；这不证明数据不存在其他形式的非线性。
- 上一轮 SEVC 零延迟端到端结果更差仍然有效。本轮静态监督拟合不是该运行时对照的替代，不能直接将产品参考延迟改为 0。
- 结论限于 fileid 4、固定基函数与正则化，以及这两个时间半段；剩余非线性、时变性和自适应过程仍未唯一分离。

## 已实现与验证

- 工具：modules/aispeech/tools/codex_assets/echo_model_probe.py，只读 JSON CLI，带 --dry-run 和 --reverse。
- 输出输入 SHA256、模型覆盖、参数数目、保护区、训练/预测样本数和得分；不输出系数、波形或处理后 PCM。
- 每轨最多一百万采样、容器最多16 MiB、单模型最多4096系数、一次最多12模型；拟合工作内存有保守估算门禁，不当作 RSS 保证。
- NumPy 1.24.4；无需额外安装 SciPy。
- 4 个单元测试通过：已知线性尾长与早期分量、已知三次项、反向分割与低激励/内存门禁、损坏 WAV 与 dry-run 禁止拟合。
- 测试、CLI help 和真实输入 dry-run 均从非仓库 cwd 验证；Makefile 的 run-echo-model-probe 入口通过。
- git diff --check 通过；不重建产品算法库，不部署设备。

## 复跑

从 AISpeech 子仓根使用 tools.codex_assets.echo_model_probe，模型列表固定为：
0:512:1、0:1024:1、0:2048:1、0:512:3、0:1024:3、405:512:1、405:1024:1。
参见 tests/README.md 的完整命令；训练/预测对照用 --reverse，先用 --dry-run 核对计划。
rtk make -C modules/aispeech/tests run-echo-model-probe 验证合成控制。

## 身份

- far SHA256: 9a05b206438e183c6a7022192b901860c3f32ae0e7b3d4f8a18f4dfde4112652
- echo SHA256: c10155163f33c8343e514d0a4df4b897edb658a09e31e492ffb8e82421242ed7
- probe SHA256: 95704157a5e61333368acd8ef5cd4d470295b7e466758901dd3244b075cb81fe
- test SHA256: 6ce122ee35d1ae55a614c9458f5a607c16dd727d5b60ec551fbc3ce2c93c4375
- 未变化的 Host 算法库 SHA256: ac5b48ae8186d6e7b233a0fd1caadc25f3d8471dac1844ff4ed070b738d3ecef

后续应使用独立样本验证参考起点/覆盖区间的诊断能否推广，再设计产品候选；不要基于单样本拟合结果直接变更默认延迟或抽头。
现有条件释放候选保持关闭；产品声学门禁、真实双麦、板端和 QIVW 未闭环。
归档仅保留脱敏方法和结论，不含原始音频、模型系数或逐帧日志。
