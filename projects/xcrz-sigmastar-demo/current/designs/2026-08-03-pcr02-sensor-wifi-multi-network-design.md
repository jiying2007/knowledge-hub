---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
maturity: null
security_classification: team-internal
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-sensor-wifi-multi-network-design-20260803
title: PCR02 多 WiFi 存储与切换完整实现方案
kind: architecture
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/designs/2026-08-03-pcr02-sensor-wifi-multi-network-design.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: repository-design
  from: xcrz_sigmastar_demo/多WiFi存储与切换实现方案.md
  source_sha256: c888606fc3f433be950cfe6474c6b78ed6adf2432b135d8871631979e2c78c63
review_after: '2026-11-07'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; reviewing capture does not authorize active promotion or owner decision
tags:
- pcr02
- wifi
- sensor
- api
- multi-wifi
- transaction
- design-review
validation_refs:
- projects/xcrz-sigmastar-demo/current/designs/2026-08-03-pcr02-sensor-wifi-multi-network-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: code-inspection-and-requirements-implementation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/designs/2026-08-03-pcr02-sensor-wifi-multi-network-design.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-07'
last_verified: '2026-08-07'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-07'
manual_validation_pending: true
summary_zh: PCR02 多 WiFi 采用 Task 产品编排、Sensor 操作编排、API/WiFi 原子持久化；统一 5 条容量、两阶段配网、非破坏切换、操作关联和安全验收边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Sensor/WiFi 多 WiFi 存储与切换方案评审
- PCR02 多 WiFi 完整实现方案
---

# PCR02 多 WiFi 存储与切换完整实现方案

## 摘要

本文归档 PCR02 当前多 WiFi 目标架构及其代码核对结论。正式源文档位于源码仓 `多WiFi存储与切换实现方案.md`；本记录提炼可长期复用的职责边界、事务语义、风险和验收门禁，不替代源文档或代码。

目标架构为：Task 管理配网、绑定、弱网门禁、视频锁和 UI/语音等产品流程；SensorWifiService 管理 WiFi 请求协议、单操作队列、事实状态和领域动作执行；api_wifi 与 wifimg 管理容量、凭据、supplicant network 和原子持久化。supplicant saved-network 是唯一持久化真相源。

本记录状态为 `reviewing`。它不表示当前固件已经实现多 WiFi，也不构成 active 架构决策或产品策略签收。

## 原始来源

- Source：`xcrz_sigmastar_demo/多WiFi存储与切换实现方案.md`。
- Source hash：`c888606fc3f433be950cfe6474c6b78ed6adf2432b135d8871631979e2c78c63`。
- Code baseline：根仓 `dev/pcr02@f9b9b075`；`sensor@3006f8f`、`api@dcc8b0f`、`wifi@dbfed81`、`app@a35b275`。
- Captured at：2026-08-07。
- Provenance：用户要求基于当前 Sensor、App、API、WiFi 等代码更新正式方案并归档。
- Sanitization：未归档密码、PSK、二维码内容、账号、token、设备端点、raw log、binary 或完整会话。

## 适用范围

- 项目：PCR02 / `xcrz_sigmastar_demo`。
- 模块：手机 App/云端适配边界、Iot、Task、SensorWifiService、api_wifi、wifimg、supplicant。
- 场景：扫码配网、绑定提交、saved-network 查询、新增或更新、删除、手动切换、弱网切换、断连恢复、解绑和恢复出厂。
- 产品基线：最多 5 个热点；连接成功以 IP_READY 为准；优质环境连接不超过 5 秒、已保存网络切换不超过 3 秒；失败收敛上限 30 秒。

## 稳定架构结论

### 1. 职责边界

- Iot 负责云协议、受理回包、最终结果补发和 MQTT 重连，不管理 saved-network，不判定 WiFi 候选。
- Task 负责配网和绑定状态机、弱网持续时间、5 分钟冷却、视频锁、进入配网模式、UI/语音和云错误映射。
- SensorWifiService 负责 `wifi/dev/ctrl`、请求校验、操作串行化、状态采样、API 调用、候选执行和操作结果发布。
- api_wifi 负责 WiFi 领域 API、统一写锁、事务和底层错误映射。
- wifimg 负责 supplicant network-id、扫描、关联、认证、DHCP、prepare/commit/abort 和持久化。
- Sensor 不承担账号绑定、外网/MQTT/P2P 健康、动画、语音、视频锁或产品文案。

### 2. 唯一真相源和容量

- saved-network 只由 WiFi/supplicant 持久化；Task 不再使用 `wifi.toml` 或本地缓存。
- `user_config.toml` 不参与多 WiFi QUERY、DEL 或 SWITCH，并应后续移除明文 WiFi 密码。
- 最大数量为 5。查重、计数、容量预留、提交和释放必须在 API/WiFi 同一事务锁内完成。
- 所有生产写入口，包括首次配网、在线新增、离线二维码和诊断入口，都必须经过同一容量与事务门禁。
- SSID 按原始字节精确匹配，长度按 1～32 字节校验；`network_id` 不是跨重启业务 ID。

### 3. 密码和输入安全

- QUERY、状态、操作结果和日志不返回或输出密码。
- DEL、SWITCH、弱网切换不传密码。
- Sensor/API 只在 ADD 或配网操作期间持有凭据，结束后清零，不保留 `active_password_`。
- 自动重连使用 supplicant saved-network，而不是 API 内存密码。
- SSID 和密码必须安全转义或使用十六进制编码写入 supplicant，禁止直接拼接控制命令。
- supplicant 配置路径必须由运行配置唯一确定；不能同时维护 `/etc` 和 `/data/etc` 两套假定真相源。

### 4. 原子事务

新增网络：容量预留后创建临时候选；达到 IP_READY 才提交，失败删除候选并恢复原网络。

同名凭据更新：保留旧 network-id，使用新临时 network-id 验证新凭据；成功后替换旧配置，失败只删除候选并恢复旧配置。满容量时允许同名更新。

手动切换：选择已保存目标并等待 IP_READY；失败恢复原 network-id，绝不能删除目标 saved-network。

删除当前网络：默认 `FAILOVER_THEN_REMOVE`。只有替代网络达到 IP_READY 后才能删除原网络；没有可用替代网络时默认拒绝。恢复出厂使用独立、幂等的 CLEAR。

### 5. 两阶段配网

- QR 模块只解析凭据并交给 Task，不直接决定绑定或连接，不记录完整二维码内容。
- Task 以 `PENDING_UNTIL_COMMIT` 发起配网。
- WiFi 达到 IP_READY 后仍保持 pending；云绑定成功才 COMMIT。
- 无外网或 3 分钟绑定超时执行 ABORT，删除本次候选并恢复旧网络；首次配网没有旧网络时回到配网模式。
- 已绑定设备断网后扫描其他用户二维码，只使用网络信息，不改变绑定关系。

### 6. 自动选择和弱网

- 开机由 Sensor/API/WiFi 扫描 saved-network 并连接信号最强的可用候选；隐藏网络使用定向扫描。
- 断连后 WiFi 在 3 秒窗口重连原网络，Sensor 再用 10 秒窗口尝试其他 saved-network；均失败时由 Task 进入配网和退避扫描。
- Task 使用迟滞判定：RSSI 小于等于 -75 dBm 持续 15 秒进入弱网，RSSI 大于等于 -70 dBm 恢复，中间区保持原状态。
- Task 管理 5 分钟冷却和视频锁；通过门禁后下发最小 RSSI 增益 5 dBm。
- Sensor 使用同一扫描快照从 saved-network 交集中选择候选；没有更优网络时保持当前连接。

### 7. 操作关联和结果语义

- 请求 Header sequence 作为 request_id，Ack 必须原样回显。
- Sensor 为变更操作生成 operation_id，并保存终态结果用于超时补查和幂等重试。
- “accepted”只表示进入队列；“final + succeeded”才表示最终成功。
- 最终结果通过本地 operation result 事件发布，并支持按 operation_id 查询。
- 可解析的失败 Ack 是业务失败，不应被 Request 层误判为通信失败。

## 当前代码证据

1. `wifi_ctrl.proto` 已定义命令 0～9，但 `SensorWifiService::handleCtrlMsg()` 只实现 0～4。
2. Sensor 当前长期保存 pending/active 密码，并在新凭据到达时先断开当前网络。
3. `VSAPIWIFI_SaveNetwork()` 只写内存，`GetSavedNetworks()` 还会伪造 WPA2 安全类型。
4. wifimg 当前连接或自动切换失败会删除目标网络，同名凭据更新无法保证旧配置回滚。
5. WiFi 配置 dump 和二维码日志存在凭据泄露风险。
6. wifimg 密码缓冲区、BSSID 解析和 REMOVE 命令缓冲区不满足兼容性与内存安全要求。
7. `modules/app` 诊断 WiFi provider 直接调用 API，绕过 Sensor 唯一写入口。
8. 当前仓只提供预编译 Task/Iot 库；符号证据未显示完整多 WiFi处理能力。

以上证据说明正式方案必须先完成底层安全和事务改造，不能只实现 Sensor 的 ADD/DEL/SWITCH 分支。

## 协议演进边界

- 现有命令 0～9和请求字段 1～5、Ack 字段 1～10保持编号和含义。
- 追加 CLEAR、COMMIT_PENDING、ABORT_PENDING、QUERY_OPERATION、CANCEL_OPERATION。
- 追加 credential、operation options、operation_id、accepted/final、operation state、revision 和 rollback 信息。
- saved-network 追加 connected、current RSSI、link state、security、hidden 和 network-id，不包含密码。
- `wifi/status` 追加 SSID、link state、RSSI、失败原因、operation-id 和采样时间。
- 云端现有 SSID/密码字段保持兼容；为可靠支持隐藏网络和安全模式，应增加可选 security/hidden。

## 实施门禁

实施顺序：

1. 修复 WiFi 凭据日志、内存安全和失败删除配置。
2. 在 wifimg/API 实现 prepare/commit/abort/select/restore/clear 原子语义。
3. 扩展 protobuf 并同步生成代码。
4. 实现 Sensor 操作队列、CRUD、状态和操作查询。
5. 收口 App 诊断旁路，建立唯一写 owner。
6. 获取 Task/Iot 源码后接入手动多 WiFi。
7. 接入两阶段配网、解绑、恢复出厂、开机选网、断连恢复和弱网切换。
8. 完成故障注入、压力、HIL 和最终 image/OTA 重建。

在前五项完成前，不应开放云端多 WiFi 写操作。

## 验收证据要求

- 并发 ADD 后已提交加预留数量始终不超过 5。
- 同名密码错误保留旧凭据；SWITCH 失败保留目标并恢复原网络。
- QUERY 失败与真实空列表可区分，非当前网络不返回伪实时 RSSI。
- 隐藏网络、中文/特殊字符/32 字节 SSID、WEP/WPA/WPA2/WPA3 通过板级矩阵。
- 配网 100 次成功率不低于 98%；解绑 200 次和重置 100 次成功率不低于 99%。
- 优质环境连接到 IP_READY 不超过 5 秒；已保存网络切换不超过 3 秒。
- 对 SAVE_CONFIG 失败、DHCP 超时、进程重启、请求 Ack 丢失和操作中断执行故障注入。
- 日志、Ack、状态和 core 文本中不出现密码、PSK 或完整二维码内容。
- 最终发布核对 proto、api、wifi、sensor、app、task、iot、image 和 OTA 制品身份；后编译库不会自动进入旧镜像。

## 当前风险与待确认项

1. Task/Iot 匹配源码、构建和发布链路尚未进入当前 checkout。
2. 设备实际 supplicant 配置路径和持久化挂载需通过运行态确认。
3. 云端/二维码若不增加可选 security/hidden，隐藏网络兼容无法可靠验收。
4. 删除当前网络默认 `FAILOVER_THEN_REMOVE` 仍需产品 owner 确认。
5. 事务接口、WPA3/WEP 和性能目标尚缺 HIL 证据。

## 归档边界

- 本文是项目级 reviewing 架构候选，不提升到通用嵌入式标准。
- 本文不替代源码仓正式设计文档，也不证明实现、测试、镜像或 OTA 已完成。
- 若源文档、协议或代码发生变化，应更新 source hash、证据和 review 时间。
- 不写 Codex memory，不静默提升为 active，不代替 owner 签收。

## Review

- Owner：leiwenjun。
- Review after：2026-11-07。
- Gate result：`needs-fix`。结构化方案和代码证据已归档，仍缺 owner 策略确认、Task/Iot 源码、底层实现和板级验证。
- Memory candidate：no。
