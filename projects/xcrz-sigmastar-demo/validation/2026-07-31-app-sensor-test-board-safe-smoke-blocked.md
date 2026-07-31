---
id: app-sensor-test-board-safe-smoke-blocked-20260731
title: app_sensor_test staged safe 板测 transport 阻塞
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-board-safe-smoke-blocked.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz_sigmastar_demo
  source_sha256: 3b64dd22fac5f83f788722e6590e792d85be776b091c990842dd494c5d76f5ea
review_after: '2026-10-29'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- app_sensor_test
- validation
- board
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-board-safe-smoke-blocked.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-board-safe-smoke-blocked.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: app_sensor_test 第四轮 source-gate 全通过并冻结 ARM 候选；独立 staged safe 执行已获授权，但最新只读预检判定 ADB transport missing 且 circuit
  breaker 打开，设备端未创建目录、未推送、未执行、未覆盖 installed。恢复条件是 transport 明确为 device 后从 preflight 重启并核对 out/staged MD5。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- app_sensor_test staged safe 板测 transport 阻塞
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# app_sensor_test 完成性复审（JSONL v4）

复审日期：2026-07-31。

## 1. 结论

本轮没有沿用“22个迁移 case 即代码完成”的旧结论，而是以生产 `SensorModule`、
`sensor_ctrl.proto`、`sensor_info.proto`、transport topic 和板端/HIL 边界重新审计。

当前源码级结论：

- blocker：0；
- major：0 个已知未处置源码缺陷；
- catalog：44个 case，44个 executor；
- production command surface：25/25 有 manifest，名称/数值/disposition/case 引用有自动门禁；
- Host/ASan+UBSan/TSan/coverage/architecture/ARM build：通过；
- 外部未闭环：本次候选因最新 ADB transport 预检熔断而未 staged/installed，
  board JSONL 与仪器 HIL 仍缺证据。

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
| C6 | major | concurrency 仅列为 HIL 缺口，没有正式压力 case | 新增 concurrent req/rep，预生成 sequence/command ID，记录延迟和资源预算 |
| C7 | major | unsupported/reserved/delegated 被混为一般负向 ACK | `protocol.declared-behavior` 分别固化 DISPLAY/SOC_SHUTDOWN、AUDIO、OTA 错误语义 |
| C8 | major | DVR replay list 即使缺失 payload 也可能被默认空对象误判通过 | 强制 `has_dvr_replay_list()`，再校验 count/entries/truncated |
| C9 | minor | IR distance 把0硬判失败，没有生产契约依据 | 改为 timestamp + uint16 domain，精度/有效性进入 HIL 阈值 |
| C10 | governance | 原 coverage 名称可能让局部 Host 覆盖率看似全应用覆盖率 | 改名 `host-testable production line coverage`，板端 executor 单独由 ARM/board evidence 证明 |
| C11 | maintainability | 首版新增 device case 达657行，违反自定规模预算 | 拆成 device/service/telemetry/HIL/ingress 分域文件，最大 production cpp 严格不超过500行 |
| C12 | major | 25类命令不能代表 AudioPlay、velocity、WiFi 等稳定公共输入 | 新增5类 ingress manifest、zero-velocity 与WiFi malformed case，并对生产成员做架构门禁 |
| C13 | major | `machine+hil` case 的机器 ACK 通过会计入 pass 并返回0，外部工具可误判为能力全通过 | JSONL v4 硬切换为 machine/verified/external-pending 三类统计；HIL pending 强制 exit=2 |
| C14 | governance | 计划声称 CI 执行多类门禁，但仓库没有单一聚合入口，调用方可漏跑 | 新增 `tests/Makefile::source-gate`，串行执行 clean/check、machine/HIL tool、ASan/UBSan、TSan、coverage、ARM，并由架构测试保护 |
| C15 | major | 文档要求 HIL bundle，但没有可执行裁决器，pending case 可漏判、错绑 run 或伪造 overall verdict | 新增 `sensor-hil-bundle/v2` validator，绑定 JSONL SHA/run、逐 case verdict、阈值、owner、敏感字段、制品身份与最终健康 |
| C16 | major | 首版 concurrent case 的多线程复用同一 REQ socket，事务锁会串行化全部请求，不能证明真实 client 并发 | 每个 worker 创建 `allow_reuse=false` 的独立 client，并以 `max_in_flight>=2` 作为必过断言 |
| C17 | major | 首版 HIL validator 信任 summary，且 artifact/boot 未与 machine run 交叉绑定，可用伪造 summary 掩盖 machine fail 或错绑制品 | validator 独立复算 case lifecycle/evidence/counts，并强制 machine build identity、self size、boot_id 与外部身份读取证一致 |
| C18 | major | duration 可在首轮中途停止，已执行子集全通过时 runner 仍可能把未执行的 selected case 静默漏掉 | 新增 executed/unexecuted selection 会计；每个 selected case 未至少执行一次时强制 incomplete，HIL validator 从唯一 case ID 独立复算并拒绝自报计数 |
| C19 | major | HIL validator 未绑定 `run_start.selected_cases` ID 集合，理论上可缩小 summary selection 后裁决已执行子集 | 强制 run_start ID 集合、summary selected/executed 和 case result 唯一 ID 三方完全一致 |
| C20 | governance | build identity 只有父仓 commit；目录 dirty/untracked 时会产生“该 commit 可复现当前候选”的错误暗示 | 构建注入 `source_state=clean|dirty` 并进入 machine identity；validator 拒绝 unknown，ELF 强身份仍由外部读取证绑定 |
| C21 | major | stress 只记录 latency 不参与 verdict，且旧 p95 公式对2个样本把 `{10,20}` 算成10 | 改为 nearest-rank p95，新增 p95/单次最大延迟预算并进入 pass/fail；参数关系有运行时门禁 |
| C22 | major | CPU 只记录不判定且整数除法会低估小样本；operations 与 latency 样本可不一致 | 新增单操作 CPU 预算并向上取整；完成数与样本数不一致直接判为框架错误 |
| C23 | governance | 默认 GCC 9 TSan 链接环境缺 `libtsan_preinit.o`，但主机已有可用 Clang TSan；把它长期列为环境缺口会形成准入盲区 | 增加独立 `THREAD_CXX` 选择链，默认选中 `clang++-13`，并把 ThreadSanitizer 纳入 `source-gate` |
| C24 | major | 独立 concurrent client 启动时间没有统一门禁，调度偏差可能使 worker 串行消耗任务，弱化“同时施压”结论 | 增加有界、可取消 `ConcurrentStartGate`；全部 client ready 后统一释放，并记录 `ready_clients` |
| C25 | major | 原 machine parser 只接受 HIL pending，safe verified、真实 failed 和 incomplete 都没有独立机器裁决入口 | 新增通用 machine evidence validator，独立复算 lifecycle、selection、计数、verdict 与 exit，覆盖四类有效终态 |
| C26 | major | 已含 summary 的 `.partial` 可被 parser 当作 finalized evidence，且 durability marker 未校验 | validator 拒绝 `.partial`，并强制 `fsynced_pending_atomic_finalize` durability 契约 |
| C27 | major | HIL `final_state` 只有布尔值而无取证引用，时间戳正则还接受不存在的日期 | 合同硬切 v2，final health 必须有 evidence refs，UTC 时间戳语义解析，v1 明确拒绝 |
| C28 | blocker | fixture/logger/runtime 初始化失败会写没有 `case_start`、也不属于 selection 的伪 `case_result`，导致程序自产 final 无法通过通用 validator | 新增独立 `run_error` record；fixture 错误不污染 case lifecycle，validator 复算为 error/70 |
| C29 | major | final 与 live `.partial` sibling 同时存在时，validator 仍可能把 final 当作已完成证据 | machine/HIL parser 在读取 final 前检查 sibling，存在即拒绝 |
| C30 | maintainability | Host test asset 仍携带旧协议版本号，与 v4 合同形成遗留版本语义 | 硬切为稳定职责名，不提供 alias/兼容 target；架构门禁禁止旧命名回归 |
| C31 | governance | 新增 `test_*.cpp` 时可能漏加 target/check/Sanitizer，source-gate 仍可绿 | Make parse-time 比较 discovered/registered 集合；check/Sanitizer 从同一 `TARGETS` SSOT 自动执行 |
| C32 | major | start gate 后仍由全局 atomic 抢任务，调度优先 worker 可能吃完任务，不能证明所有独立 client 参与 | `ConcurrentWorkPartition` stride 静态分片，要求 `participating_clients=workers`，纯 Host 验证无重漏 |
| C33 | governance | header-only start gate/work partition 虽被执行，却未进入 production line coverage 分母 | 两个 `.h.gcov` 明确纳入聚合，防止 coverage 高估 |

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
| Machine/HIL evidence validators（25 tests） | PASS |
| ASan + UBSan（9 binaries） | PASS |
| ThreadSanitizer（2 runtime binaries，Clang 13） | PASS，已纳入 source-gate |
| Host 可测试生产逻辑 line coverage | PASS，81.79%（1653/2021），门槛75% |
| Proto/manifest/production disposition drift | PASS |
| catalog/executor parity、hard-cut、dependency、size | PASS |
| ARM `app_sensor_test_app_all`，`-Werror` | PASS |

本次 ARM 候选：

- path：`out/arm/app/prog_sensor_test`
- type：ARM EABI5、动态链接、含 debug_info、not stripped
- size：88,059,620 bytes
- build time：`2026-07-31 11:36:47 +0800`
- BuildID：`bda745b8170617574fa4f05e96f12a213ebce139`
- SHA-256：`486c4f9e108b4e73f317bfe3e64c1b1356a5c5fee53c13a8a56118a7332bb269`
- MD5：`1d47dd32b078ed8187b62829f8a19e5f`
- build source state：`dirty`（当前整个 `app_sensor_test/` 尚未纳入父仓 Git）

## 5. 设备只读 preflight

较早一次只读 preflight 曾按用户显式 serial 选择设备并确认 ADB 状态为 `device`。当时证据：

- boot_id：`2f9d00d7-dc56-4f20-b196-2fbaa3b81638`；
- preflight 时 uptime：约10小时47分钟；
- `prog_pcr02`、`prog_sensor_test` 当时均未运行；
- installed `prog_sensor_test`：80,494,700 bytes，MD5
  `1f882e03c96965e7b18285992bd32598`；
- installed 与本次候选身份不一致，不能用于本次44-case验收。

用户随后明确授权在独立 staged 路径 push 候选并执行 safe 测试。但本次候选完成后重新
preflight 时，主机虽有路由条目，ADB connect 仍返回 `No route to host`，
`adb devices -l` 中目标状态为 `missing`。runbook circuit breaker 已打开，因此没有创建
设备目录、没有 push、没有覆盖 installed binary、没有启动测试，也没有生成 board
JSONL。设备端点不进入源码、文档、Hub 或脚本默认值。

## 6. 剩余边界

1. staged safe smoke 已获授权；须待 ADB transport 恢复为 `device` 后从只读 preflight
   重新开始，并核对 out/staged 候选 MD5。
2. 光学、声学、QR码卡、DVR故障、电机运动、供电、reboot/wake、OTA 等必须依
   `HIL_RUNBOOK.md` 产生外部证据；machine ACK 不能替代物理判定。
3. 外层仓库仍把整个 `app_sensor_test/` 显示为 untracked。未纳入版本控制前，它还不是
   可审查、可追溯的团队长期资产；本次不自动 stage/commit。
