---
id: aispeech-agc-joint-review-20260921
title: AISpeech AGC联合指标与试听工件
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-joint-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 02a7d9fd3ae0599f6eb24122fbf8885ae312d68ed23dd97468e623d7e832a955
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-joint-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-joint-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 补充分段电平与增益变化，24WAV试听包校验通过，人工听感待评
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AGC 联合电平指标与人工试听工件

本轮只修改观测器/文档，不修改算法参数。低输入封顶候选仍默认关闭，独立听感未执行。

## 方法及边界

沿用4/7/18/21/25/29/35/43的整段观测，默认/候选共192项。
原始干净参考每256样点帧RMS>=64作为活跃掩码，不依赖输出或缩放；文件三等分
计算活跃样点输出/目标能量比。中间三分之一的低参考能量帧标记quiet，可能仍含弱语音，
不能称人工标注纯噪声。空掩码指标输出nan并保留样点数。gain step统计有效对齐区的
相邻帧（含三段边界），这是增益控制变化，不是PCM瞬态检测。

## 观测

样本21、八分之一幅度加噪声：quiet有9728样点，输入-40.8466dBFS，
干净参考-83.2200dBFS，默认输出-33.5062dBFS，候选-48.8483dBFS。
最大逐帧增益变化7.1424→0.3676dB；平均绝对逐帧变化0.2077→0.0044dB。
活跃区三段输出/目标电平比分别23.4614/5.2088/14.9912dB→5.9748/4.2466/2.9682dB。
这些数据支持增益波动和部分低能量区输出变小，但不能直接称听感更自然。

样本21、正常幅度无噪声（此前SI-SDR回落0.053dB的组合）：
活跃电平7.0901/4.9334/6.4028→5.8874/4.4989/4.4906dB，后段低1.9122dB。
最大gain step18.3796→3.3270dB。应听评电平变化是否影响尾音/响度，而非只看SI-SDR。
样本18弱噪声后段活跃电平默认-8.1991、候选-8.2072dB，弱段抑制仍存在。
样本4弱噪声quiet仅256样点，不能对其短窗作稳定噪声结论。

## 试听包

路径/tmp/aispeech-agc-review-20260921-v1.zip，2609462字节，26个条目。
SHA256 fd56efc5b09582508cff3fb01bb51e38106086373044043996fdd19e2e9b1f40。
解包目录同名，README包含试听顺序和链接，manifest记录24个WAV身份。
3组：样本21正常干净、样本21弱噪声、样本18弱噪声；各含默认/候选，
每版本input/clean/output/matched四个WAV。没有客户录音，素材沿用现有公开测试集许可。

所有WAV单声道16kHz PCM16LE，159744样点（9.984秒），output按CALL512样点对齐。
matched按相同参考掩码将活跃区RMS缩放到1280，6个文件均未触发32700峰值保护。
实测匹配RMS在1279.9979～1280.0011之间。不是感知响度归一，也不是产品算法。
应先听output比较响度/词首，再听matched比较音色、噪声起伏、尾音。
禁止把生成文件或数值验证写成独立听感通过；等待人工记录具体时刻与偏好。

## 验证

- 默认/候选观测器-Wall/-Wextra/-Werror（仅关闭厂商unused parameter）直接编译通过，192项运行退出0。
- 对新导出路径和AGC源码启用ASan/UBSan，默认/候选样本21弱噪声各运行并导出成功。
  其他库代码没有整体instrument。
- Python标准库只读检查24WAV格式、长度、默认/候选input及clean逐字节一致、匹配RMS及无满幅。
- 从导出WAV独立重算样本21 quiet能量，得到-33.5062292747和-48.8482833459dBFS，与观测器一致。
- 已存在前缀重复导出返回1，使用独占创建，不覆盖原工件；zip CRC与26条目验证通过。
- diff --check通过；本轮不重建ARM或部署。默认行为未改。

指标统计保留/tmp/aispeech-agc-joint-results-20260921.json；音频只在/tmp审查包，未写Hub正文或Git。
观测器源码SHA256 d004afec6b476099941e39c083c531d8c8250c8c41aa50ef879403dbefd5d411。
主代理targeted自审及独立计算实现校验，无独立人员听评。
Runtime Control idle/null goal缺会话制品按planning skill单列not_applicable。
reusable_pattern: 用输出独立的参考掩码结合电平与增益变化，并同时提供原输出/RMS匹配试听。
promotion_candidate: false；do_not_promote_reason: 人工听感及中文设备门禁缺失；owner_review: pending。
rollback_path: 移除本轮观测器/README增量，不动其他dirty或候选默认配置。
next_task_friction_reduced: 可直接听评具体回落/弱噪声场景；reduced_by: 24WAV+README+manifest。
reduction_evidence: 格式/输入一致性/RMS/独立能量/ZIP校验；下一步人工听感记录及中文场景补充。
