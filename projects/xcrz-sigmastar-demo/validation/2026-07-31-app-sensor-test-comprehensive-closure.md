---
id: pcr02-app-sensor-test-comprehensive-closure-20260731
title: PCR02 Sensor 全面测试框架落地验证记录
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-comprehensive-closure.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz_sigmastar_demo
  source_sha256: 4d696a927da8ad8b4e57ec7fbaa31a3f3963dca6d42902de45a5b8673373c4ea
review_after: '2026-08-14'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- sensor
- validation
- hard-cut
- hil
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-comprehensive-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-comprehensive-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: app_sensor_test 已硬切换为44项全面测试框架，25类命令与5类稳定入口具备自动闭包门禁；Host、ASan/UBSan、81.57%覆盖率和ARM构建通过，设备staged与HIL仍待授权和外部证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Sensor 全面测试框架落地验证记录
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# app_sensor_test v3 完成性复审

复审日期：2026-07-31。

## 1. 结论

本轮没有沿用“22个迁移 case 即代码完成”的旧结论，而是以生产 `SensorModule`、
`sensor_ctrl.proto`、`sensor_info.proto`、transport topic 和板端/HIL 边界重新审计。

当前源码级结论：

- blocker：0；
- major：0 个已知未处置源码缺陷；
- catalog：44个 case，44个 executor；
- production command surface：25/25 有 manifest，名称/数值/disposition/case 引用有自动门禁；
- Host/ASan+UBSan/coverage/architecture/ARM build：通过；
- 外部未闭环：本次候选尚未 staged/installed，board JSONL、TSan 与仪器 HIL 仍缺证据。

因此可以声明“全面测试框架和可执行 case 已在源码侧落地”，不能声明“Sensor 全硬件能力
已通过”。

## 2. 本轮完成性审计发现

| ID | 级别 | 发现 | 处置与证据 |
| --- | --- | --- | --- |
| C1 | major | 旧结论只证明22个迁移 case，生产25类 DeviceCommand 无完整映射 | 新增 `DeviceCommandCapability`，25/25登记 supported/reserved/delegated/unsupported 与 case |
| C2 | major | Proto 增删、枚举值变化或生产 switch disposition 漂移可静默发生 | architecture test 解析 Proto，并比较 manifest 和 `SensorEntry` 分支 |
| C3 | major | catalog 与 executor 只在板端启动时校验，Host 无法提前阻止漏注册 | architecture test 比较44个 catalog/executor ID 集合完全相等 |
| C4 | major | IR、QR、Display、Audio、DVR、TCPKA、camera FPS、motor ESTOP 只有“未来项” | 新增可执行 control/cleanup/list/lifecycle case，required restore 参数阻止猜测健康值 |
| C5 | major | IR matrix、IR distance、motor telemetry 未进入测试 runtime | 扩展中立 `SensorTopic` 与 adapter，增加 protobuf shape/numeric contract case |
| C6 | major | concurrency 仅列为 HIL 缺口，没有正式压力 case | 新增多 client 并发 req/rep，预生成 sequence/command ID，记录延迟和资源预算 |
| C7 | major | unsupported/reserved/delegated 被混为一般负向 ACK | `protocol.declared-behavior` 分别固化 DISPLAY/SOC_SHUTDOWN、AUDIO、OTA 错误语义 |
| C8 | major | DVR replay list 即使缺失 payload 也可能被默认空对象误判通过 | 强制 `has_dvr_replay_list()`，再校验 count/entries/truncated |
| C9 | minor | IR distance 把0硬判失败，没有生产契约依据 | 改为 timestamp + uint16 domain，精度/有效性进入 HIL 阈值 |
| C10 | governance | 原 coverage 名称可能让局部 Host 覆盖率看似全应用覆盖率 | 改名 `host-testable production line coverage`，板端 executor 单独由 ARM/board evidence 证明 |
| C11 | maintainability | 首版新增 device case 达657行，违反自定规模预算 | 拆成 device/service/telemetry/HIL/ingress 分域文件，最大 production cpp 为473行 |
| C12 | major | 25类命令不能代表 AudioPlay、velocity、WiFi 等稳定公共输入 | 新增5类 ingress manifest、zero-velocity 与WiFi malformed case，并对生产成员做架构门禁 |

## 3. 既有框架问题闭环

| ID | 原级别 | 问题 | 当前闭环 |
| --- | --- | --- | --- |
| R1 | major | operation 可越过 case deadline | req/rep、feature、Deep Sleep 使用 remaining budget |
| R2 | major | deadline 耗尽后 cleanup 得到0ms | `cleanup_timeout_ms` 与执行预算独立，默认5s且共享有界预算 |
| R3 | major | Deep Sleep callback 生命周期可能悬空 | `shared_ptr` coordinator + RAII callback session |
| R4 | major | 未授权 case 参数误判未知 | 参数 schema 与风险授权分阶段校验 |
| R5 | major | duration 与 case timeout 混淆 | invocation 标记 deadline 来源，case timeout 强制 fail |
| R6 | major | executor/evidence/cleanup 错误可能丢失退出语义 | exception、sink、finalize、cleanup 均影响 result/exit |
| R7 | minor | 资源探针缺字段仍产生零值 | RSS/HWM/thread 必须完整解析 |
| R8 | maintainability | adapter 混合 ACK/callback 职责 | 拆出 `device_control_ack`、`DeepSleepCoordinator` |

## 4. 当前验证证据

| Gate | 结果 |
| --- | --- |
| Host check（9 binaries） | PASS |
| ASan + UBSan（9 binaries） | PASS |
| Host 可测试生产逻辑 line coverage | PASS，81.57%（1536/1883），门槛75% |
| Proto/manifest/production disposition drift | PASS |
| catalog/executor parity、hard-cut、dependency、size | PASS |
| ARM `app_sensor_test_app_all`，`-Werror` | PASS |
| ThreadSanitizer | 环境缺口：GNU linker 缺少 `libtsan_preinit.o` |

本次 ARM 候选：

- path：`out/arm/app/prog_sensor_test`
- type：ARM EABI5、动态链接、含 debug_info、not stripped
- size：87,825,812 bytes
- build time：`2026-07-31 08:42:52 +0800`
- BuildID：`7f079488ae3328ac1dcc409ab2420637bb4e1115`
- SHA-256：`fb35ce5a6aef7d6b7d07ed57035c6adc1be6c1a9aaa47556886b6ae608519a25`
- MD5：`4a5eb115c7d21af5c8278cb685a0a0a5`

## 5. 设备只读 preflight

用户提供的设备已按显式 serial 选择并确认 ADB 状态为 `device`。只读证据：

- boot_id：`2f9d00d7-dc56-4f20-b196-2fbaa3b81638`；
- preflight 时 uptime：约10小时47分钟；
- `prog_pcr02`、`prog_sensor_test` 当时均未运行；
- installed `prog_sensor_test`：80,494,700 bytes，MD5
  `1f882e03c96965e7b18285992bd32598`；
- installed 与本次候选身份不一致，不能用于本次44-case验收。

设备端点不进入源码、文档、Hub 或脚本默认值。当前未获 staged push/运行授权，因此没有
覆盖 installed binary、没有启动测试，也没有生成 board JSONL。

## 6. 剩余边界

1. staged/installed/board smoke 必须先获得设备写与执行授权，并重新核对候选 MD5。
2. 光学、声学、QR码卡、DVR故障、电机运动、供电、reboot/wake、OTA 等必须依
   `HIL_RUNBOOK.md` 产生外部证据；machine ACK 不能替代物理判定。
3. TSan 缺库是当前 Host 工具链环境限制；ASan/UBSan 和已有并发测试不等价于 TSan。
4. 外层仓库仍把整个 `app_sensor_test/` 显示为 untracked。未纳入版本控制前，它还不是
   可审查、可追溯的团队长期资产；本次不自动 stage/commit。
