---
id: audio-test-capture-integrity-review-20260921
title: 音频采集完整性与退出取消复审
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-capture-integrity-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:be79c1114616b25767261bed6a3e0a21e9213655f6715b689c459b52fcd59590
  source_sha256: be79c1114616b25767261bed6a3e0a21e9213655f6715b689c459b52fcd59590
  temporary_source_retained: false
review_after: '2026-12-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- debug-record
- capture
- manual-validation-pending
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-capture-integrity-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-capture-integrity-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: false
manual_validation_pending: true
summary_zh: 修复预热掩盖缺尾及播放取消结果误判，v2逐帧校验通过Host和ARM验证
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频采集完整性复审

范围：workspace://xcrz-sigmastar-demo/app_audio_test；本轮未部署或运动。

## 确认问题

此前完整性依赖总采样数，预热数据可能补足正式场景缺失的尾段；记录中的输出无效标志、重复序号和配对PTS未参与最终判定。
退出时在UART清理后才通知播放取消，且播放随后结束可能掩盖进入退出时尚未完成的状态。

## 修复

- 新增validation.c，在reader退出后线性扫描记录，无实时回调额外计算或分配。
- 新增唯一scene_end标记；与scene_start共同限定正式窗口。
- 检查阶段、epoch、序号、PTS步进、采样偏移、原始输入与输出二比一配对、总数一致性。
- 正式窗口输出必须有效，首尾覆盖和窗口内样本数达标；预热不能补齐正式尾段。
- session.json版本升为2，frame_validation给出0至-6的明确错误分类；旧v1的complete不等价。
- 退出先发播放取消，再清理UART；进入退出时未完成播放固定失败，随后取消完成不升级成功。

## 新鲜验证

make -C app_audio_test/tests test退出0，ASan/UBSan；保留原有核心、9类生命周期、实际播放worker和motor adapter回归。
新增完整窗口、无效输出、重复序号、错误偏移、错配PTS、时间倒退、尾段缺失及起止标记异常测试。
实际保存正负数据包；独立JSON读取确认v2：完整样本352000、complete=true、frame_validation=0；
缺尾样本335872仍超过20秒总量，但complete=false、frame_validation=-6。
播放取消helper验证未完成不能因随后完成而升级成功。
ARM应用构建通过；规则/边界/格式一致性检查通过。

## 制品与限制

BuildID：afa82d01e13e7656ce1a6c415e9ddea79d542e68。
SHA256：5699e9ab5bed38dd0ea9fc074c67b7f329edc67c3303cd586bfbc49cf76e97fd。
Host合成数据只证明结构判断，不能证明真实参考、中文双讲、设备播放排空或物理运动。
零速TX允许滑行，语义未改变；设备及SD卡故障验证仍待现场执行。
本记录为项目reviewing candidate，不晋升团队标准。
