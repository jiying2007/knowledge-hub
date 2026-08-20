---
related: []
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
incident_id: null
severity: null
affected_version: null
id: pcr02-tcpka-payload-server-alignment-20260805
title: PCR02 TCPKA payload 与服务端路由校验优化
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-pcr02-tcpka-payload-server-alignment.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 当前 Codex 会话、设备端和服务端源码检查及静态协议向量验证
  source_sha256: 2ac1a69b133b7de95805111872a589982dcbc531b60f61c3e0f7e6c1ac0065fc
review_after: '2026-11-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- tcpka
- low-power
- wifi
- server
- protocol
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-pcr02-tcpka-payload-server-alignment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-05-pcr02-tcpka-payload-server-alignment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-05'
updated_at: '2026-08-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-05'
manual_validation_pending: true
summary_zh: 记录 PCR02 TCPKA 的 pcr02 八字节名称、48 字节报文上限、设备端 ACK 捕获门禁、服务端结构校验与路由续期优化；源码静态验证通过，服务端部署和板级 HIL 待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 TCPKA payload 与服务端路由校验优化

## 现象

PCR02 进入休眠后由 WiFi TCP keepalive 触发 MCU 唤醒。现场存在两类相互关联但尚未证明同源的现象：

- 快速进入休眠并立即出现 WiFi 唤醒电平时，5 秒入口保护可能忽略该次唤醒；若中断保持高电平，后续缺少新边沿。
- 一次脱敏抓包中，短 TCPKA payload 虽收到服务端 TCP ACK，WiFi offload 仍以约 1 秒间隔重传相同序列范围，随后出现非预期唤醒。

本记录只归档协议、源码边界和静态证据，不保存设备地址、服务端地址、真实设备 ID、raw 抓包、完整串口日志或二进制。

## 影响范围

- 项目：`xcrz-sigmastar-demo`
- 设备端：Sensor TCPKA 配置、设备身份生成、休眠前 TCP session capture
- 服务端：Netty 帧解码、设备连接映射、Redis 路由 TTL、演示客户端
- 不涉及：MCU 5 秒入口保护策略本身、服务端部署、镜像/OTA 生成、真实设备 HIL

## 环境

- 平台：PCR02 / SigmaStar SSC305
- WiFi：Broadcom DHD 私有命令 `tcpka_conn_add`、`tcpka_conn_dump`、`tcpka_conn_enable`
- TCPKA 周期：30 秒
- 来源：当前 Codex 会话、设备端与服务端源码检查、驱动结构检查、脱敏抓包摘要和静态协议向量
- 源码状态：设备端与服务端修改均未在本记录中声明已提交、已编译或已部署

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 2026-08-05 | 检查短心跳抓包 | 服务端 ACK 存在，但 offload 对短 payload 出现重复发送；不能仅归因于服务端未 ACK |
| 2026-08-05 | 检查 DHD 驱动结构 | `len` 与 `ka_payload_len` 为独立字段，源码不能证明注册包与心跳包必须等长 |
| 2026-08-05 | 收敛设备端协议 | 名称固定为 8 字节 `pcr02`，头部 14 字节，总 payload 最大 48 字节，设备 ID 最大 34 字节 |
| 2026-08-05 | 优化服务端 | 增加 48 字节帧上限、严格名称校验、连接身份不可变、心跳续期和跨实例路由接管处理 |
| 2026-08-05 | 调整职责边界 | 服务端传输层只校验设备 ID 长度和安全字符，不解析设备身份内部业务格式 |

## 证据

### 源码边界

- `modules/sensor/hardware/tcpka_protocol.h`
  - 集中定义名称 8 字节、头部 14 字节、总 payload 48 字节和设备 ID 34 字节上限。
- `modules/sensor/hardware/tcpka.cpp`
  - 注册 socket 首包与 WiFi TCPKA 使用相同完整 payload。
  - 在停止 `tcpka_conn_dump` 前通过 `TCP_INFO.tcpi_unacked` 等待注册数据获得 TCP ACK。
  - 保持 30 秒 TCPKA 周期。
- `modules/sensor/main/device_identity_service.cpp`
  - 与 TCPKA 层共享设备 ID 最大长度，避免身份生成层与传输层边界漂移。
- `tcpka/tcpServer/XcrzTcpPayload.java`
  - 最大帧限制为 48 字节，名称严格匹配 `pcr02\0\0\0`。
  - device ID 只允许 1–34 个字母、数字、连字符或下划线。
- `tcpka/tcpServer/XcrzTcpServerHandler.java`
  - 同一连接注册后的 device ID 不可改变。
  - 相同 device ID 的后续完整 payload 作为心跳处理并刷新路由。
  - 非法帧关闭连接，异常日志不输出完整原始 payload。
- `tcpka/tcpServer/XcrzTcpServer.java`
  - 相同 device ID 的新连接替换旧连接。
  - Redis TTL 可由心跳和定时任务续期；跨实例 owner 变化时旧连接停止续期。

### 验证索引

| Command / Check | Exit Code | 结果摘要 | 证据边界 |
| --- | ---: | --- | --- |
| `rtk git diff --check`（Sensor 子仓） | 0 | 差异无空白错误 | 不包含编译和运行时行为 |
| 设备端源码静态契约检查 | 0 | 30 秒周期、共享上限和 ACK gate 顺序符合预期 | 基于当前未提交源码 |
| 服务端源码静态契约检查 | 0 | 帧上限、严格名称、身份不可变和路由续期均存在 | 服务端目录缺少独立构建入口 |
| 协议向量检查 | 0 | 完整 ID 和简写 ID 两个合法向量通过；错误名称、空 ID、超长 ID和非法字符四个向量被拒绝 | 等价协议模型，不替代 Java 集成测试 |
| 交叉工具链头文件检查 | 0 | 支持 `TCP_INFO` 和 `tcpi_unacked` | 未执行目标模块编译 |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | 会话完成门禁通过 | 不替代服务端上线与板级 HIL |

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 服务端没有发送 TCP ACK | 检查脱敏抓包摘要 | 服务端 ACK 已出现 | 已排除 |
| 服务端主动下发应用数据导致唤醒 | 检查对应服务端到设备方向 | 未观察到应用 payload | 当前样本中排除 |
| 短心跳 payload 必然不被驱动支持 | 检查 DHD `tcpka_conn_t` | 驱动分别保存最后包长度与 keepalive payload 长度 | 未证实 |
| 注册 ACK 尚未进入固件捕获状态 | 在设备端增加 ACK gate 后再结束 session capture | 源码已实现，尚无板级结果 | 待验证 |
| 使用同一完整 payload 可消除重复发送 | 设备端与服务端已统一处理完整 payload | 尚未上线抓包验证 | 待验证 |

## 根因

未确认。

现有证据能够证明短 payload 重传不是简单的“服务端未 ACK”，但不能从驱动源码推出“注册包和 TCPKA payload 必须完全相同”。当前采用相同完整 payload，是面向下一轮板级验证的实现选择，不是已确认根因。

## 修复或规避

### 设备端

- 建立单一协议常量来源，约束 8/14/48/34 字节边界。
- 注册与周期 TCPKA 使用相同完整 payload，服务端把重复完整 payload 视为心跳。
- 注册发送后等待 TCP ACK，再结束 WiFi session capture。
- 设备身份生成层与 TCPKA 传输层共享最大长度。

### 服务端

- 解码器最大帧从宽泛上限收紧到 48 字节，并严格检查长度字段和 8 字节名称。
- device ID 的传输校验保持通用：只检查 1–34 字节和安全字符；身份组成规则不下沉到 payload 解码器。
- 同连接禁止改变身份；重复心跳只续期，不重复注册。
- 同设备新连接替换旧连接，并防止旧连接续期其他实例已接管的 Redis 路由。
- 异常日志不再记录完整原始报文。

### 兼容与回退

- 设备端与服务端必须使用匹配的 8 字节名称和 14 字节头部布局。
- 如上线验证失败，设备端和服务端必须成对回退，不能只回退其中一侧。
- 当前设备端存在调试地址覆盖，正式发布前必须恢复使用上层配置；归档不记录现场端点。

## 验证

当前完成的是源码静态验证，结论为 `source-static-pass / runtime-pending`。

上线验证至少满足：

1. 服务端真实工程完成编译和部署，确认 Netty 解码器、Redis 和 Spring scheduling 配置实际生效。
2. 设备端使用匹配源码重新构建和部署，核对最终制品身份。
3. 抓包确认首次注册与每次 30 秒 TCPKA 均为相同完整 payload。
4. 每次服务端 ACK 后不再出现约 1 秒间隔的同序列 payload 重传。
5. 服务端未下发应用数据时，不发生 TCPKA 引起的非预期唤醒。
6. 重复快速休眠/唤醒并覆盖 5 秒入口保护窗口，确认 WiFi 中断不会因持续高电平丢失后续唤醒。
7. 采集 `tcpka_conn_sess_info` 或等价诊断，核对固件 `seq/ack` 与抓包一致。

### 离线待验证（可选）

```yaml
manual_validation_pending: true
manual_validation_reason: 服务端真实工程编译部署与设备板级 TCPKA 抓包尚未执行
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
owner: leiwenjun
review_after: 2026-11-05
```

## 后续动作

1. 服务端上线后执行上述抓包与路由验证，另建 validation 条目，不把 raw 抓包写入正文。
2. 完成设备端快速休眠/唤醒循环和 WiFi 中断电平 HIL。
3. 若同 payload 后仍出现重传，优先对比 WiFi 固件捕获的 `seq/ack`、TCP 时间戳和服务端 ACK，不重复假设服务端未 ACK。
4. HIL 通过并经 owner 复核前，本条目保持 `reviewing`，不提升为 active 事实或团队通用规范。

## 归档治理

- Sanitization：已移除现场 IP、真实设备 ID、raw log、raw 抓包、二进制和本机绝对路径。
- Provenance：当前 Codex 会话、项目源码、平台驱动源码和静态协议向量。
- Memory candidate：no。
- Gate result：reviewing / manual validation pending。
