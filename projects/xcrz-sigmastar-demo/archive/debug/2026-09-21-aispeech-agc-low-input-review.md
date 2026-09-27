---
id: aispeech-agc-low-input-review-20260921
title: AISpeech AGC低输入增益与VAD耦合候选
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-low-input-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 9c6c60e0260b7ab246958b5d2a380e43900e30858f9151f83dbc6cfa660cb2c6
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-low-input-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-agc-low-input-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 低输入目标增益默认关闭候选完成数值与冻结留出验证，保留回落未晋升
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AGC 非零低输入增益与VAD耦合：默认关闭封顶候选

本轮确认现有曲线/门控行为，实现SEVC_AGC_CAP_LOW_INPUT_GAIN候选，默认0。
原全零保持候选也保持0；两者同时开启未经验证。未提交、部署或发布。

## 归因与实现

低于T1（当前-60dB）时，曲线目标输出为G_low=-60dB，不依赖VAD；
1LSB输入约-90.309dB，请求增益30.309dB。实际增益上升由另一套平滑门控决定。
短时阈值0.05可以启动上升，而对外speech阈值为0.2；输入代理VAD为0.05时
speech=0但1LSB增益仍可升到30.309dB。0或0.04时从Reset的0dB保持不升。
这是既有不同用途阈值的耦合，不直接判定某个阈值错误。

新候选仅在fXDb<T1时把请求增益封顶到现有T2_gain（6dB），然后走原平滑和峰值约束。
不是即时钳制实际增益，不改变VAD、阈值、时间常数、结构或公开接口。
非零微幅和纯零输入均覆盖；从Reset开始的1LSB高代理VAD稳态由30.309dB变为6dB。
已有高增益仍按配置释放，不瞬间跌到6dB。

## 数值与边界

run-agc-low-input直接对AGC启用ASan/UBSan，默认/候选各8幅度×5VAD，
另加40dB初始增益向低输入目标释放的控制测试，均通过。
curve_gain_db是未经候选封顶的曲线请求；actual_gain_db是实际平滑值。
首次释放用例错误要求240帧后误差<0.001dB，断言失败；现改为按配置alpha计算
目标指数曲线并允许每帧1个Q24单位的累计舍入差。没有为测试改释放速度。

## 观察集与冻结留出

原观察集4/7/18/21；在读取留出结果前固定25/29/35/43，均为现有split近端干净标记。
后者未用于本轮候选设计；这次已用于验证，以后不能继续称为未见集。
沿用整段与起始观测方法，共8样本×(12整段+8起始)×2版本=320项。
其中CALL比较为32个整段对、64个起始对；另64对交互/旁路AGC是控制路径。

- CALL整段：30改善、1相同、1下降；平均SI-SDR变化+5.4067dB。
- 唯一整段回落：观察集21、原幅度无注入噪声，10.773→10.720dB，下降0.053dB。
- 起始64对均改善，最小+0.3600dB，平均+7.9050dB。
- 留出集未发现负变化；CALL整段最小0dB、起始最小+2.3699dB。
- 原候选失败的样本18纯零起始两项，现在相对默认约+8.968dB；未针对该样本改参数。

仍不晋升默认：整段SI-SDR受时变增益影响；输出响度变化与真实词首听感没有独立验收。
样本只有8个，复制双麦/reference零、固定随机噪声、阈值裁剪起始，不是阵列/双讲/中文HIL。
不为0.053dB单个回落调参，应联合分段电平、增益变化和听感评判。

新增留出输入SHA256：
- 25: 0b438a4846783542e947552db8a74f1b3037faced082dba913fc0e856391305d
- 29: 874198bda05dbf93a9dc50f10cbbd84df997bd450f727bc31501597d374740a8
- 35: 26ca685572826769ff4d7b445fd24d8ec4aeee8be8d875447e4687c265671e84
- 43: 2c8e6bec53bdcf70ad70dc60245bbef2cd6a4a8be6bc474ee394fc4b8c7fcec9
原观察集身份沿用此前归档。统计保留/tmp/aispeech-agc-low-input-results-20260921.json，无音频正文归档。

## 验证与制品

- `rtk make -C modules/aispeech/tests run-agc-low-input run-pipeline-fingerprint run-agc-window run-vad-status`最终退出0。
- 默认指纹16985685392395738340、内存315620；40150帧AGC窗口及VAD状态通过。
- 观察矩阵直接构建运行320项全部退出0；入口run-agc-low-observation复跑相同样本。
- 默认 `rtk make NC=1 modules/aispeech_lib_all -j4`退出0；候选AGC独立ARM对象编译退出0。
- diff --check通过。默认ARM静态库SHA256 4674d6739d32a4fb3ba5201401884c5dfbf6b4d255d991d5babb577b7ab28f04。
- 默认ARM动态库SHA256 665308e7b08819f1c29b3512ec7ae56711884373e149e19924f61ba1c0493cc2。
- 候选对象SHA256 e04f1e6eac48ab0e4bcd35cae75d8accc9a45b65ae26a2841eff569f822954b0。
没有候选完整ARM产品或设备证据。候选Host仅直接编译AGC覆盖库成员，宏不影响其他对象/布局。
Sanitizer覆盖定向AGC，不是全库。主代理targeted自审，无外部独立审查。
Runtime Control idle/null goal缺会话制品，按planning skill单列not_applicable。
reusable_pattern: 区分增益请求、平滑门控和对外语音状态，候选保留负例与冻结留出。
promotion_candidate: false；do_not_promote_reason: 联合声学门禁未完成；owner_review: pending。
rollback_path: 新宏0禁用候选；仅反向本轮增量保留其他dirty。
next_task_friction_reduced: 曲线/门控与整段/起始可复跑；reduced_by: run-agc-low-input及run-agc-low-observation。
reduction_evidence: 80条控制曲线和320项观察；下一步联合响度恢复、噪声与听感指标。
