---
id: pcr02-api-msg-player-uart-crosstalk-validation-20260730
title: PCR02 API消息队列并发创建导致Player/UART串消息验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/reports/2026-07-30-api-msg-player-uart-crosstalk-validation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: engineering-session
  from: 2026-07-30 user-provided serial log and local PCR02 source/build evidence
  source_sha256: 7312d08eee4f99f1480f519c568c3c1dce584916920e45baa4e1e755d631e18b
  temporary_source_retained: false
review_after: '2026-10-30'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- player
- uart
- api-msg
- concurrency
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/reports/2026-07-30-api-msg-player-uart-crosstalk-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/reports/2026-07-30-api-msg-player-uart-crosstalk-validation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: 确认启动期VSAPIMSG_Create并发选中同一槽位会令Player与UART共享消息链表；现场type=2,len=2与Player STOP request=2字节布局完全对应。源码已串行化槽位创建并通过API和整机链接，设备MD5部署及1000次重启HIL待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 API消息队列并发创建导致Player/UART串消息验证
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 API 消息队列并发创建导致 Player/UART 串消息

## 结论

2026-07-30 启动循环中出现的 `start.wait_accept` 与后续
`stop.wait_complete` 并非 Player Open 卡死。根因是
`VSAPIMSG_Create()` 在全局锁外查找和初始化空闲槽位；启动期并发创建
Player 与 UART 队列时，两个独立句柄可能取得同一个
`VSAPIMSG_Elem_t` index，继而共享消息链表。

现场日志提供了字节级闭环证据：Player 清理 STOP 消息为
`s32MsgType=2, u64RequestId=2`；UART 紧邻打印
`queued frame invalid type=2, len=2`。在 ARM 结构布局中，UART 将
Player 消息偏移 0 的 type 读取为 `u8MsgType=2`，并将偏移 8 的
request ID 读取为 `u32FrameLen=2`。这说明 STOP 节点被 UART 发送线程
从共享链表取走，Player 工作线程因收不到 START/STOP 而分别超时。

## 排除项

- `stream=(nil)` 且失败阶段为 `start.wait_accept`，排除 Open 阶段阻塞。
- `VS_TIMEOUT_IMMEDIATE` 在当前 HDI 中走 `sem_trywait`，排除被误当作无限等待。
- 条件变量等待会释放 completion mutex，且完成 ID 在同一互斥体下检查，未发现
  completion mutex 自锁证据。
- 日志字符串为 `start.wait_accept`，排除设备仍运行旧版
  `start.wait_open_complete` Player 逻辑；但日志未记录完整制品 MD5，
  不能据此证明设备与当前本地产物逐字节一致。

## 修复

在 `modules/api/src/api_ipc/api_msg.c` 中把槽位查找、槽位初始化和队列发布
放入同一个全局锁事务；失败路径在解锁前销毁已创建的 semaphore、memory pool
和 queue。Player 超时、Open 取消点及 Sensor 状态机不因本修复改变。

## 验证

- `rtk make modules/api_obj_all -j20`：通过。
- `rtk make pcr02_app_all -j20`：通过，输出 `make: ok`。
- `rtk git -C modules/api diff --check`：通过。
- 本地产物：`out/arm/app/prog_pcr02`，
  MD5 `28b53ddb3ce2b2df232b1fbf6b78ef05`。
- 本轮生成物 BuildID 仍为
  `9b9a505e36d333f7ab511db816a02748394891ea`，增量链接前后未变化，
  因此部署验收必须同时核对 MD5，不能只看 BuildID。

## 未闭环项

尚未部署该 MD5 到设备，也未完成重启压力验证。板端门禁应至少执行：

1. 单次启动 smoke，确认启动音乐正常且无 Player/UART 串消息错误。
2. 5～10 次短循环。
3. 1000 次强制重启长循环，统计
   `start.wait_accept`、`stop.wait_complete` 和
   `queued frame invalid type=2, len=2` 均为零。
4. 每轮记录设备安装制品 MD5；出现异常立即停止扩大测试并保留完整日志。

在上述 HIL 完成前，只能声明根因闭环、源码修复和本地构建通过，不能声明板端
问题已经最终解决。
