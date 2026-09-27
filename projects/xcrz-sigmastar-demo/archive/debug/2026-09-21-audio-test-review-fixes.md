---
id: audio-test-review-fixes-20260921
title: 音频采集工具实现审查与修复
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-review-fixes.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: ephemeral-file-capture
  from: ephemeral-content-sha256:267e1e49b9a0832559ed818c402b9d6c9d5893aa3bcab17ae4ef08642690b1d0
  source_sha256: 267e1e49b9a0832559ed818c402b9d6c9d5893aa3bcab17ae4ef08642690b1d0
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-review-fixes.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-audio-test-review-fixes.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: false
manual_validation_pending: true
summary_zh: 修复profile门控、控制阻塞、RPM溢出及目录句柄泄漏，扩展实际worker回归
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# 音频采集工具实现审查与修复

项目：workspace://xcrz-sigmastar-demo；范围为app_audio_test，未改算法参数或部署设备。

## 已确认问题与修复

1. profile等待退出只检查ready，错误active profile也可能放行：同时校验active profile及采集错误。
2. 场景结束判断先于错误检查，最后一次调度的异常可能被覆盖：错误/超时优先于正常结束。
3. AO排空在控制线程可能等待数秒，引发调度超时并延迟响应：移入实际播放worker，完成状态在排空调用后发布。
4. 终端提示阻塞会拖住控制循环：独立非阻塞描述符，仅写终端或管道；普通文件/满管道记录console_prompt_dropped，不在控制循环写盘。
5. RPM校验前对有符号值取反可能溢出：校验后转换；初始化拒绝重复owner并清除旧遥测，避免跨会话假就绪。
6. 保存失败和创建目录后续失败可能遗留目录fd：统一释放；增加采样、帧和事件上界检查，完整结果要求实际profile就绪。
7. 预分配采用统一显式预触页，覆盖音频和帧元数据，移除重复的音频全量清零，降低首次写入缺页开销。

## 新鲜验证

- make -C app_audio_test/tests test，退出0，ASan/UBSan。
- 实际runtime fake clock覆盖9种生命周期路径，包括错误profile、最终tick错误、结束时调度超时。
- 实际播放worker覆盖3种时序乘5种正常/故障模式，另验证满管道和普通文件输出拒绝。
- 实际motor adapter验证INT_MIN/INT_MAX拒绝、右轮方向字节编码、允许非零滑行、重复owner拒绝、旧遥测拒绝。
- 核心测试验证保存成功/失败后fd计数不增长，非法记录计数拒绝。
- make NC=1 app_audio_test_app_all -j4，退出0。
- tools/ai.sh check退出0，扫描15份C/头文件；格式仍与HDI/API/APP一致。
- 控制台堵塞测试证明本工具提示路径不等待恢复，不证明所有底层SDK调用无阻塞。

## 制品与边界

- BuildID：57561baa32d9ed3d6072f27aafeeca59170cf5ef。
- SHA256：69ccc83c1f9e61eeb9759cd9b3456bc606f99b63c12b5d3d6ed69084967f8cdb。
- 仅自审和Host/ARM构建，未独立代理审查、未进行设备采集/播放/运动。
- 零速仅TX，不锁止、不要求轮速归零。AO排空返回不能证明声学输出已完成。
- 真实SD文件系统、拔卡/满盘、实际音频通道、CPU/RSS、下层失联和听感仍需板端验证。
- 本记录为项目reviewing candidate，不晋升通用标准。
