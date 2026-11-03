---
id: provider-b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad
title: PCR02 WiFi复审三项问题最小修复与验证
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad
  source_sha256: b8fd2665513af928e5cef61ab6f0c8ca0552a2528c59dd562f5b6dde5d4056e7
  temporary_source_retained: false
review_after: '2027-01-17'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/gros/validation/provider-b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 日期：2026-10-19。范围：上轮F1-F3；用户要求不过度设计。没有修改Task、公共消息结构或既有音频改动，没有提交、推送、设备写操作或部署。候选状态：reviewing。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: b34ef66ea18fae66cda63ed17b568e65bdde2cbfa4d511a1cd47d5872b244bad
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- PCR02 WiFi复审三项问题最小修复与验证
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# WiFi/API/Sensor 复审问题最小修复候选

日期：2026-10-19。范围：上轮F1-F3；用户要求不过度设计。没有修改Task、公共消息结构或既有音频改动，没有提交、推送、设备写操作或部署。候选状态：reviewing。

## 契约与修改

- 唯一执行owner仍为现有WPA事件worker。失败完成时STATUS不可用或关联已变化，停止客户端但不清除接口地址。停止未确认退出时保留按地址族记录的pending mask，busy查询只读；worker下一轮重试并在确认退出后释放pending、再次通知失败。进程持续不可退出时保留busy，不伪造成功。
- CONNECTED繁忙时合并成一个pending标记。沿用已有poll，STA周期改为1秒，并在事件处理后也执行pending检查，避免持续扫描事件饿死待处理工作。空闲后读取当前STATUS，仅对COMPLETED关联启动DHCP；查询失败保留标记，断连/终止/worker退出后清标记。没有新增线程、队列、对外重放API或通用状态机。
- API异步事件消费时，若当前已不是DHCP_FAILED，丢弃排队的旧DHCP_FAILED通知。Sensor后台失败状态及事件均先复用现有快照刷新，以当前状态决定在线信息，不再将旧通知作为新的权威状态。保留原有前台连接失败和凭据恢复逻辑，没有扩展revision/epoch公共协议。

## 验证

- WiFi：rtk make -C tests/wifi_recovery_lifecycle test，7个ASAN/UBSAN程序及1项release contract通过。新增清理重试、busy仅由worker释放、单次CONNECTED后无第二事件仍获取DHCP、STATUS暂时失败保留pending、旧失败事件在新在线状态下不交付等用例。
- Sensor：rtk make -C tests/sensor_wifi_service test，最终退出0，2个ASAN/UBSAN程序通过。新增旧失败状态/事件消费时当前快照已在线的行为断言，保留真实失败的离线断言。fixture补齐WPA2_PSK前置条件，真实终态用例同步当前快照。
- 结构契约：rtk python3 tests/contracts/test_wifi_security_contracts.py，22/22通过。
- ARM：从实际根Makefile dry-run提取参数，SigmaStar GCC/G++ 11.1.0编译linux_sta.c、linux_common.c、api_wifi.c、sensor_wifi_service.cpp，4/4通过，仅写/tmp对象。第一次编排预期6个对象而make只调度4个实际变化对象，断言未通过；按实际4个修改生产单元修正编排后退出0。没有库或应用链接。
- API/Sensor tools/ai.sh doctor及check通过；WiFi/API/Sensor及父仓git diff --check通过。实现代理做完整增量及生命周期复审；不是独立reviewer/owner放行。

## 源码SHA256

|文件|SHA256|
|---|---|
|linux_sta.c|b75aa065fa62e9338ca70a63d17893bfaf3f0ab66ea5ea60006ab46f4d2791eb|
|linux_common.c|0b1264714035e27b0774a7f215b4970764bcd2f26a78f8f2aa2d70938deff06c|
|api_wifi.c|64e115fe7ce02ed79de8226799d8dc96093eb86e35c9469ed7616f62a578cb0d|
|sensor_wifi_service.cpp|b0fad09d459965ae1cce774deb50782817f6bce0ba4235f9880c9f8139a2f959|

## ARM对象SHA256

|/tmp文件|SHA256|
|---|---|
|wifi-review-fix-linux_sta.c.arm.o|56c1d8a830a3671ab9d05d9eda0d8549999aef5e9c84dd86bb3b8438304746a6|
|wifi-review-fix-linux_common.c.arm.o|ddc09b75b8e4b91a14da83644a4dccde864f25204eac13d0fbd2d701327cb208|
|wifi-review-fix-api_wifi.c.arm.o|4aa144722aa7aa48a14dca948e39bc1b56f38404e71324cc9873cb071512f8fa|
|wifi-review-fix-sensor_wifi_service.cpp.arm.o|648f623942f6501581b0489acaecf90f1f13921b3195879855ca23774c0c06ae|

## 边界

F1、F2、F3在本次明确的单STA、通知作为刷新提示契约下完成修复及Host复验。没有新发现的阻断项；此结论仅为本地源码验证，不构成独立审查或产品放行。

本次仍沿用平台单STA客户端、进程名清理机制，不将其扩展成多接口/多DHCP owner框架。Host覆盖生产函数及调用边界，真实supplicant socket/poll时序、内核不可退出进程和漫游仍需板端验证。没有关闭busy超时后强行重置，没有改变Task的ACK冷却或NetCfg策略。
后续制品须一致重建WiFi/API/Sensor并核对最终链接和安装身份；Host/ARM对象不等于设备生效。后编译app不会自动进入已有image/OTA。现有用户脏改保持，回退应只反向移除本次目标补丁，不能整体reset工作区。
