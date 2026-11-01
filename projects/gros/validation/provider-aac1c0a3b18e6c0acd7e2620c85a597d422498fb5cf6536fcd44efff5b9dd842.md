---
id: provider-aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842
title: PCR02 WiFi DHCP终态与恢复修复本地验证候选
kind: validation
domain: projects/gros
path: projects/gros/validation/provider-aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842
  source_sha256: 125dd6abbe2df3bc905fc6dbc4ec73b417c3f8d138ae05c1afc2f4d05a0c51f3
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
- projects/gros/validation/provider-aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/validation/provider-aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-19'
updated_at: '2026-10-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-19'
manual_validation_pending: true
summary_zh: 日期：2026-10-19。范围：WiFi、API、Sensor的本地源码、Host测试和ARM对象。用户明确排除Task。状态：reviewing candidate；未作产品放行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: aac1c0a3b18e6c0acd7e2620c85a597d422498fb5cf6536fcd44efff5b9dd842
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- PCR02 WiFi DHCP终态与恢复修复本地验证候选
related:
- projects/gros/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 WiFi DHCP终态与恢复修复验证候选

日期：2026-10-19。范围：WiFi、API、Sensor的本地源码、Host测试和ARM对象。用户明确排除Task。状态：reviewing candidate；未作产品放行。

## 问题与证据边界

现场漫游后WPA关联成功，而上层长期停留OBTAINING_IP，后续恢复网络。源码确认两项恢复缺口：WiFi在STATUS查询或解析失败时可能退出而未给出DHCP终态；API未处理DHCP_TIMEOUT及DHCP_TIMEOUT状态，也未从DHCP_FAILED进入已有重连链。当前修复针对这些可确认缺口。现场首次DHCP失败的底层触发原因、307秒事件间隔对应的实际责任计时器仍未由设备制品及完整运行证据确认。

## 最终修改

- WiFi：单一DHCP退出点补齐START后的成功/失败终态；STATUS使用有界查询；完成时复核关联身份，旧操作不清除新关联地址、不缓存错误关联租约；清理先于终态通知，清理失败继续报告busy。新增只读busy快照，连接准入避免已有DHCP/清理owner；它不是原子资源预留或全局无线互斥协议。
- WiFi：修正默认地址位掩码；默认模式即使有IPv6，缺IPv4仍获取IPv4；同SSID不同BSSID重新获取IPv4；复用租约不刷新租约获取时间。
- API：映射DHCP事件和状态失败；重复及已离开OBTAINING_IP后的失败不覆盖当前状态；条件状态修订检查覆盖busy查询期间的新关联竞争。60秒单调时钟watchdog仅在未暂停且后端空闲时交付FAILED，busy时不强行重置。
- API：DHCP_FAILED参与原有后台重连及pending查询；busy时拒绝新连接。
- Sensor：后台DHCP失败清除当前在线快照与unknown确认状态，保留凭据和已知网络，进入既有恢复链，不给整个SSID添加前台连接失败冷却；等待API重连结束后才允许恢复扫描。过渡状态日志按状态变化及30秒限频。
- 测试：新增真实WiFi DHCP函数故障注入，扩展API回调和Sensor后台恢复测试。现有Sensor测试fixture及结构契约同步当前已存在的known-network/persistence接口命名和参数，避免陈旧fixture遮蔽验证。

## 仓库身份与已有脏改

父仓HEAD：90cfa77a4b8f34c0999b7f06529b3c5fd666585d。
WiFi独立仓HEAD：623620a50f3461fdfa42a6000fd9547baed4b3be。
API独立仓HEAD：5558299b5ee94976d9e78cfe6be25499acc28c0d。
Sensor独立仓HEAD：581d092a66b9ad38fd986a08fe622498b267b777。
三个子仓位于dev/wifi_fix。API已有6项音频暂存修改，Sensor已有audio_player.cpp/.h修改及父仓大量已有改动，均保留。本次没有commit、push、stage、设备写操作或替换现有库/app。测试目录在父仓为未跟踪目录，独立模块改动应分别审查纳管，不能只提交父仓指针即视为交付。

## 新鲜验证

1. `rtk make -C tests/wifi_recovery_lifecycle test`：退出0，7个ASAN/UBSAN程序通过，另1项Python release contract通过。覆盖提前STATUS失败、无IP冷启动、同SSID漫游、DHCP失败清理、残留owner、关联改变、复用租约、默认IPv4及IPv6缺项、busy重入、API终态映射、重复失败、新状态修订竞争与watchdog边界。故障注入中的错误日志是预期结果。
2. `rtk make -C tests/sensor_wifi_service test`：退出0，2个ASAN/UBSAN程序通过，含真实service生命周期及后台DHCP_FAILED恢复准入。
3. `rtk python3 tests/contracts/test_wifi_security_contracts.py`：22/22通过；这些为结构契约，不能替代行为测试。
4. ARM对象：从根Makefile的`make -n NC=1 modules/wifi_obj_all modules/api_obj_all modules/sensor_obj_all`提取真实编译参数，以SigmaStar GCC/G++ 11.1.0编译5个受影响生产翻译单元，输出至/tmp。linux_sta.c、udhcpc.c、wifimg.c、api_wifi.c、sensor_wifi_service.cpp全部退出0。WiFi保留原有组件警告，未将其记作新增失败。未执行全量构建或库/app链接。
5. WiFi/API/Sensor子仓及父仓`git diff --check`通过。实现代理完成终态、清理顺序、busy准入、凭据保留和晚到事件差异复审；没有独立审查代理结果。

## 源码SHA256

|文件|SHA256|
|---|---|
|linux_sta.c|649b0415e6257ece499df2635f7c4bdbd5c871127b857c9f43b1bedb0005ff72|
|udhcpc.c|f8d8a05e02183e670f7b3475c266cce552aa6c22a955d5f1013852834d908386|
|wifimg.c|f5f3c9d0bb9b324ac39e9385e727562a2772c449e0d2d889421247a2f2b52b45|
|api_wifi.c|c8641563b34911d3248b86dec7bee8ffe5f0eaa20b3cf72111f57176c92d48ec|
|sensor_wifi_service.cpp|a9a57364591c16822a73ffac9bc01f09ee9fc34fd3234d91cfb7a8ce4af6f76b|

## ARM对象SHA256

|/tmp对象|SHA256|
|---|---|
|wifi-dhcp-fix-linux_sta.c.arm.o|850b2a7ef8b678adf85b516aa7d4e961481ad27800198c74a19364a08817799c|
|wifi-dhcp-fix-udhcpc.c.arm.o|69453862d7411e8845ceed85a1d24c3f7639fc101722d7f26ab89b7316fee1c4|
|wifi-dhcp-fix-wifimg.c.arm.o|bd3257358b84737a2eca5e8f0385342b29f1ade26718d07ee464a190482b6466|
|wifi-dhcp-fix-api_wifi.c.arm.o|4fe9fd9a4ea46d3462f64b360766c821331d1a335faea032b0633be545be33dd|
|wifi-dhcp-fix-sensor_wifi_service.cpp.arm.o|5467328a66a1ab64d64cd275c67b9c004a775435914a21a9259f369f56c3f7e1|

## 后续制品与板端验收

新增WiFi符号wifi_sta_dhcp_is_busy要求WiFi与API一致重建、链接；Sensor同批更新。stop_udhcpc为内部返回值契约调整。不应将新API与旧libwifi混装。之后须核验实际链接路径、最终app及安装库身份，再验证冷启动、同SSID不同BSSID漫游、DHCP无响应、恢复后MQTT与充电场景。此处没有产出已链接候选、安装身份或HIL结果；后编译app不会自动进入既有image/OTA，需按后续任务重生成制品。

Task中的失败ACK冷却和NetCfg退出策略按用户范围未修改；即使本次底层恢复缺口修复，仍需单独评估这些业务策略。busy持续时保持阻止恢复而非强行终止；残留DHCP进程扫描沿用现有进程名称机制，板端需验证实际进程退出行为。没有凭据、现场原始日志或二进制进入本候选正文。
