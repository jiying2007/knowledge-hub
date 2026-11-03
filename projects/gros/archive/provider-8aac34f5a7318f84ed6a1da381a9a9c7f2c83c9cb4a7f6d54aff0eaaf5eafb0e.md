---
id: provider-8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e
title: wifi_loss_wong 02:04 离线：定时OTA接管与版本身份异常
kind: debug-record
domain: projects/gros
path: projects/gros/archive/provider-8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e
  source_sha256: c63febaf93fb342cbba5edf5067c843d7399e5549e29ed54512c56ccf79cf9d4
  temporary_source_retained: false
review_after: '2027-01-14'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/gros/archive/provider-8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gros/archive/provider-8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-16'
updated_at: '2026-10-16'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-16'
manual_validation_pending: true
summary_zh: '- captured_at: 2026-10-16 - subject: project:gros - scope: 项目现场离线日志分析；只读源码核对，无设备操作、源码修改或提交。 -
  status: reviewing candidate - 结论置信度：OTA 接管导致业务退出为高置信；固件内容身份不一致为确认现象，错包或元数据陈旧仍待核验；短时 Sensor 异常底层根因为候选。'
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: gros
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: 8aac34f5a7318f84ed6a1da381a9a9c7f2c83c9cb4a7f6d54aff0eaaf5eafb0e
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
---

# wifi_loss_wong：2026-10-16 02:04 设备离线分析

- captured_at: 2026-10-16
- subject: project:gros
- scope: 项目现场离线日志分析；只读源码核对，无设备操作、源码修改或提交。
- status: reviewing candidate
- 结论置信度：OTA 接管导致业务退出为高置信；固件内容身份不一致为确认现象，错包或元数据陈旧仍待核验；短时 Sensor 异常底层根因为候选。

## 结论

用户报告的 02:04 离线对应 02:00 定时 OTA：Task 下载目标版本 1.4.3 的包，02:04:15 启动 prog_ota，02:04:16 主程序开始有序退出，02:04:20 以 exit_status=0 完成。后续应用重新启动，读取 OTA SUCCESS，并在 02:07:58 从 Task 侧观测到 MQTT/RTM 恢复。这次主离线应归到 OTA 接管/应用不可用窗口，不应归为已证实的 WiFi 物理断链。

按主程序开始 shutdown 至 Task 收到 mqtt=true 计算约 222.091 秒，即 3 分 42 秒；这是本地业务证据窗口，不等于 APP 或云端精确离线持续时间。

## 证据时间线（日志本地时间 +08:00）

| 时间 | 事件 | 来源 |
| --- | --- | --- |
| 02:00:00.544 | daily scheduled task triggered, hour=2, minute=0 | task/task.1.log:1735 |
| 02:00:00.546 | 电量 100%，通过升级门槛；RSSI 检查被 bypass | task/task.1.log:1736-1737 |
| 02:00:03.360 | EventOtaRequest，目标 1.4.3，当前 1.4.2 | task/task.1.log:1765 |
| 02:00:03.402 | IoT OTA 下载启动 | task/task.1.log:1782 |
| 02:04:09.179 | Task 仍查询到相同网络，RSSI -38dBm | task/task.1.log:4852 |
| 02:04:12.217-12.253 | 下载 100%、success=true，进入 upgrading、禁用 RTSA | task/task.1.log:4890-4895 |
| 02:04:15.429-15.454 | 启动 prog_ota，记录等待子进程停止父应用 | task/task.1.log:4937-4938 |
| 02:04:16.360 | 主应用开始有序 shutdown | app/app.log:2728 |
| 02:04:17.597 | IoT deinit 开始 | app/app.log:2741 |
| 02:04:17.759 | Sensor WiFi shutdown fence，connect_api_running=false | sensor/sensor.1.log:4822 |
| 02:04:20.073 | 主应用 exit_status=0 | app/app.log:2758 |
| 02:07:05.262-05.679 | supplicant p2p/wlan0 TERMINATING，WoWLAN deinit | wpa_supplicant/wpa_supplicant.log:1097-1104 |
| 校时前启动段 | 新应用启动，Sensor 关联恢复、linked=true/state=6，RSSI -26dBm | app/app.log:2759；sensor/sensor.1.log:4914-4920 |
| 02:07:49.527 | Task 发布读取到的 OTA SUCCESS，exec_status=5 | task/task.1.log:5094-5096 |
| 02:07:55.094 | 初始化阶段 mqtt=false | task/task.1.log:5117 |
| 02:07:58.451 | mqtt=true、agora_rtm=true | task/task.1.log:5127 |
| 02:08:02.111 | 所有应用模块初始化完成 | app/app.log:2778 |

## 各层解释

Task 提供直接原因链：定时触发、版本比较、下载成功、启动独立升级器、交接。主应用提供有序停止与正常返回证据，Sensor 的停止发生在应用 shutdown 之后，不能将该停止反推为离线源头。02:00 导航 executeSysResetOnCharging 后仍持续运行，所打印动作是导航状态/传感数据复位，没有证据表明它在此时重启系统。

supplicant 文件跨历史多段，混有未校时数值与 Unix epoch。1792087625.262147 换算为 +08:00 的 2026-10-16 02:07:05.262147；这条 TERMINATING 比主应用开始退出晚约 169 秒。相邻启动段随后完成同一匿名 AP 的认证。目标窗口无对应 CTRL-EVENT-DISCONNECTED 或认证失败记录，因此不能把终止清理或旧历史 reason=0/3 事件归因于本次 02:04 离线；日志未记录也不构成绝对无底层故障证明。

IoT 轮转文件最早为 05:22，02:04 窗口已缺失；本次 MQTT 恢复证据来自 Task 的跨模块状态订阅，不能冒充 IoT callback、broker 或 APP 回执。common 日志 02:04:06 共享帧诊断正常；Bridge 02:04:15 仍有采样，进程 RSS 约 66.60MB、系统 available 约 53.43MB。该采样不支持将此时正常退出归因为 OOM，但缺内核日志不能全面排除其他系统事件。

新启动前出现 1970 时间戳，待联网校时后回到实际日期；不能用这些绝对值计算启动耗时。升级前有 boot_id 记录，升级后旧 Sensor banner 无新的 boot_id 诊断；现场未提供 prog_ota、kernel/dmesg、安装二进制及包 manifest/hash，不能独立确认整板或内核重启、每个刷写阶段和耗时，更不能从 SUCCESS 文本断言安装包与云端目标版本完全一致。

## 单独发现：升级目标与运行内容身份不一致

- 目标：Task 升级请求 1.4.3，升级前比较 current=1.4.2（task/task.1.log:1765）。
- 恢复后：Task banner version=1.4.0、commit=28a9ae1e、日期 2026-09-24；后续版本比较继续使用 current=1.4.0（task/task.1.log:4965 附近、5126）。
- Sensor 升级前 banner 为 v1.4.0-14-g6935f84，日期 2026-09-30（sensor/sensor.1.log:1145 附近）；恢复后为 v1.3.6-4-gcaa55ae，日期 2026-09-24（4846 附近）。
- 随包采集的 customer/etc/version.ini 仍标 version=1.4.2，不能仅据其确定当时安装二进制身份。

已确认运行日志身份发生改变且与目标标签不一致。候选为包内容较旧、版本元数据未更新或制品组合不一致；缺实际下载包、manifest、应用/库 BuildID/hash，暂不能判定确实降级或选错发布对象。核验应绑定云端目标版本和包 hash、包内各模块 commit/BuildID、最终安装文件身份。OTA SUCCESS 与该身份核验是两个验收层。

## 单独发现：32 次瞬时 Sensor 状态异常

逐行配对 sensor.1.log 的 linked=false/state=11 与随后 linked=true/state=6，得到 32 次，持续 1.012331 至 1.029390 秒：

- 10-15 22:38:30 至 22:54:29：20 次。
- 10-16 01:08:53 至 01:14:34：12 次。

当前 api_wifi.h 枚举中 state=11 为 WIFI_STATE_ERROR，并非单凭状态就证明 DHCP 或二层断链。现场缺该版本 API 二进制及详细状态观测原因，因此底层仍保留候选。

Task 保留的第二组窗口中，有 12 次 mqtt=false/true 完整配对，约 2 至 3 秒，均紧随 Sensor 状态异常；例如 Sensor 01:14:33.216 false、01:14:34.238 true，Task 01:14:33.268 mqtt=false、01:14:36.289 mqtt=true（task/task.1.log:1412-1416）。Task 同时将质量标为 LINK_DOWN，附近 RSSI -18~-19dBm，说明这些状态不能直接用弱射频解释。IoT 同窗口日志缺失，不能确认 MQTT 的主动断开调用方或网络采样失败的具体来源。

02:04 前最后一次该类异常发生在 01:14:33，恢复在 01:14:34，距 OTA 退出约 50 分钟；02:04:13 Sensor 仍记录 state=6。因此不得将 32 次瞬时异常与 02:04 OTA 交接混为一个故障。

本地三仓已提交的瞬时 IPv4 复核/unknown 语义/内核 IPv4 查询，是针对相似状态误判放大链路的候选治理；现场是更早构建，无这些修复已部署的证据。修复不能消除 OTA 停应用窗口，也不能据此宣布此次包已验证。

## 建议与未决证据

1. 02:04 事件按定时 OTA 业务中断归档；产品端将升级中/恢复中状态与普通离线明确关联，记录 transaction、触发来源、目标版本、阶段及恢复结果，避免将预期中断作为无原因离线。
2. 优先核对目标 1.4.3 与实际包和运行模块身份。保留 SUCCESS 的现有语义，单独检查版本、制品和恢复证据，不改写为已证明健康或身份一致。
3. 升级前已采样到 RSSI -38dBm，但升级门槛日志称 RSSI 尚未报告而 bypass，提示门槛输入或状态同步需后续审查；它不是此次正常停应用的直接根因。
4. 大量 AI detection callback size=9 错误发生在升级过程中（task/task.1.log:4900 等），另作业务消费/状态处理审查；本日志不足以归为网络故障或崩溃来源。
5. 如需精确分解 3 分 42 秒窗口，补 prog_ota 日志、包 manifest/hash、内核启动证据、IoT callback/云端会话及 APP 时区/离线时间。无需为了确认已有 OTA 退出链而重启或修改现场。

## 证据文件 SHA256

| 文件（相对 wifi_loss_wong/data/log） | SHA256 |
| --- | --- |
| prog_pcr02/app/app.log | 67846ee25b3a8d5e080ca5c21b18f86868f93224939d85e04e48fec392bdb1ab |
| prog_pcr02/task/task.1.log | 2d7760fbd436e717781d816784d6d676eb6058cc47b9ac95d10d38d473417832 |
| prog_pcr02/sensor/sensor.1.log | e6fe08c23fd779ad54e01433ddb570d4ca63f0db78487eedcdc52669526ed990 |
| prog_pcr02/iot/iot.1.log | 5dc1cc866a6b5b7128d5df602895bb96329f1d6d37c3a2fcdd24c853afcdd4d1 |
| prog_pcr02/bridge/bridge.1.log | db445dd50d5b4a938f2f70035f53b912cd569775ab632634cf76ab590aa3630c |
| wpa_supplicant/wpa_supplicant.log | 0c934689f3c366d12411aaa32ea9fe01041e4451338678ee10e9ce5804e92fd8 |

本记录仅保存脱敏结论、行号与摘要 hash，不包含原始日志、SSID/BSSID、设备标识、私有端点、包下载地址或配置凭据。源码未修改，未执行构建、设备 HIL 或发布。
