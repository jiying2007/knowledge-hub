---
id: pcr02-aispeech-full-chain-review-20260921
title: AISpeech 全链路源码审查与确定性修复
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-full-chain-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 2338a869260071e0a165a17d9fe5583160579a2becda22503e1c6223186f03d6
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-full-chain-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-full-chain-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 覆盖当前VAD/AEC/BF/AES/NR/NN/AGC及尾链，修复构造和NN数值问题；验证BF资源候选，产品旧头及预编译库接入不一致仍阻断。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 全链路源码审查与确定性修复

- captured_at / last_verified: 2026-09-21
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- Review Target: working-tree；HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1。
- Reviewer Independence: author-self-review，不是独立最终审查。
- 范围：当前 16 kHz、双麦+单参考、fixed-point、COMMUNICATION/FSMN 启用路径，以及产品公开头和链接边界。
- 既有 dirty 修改完整保留；未提交、推送、部署或替换产品预编译库。未启用 GSC/BF_POST/EQ/CNG/GRU 不列为已完整验收。

## 真实调用链

输入分帧/复制 -> 参考 VAD 与 FFT -> AEC -> BF 计算/回调 -> AES -> NR 或 NN -> IFFT -> 通话模式 AGC -> OLA -> 模式输出增益 -> PCM。
关键区别：BF 三束虽被计算，但当前 AES 消费的是末路 AEC residual 与同源 echo estimate；BF 输出不作为 AES 音频输入。
交互为 NR、无 AGC、固定输出增益 1.25；通话为 NN/AGC、固定输出增益 1.0。

## 按模块审查结论

| 环节 | 已核对事实与问题 | 本轮动作及优化空间 |
| --- | --- | --- |
| VAD | 检查参考绝对幅度变化，启动1帧/释放8帧；不是通用语音VAD。构造分配失败后先解引用再判空。默认完整Reset候选仍关闭，不能认为所有参考历史都被清除。 | 修复空参数和分配失败；保留现有检测算法。低幅播放、恒幅/削波参考及参考恢复需要专门数据，不盲改阈值。 |
| AEC | 当前交互2 taps/MU0.8、通话1 tap/MU0.4；参数在尾链阶段写回，影响下一次前端Feed。已保留此前通道配对和Reset全抽头清理修复。New在参数判空前读cfg。 | 修复空参数入口；此前恢复与参考覆盖问题仍需声学对照，不能判定无优化空间。 |
| BF | 固定35mm/三束资源；当前BF输出未被AES音频使用，SPP也未喂给当前NR路径。Reset为空符合其无时域滤波历史的实现，计数器不构成音频状态。 | 修复空参数入口；验证关闭BF可作为资源优化候选，未改变默认。不能把未消费输出等同于双麦波束形成普遍无价值。 |
| AES | 末路residual/echo配对；原始判据、保持和旁路历史状态已经分层。默认关闭的幅度下降条件释放候选仍未通过所有门禁。 | 修复空参数入口；保持候选关闭。优先处理可验证的残回场景，而非单纯降低DTD计数。 |
| NR | 默认DD-MMSE，增益floor0.75；持久历史已移出共享临时区，后验SNR/功率/谱减宽整数限幅已有修复。 | 重跑数值/共享区回归。噪声跟踪与弱语音保真仍有取舍，不能仅靠降低floor增加降噪。 |
| NN | 默认meeting/FSMN模型，L=4/R=1、64 bands、CMN=38，数据Q20；右上下文增加1帧。构造错误不返回、内部模型分配失败后解引用、零右上下文先读空FIFO；复数功率可能有符号溢出。 | 修复构造链与零上下文读取，功率和权重使用无符号宽域；默认NN Reset输出等价通过。弱语音、非语音声音及不同噪声域仍需模型适用性验证。 |
| AGC | 对IFFT的512-sample窗处理，之后才OLA输出256 samples；活动输入是NN mask平方均值的Q24量，不是独立语音分类器。New空参数路径不安全，多处参数注释错。 | 修复入口；纠正注释，实际T1/T2=-60/-12dB、T2_gain=+6dB、峰值目标=-3dB，数值未变。弱音增益、噪声泵动、响度及切换听感仍待验证。 |
| 输出/切换 | 20帧预热、提交帧只输出目标尾链，使用共同OLA；NN/NR时延不同。接口请求desired为原子，但状态多字段不是并发一致快照。 | 1000轮切换回归通过；保持Feed/Reset/统计读取串行要求。当前HDI活跃reader拒绝直接profile设置，不能把内部atomic load当作泛化线程安全保证。 |

## 确认缺陷及修复证据

1. VAD 小内存分配失败：修复前 UBSan 报 `SEVC_VAD_S` 空指针成员访问；修复后安全返回 NULL。
2. NN 外层分配成功而模型分配失败：修复前 UBSan 报 `NN_STATE_S` 空指针成员访问；修复后检查内部构造返回值并返回 NULL。
3. VAD/AEC/AES/BF/NN/AGC 的空 cfg/locator 入口在读取字段前统一拒绝；测试六种空cfg及上述分配失败场景。
4. NN band energy：实部、虚部均为 S32 最小值时，修复前两个平方相加触发有符号溢出；修复后在 U64 中累加并完成加权移位，恢复到可表示的 S64 贡献，最终沿用原有Q17限幅。
5. NN 的零右上下文分支不再提前访问 ppLastX[0]，支持没有FIFO的描述；默认COMMUNICATION模型R=1不依赖此分支。
6. AGC和参考VAD/NR参数注释修正，只修改解释，不改变数值。

极端频谱测试是数值边界证据，不证明现场PCM已触发该溢出。
没有把未验证的GRU、浮点、多参考或其他配置组合声明为安全。

## BF 资源候选

用相同源码、完整同宏库和评估器，对照默认 BF=1 与 BF=0：

- 1000帧不同双麦输入、参考静音、双向模式切换及Reset的PCM指纹均为 16985685392395738340。
- 默认内存315604 bytes，BF关闭308292 bytes，Host减少7312 bytes（约7.14KiB）。
- 24个冻结四轨样本中，音频、DTD、削波及其他指标一致；只允许 memory_bytes、far_bf_vs_aec_db、double_bf_vs_aec_db 不同。
- BF关闭后的零功率观测不能解释为实际BF抑制收益；未测SSC305 CPU/p95/p99，不直接外推目标资源收益。
- 默认开关仍为1，候选只保存在临时构建中；结束时恢复默认源目录x86对象。

## 产品接入阻断（最高优先级）

- pcr02/pcr02.mk 链接 libs/3rdparty/aispeech/lib，pcr02/dep.mk 未启用 modules/aispeech 源码依赖。
- HDI AI_EXTERNAL_SEVC_ENABLE=1，使用当前三参 New 和 FeedPlanar；公开头仍声明旧七参 New。
- `build/check_public_headers.sh aispeech` 当前失败。
- ARM nm 核验现有预编译 .a/.so：有 New，但没有 FeedPlanar、TailModeRequest、TailStatusGet、FrontendStatsGet 等新入口。
- 预编译a SHA256: 6adb70b2095eac81a3cf9db8a0f11afb639ae8b44926561d0c4714f2bcba5476
- 预编译so SHA256: 1972d9289bb156972c1776cea1a2a508c2ab528d7414616709f29a116837481c

这不是只同步头文件即可解决的问题；需要在同一交付中对齐头、目标库、HDI、产品链接及设备制品身份。
本轮没有替换产品库，也没有证明现有设备实际运行了本源码。后编译app仍不会自动进入已生成image/OTA。

## 验证范围

- 新增 run-stage-contracts：直接对六个模块源码启用ASan/UBSan；11个场景通过。其余静态库模块未整体插桩。
- 新增 run-pipeline-fingerprint：修复前后1000帧PCM完全一致，内存仍315604 bytes。
- NN/AGC单独Reset后50帧输出与新实例一致。
- 原 NR 数值/共享区、AEC通道、Reset及1000轮尾链切换测试通过。
- 修复前后24个四轨样本的全部指标逐项一致；这组默认交互评估不替代NN通话质量评测。
- 六个受影响模块的 SigmaStar GCC11.1.0 ARM定向对象编译通过，不等于产品链接或设备验证。
- 子仓 diff --check 通过；保留既有编译告警。
- 独立review、双麦真实录音、QIVW词首/命中率、通话音质、峰值负载和板端长稳仍缺。

## 身份与复跑

- 默认修复后Host库 SHA256: 7af2fedfc48be7bcee4f1bda056234b9f3e0de689aad83b3500bc9e35d9ea3ca
- BF关闭库 SHA256: cd2935fa2826da75302253df83f93ea1ece16ba06a00140420a02376f9dec0b1
- VAD source SHA256: 66b79ac38a52c82b101dac8b6821035d443c50f85bf9b370987eaf88d63a98db
- NN source SHA256: 1301c53578874158b124cc348aa6f098e1138b44bacb4d96e6d6cc1dad88d437
- stage test SHA256: fb56c2a3f9952987e5e44a1497aab9907e1a8d5b7a97f7b1789d00356bd26b87

复跑入口：rtk make -C modules/aispeech/tests run-stage-contracts run-pipeline-fingerprint run-nr-numeric run-nr-shared run-aec-channel run-reset-equivalence run-long。
该入口通过共享flock串行清理/构建Host库，不与直接底层x86构建并发。

## 下一优先级与裁决

1. 对齐源码到产品的ABI/链接/制品链，之后才谈设备生效。
2. 验证BF资源候选的目标平台资源与音频一致性。
3. 建立NN/AGC专用语音、噪声阶跃及尾链时延/听感验收，继续AEC/AES真实双麦参考对齐工作。

当前裁决：本轮启用链路源码审查和确定性修复已取得上述证据；产品就绪仍needs-fix。
Runtime Control idle/工件未登记属于会话控制面not_applicable，单列，不覆盖实际源码/构建证据。
仅归档脱敏结论与身份，不存原始音频、日志、二进制或设备端点。
