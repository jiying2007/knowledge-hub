---
id: pcr02-app-sensor-test-framework-20260730
title: PCR02 Sensor 分层全面测试框架基线
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-framework.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz_sigmastar_demo
  source_sha256: 0fecb84fe82f6b8ca3fc50bb96c5eb3de6d49689589c129d9c5c6e74dd84d173
review_after: '2026-08-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- sensor
- validation
- hil
- stress
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-framework.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-framework.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: app_sensor_test 已升级为分层测试框架：host unit、生产源码 white-box、模块契约、22个板端 black-box/fault/stress/soak/recovery case、JSONL
  v2 与 ARM 构建已落地；TSan和板端HIL仍待闭环。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Sensor 分层全面测试框架基线
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# app_sensor_test 开发、证据与恢复状态

## 1. 当前目标

- goal_statement：把 `app_sensor_test` 建成 Sensor 模块长期维护的分层测试框架，统一覆盖
  unit、component white-box、module contract、board black-box、fault-injection、stress、soak、
  recovery 和 HIL。
- completion_claim：框架代码、host 三层测试、22个板端 case、压力预算、JSONL schema v2、
  ARM 构建和文档已落地；板端 smoke/stress/soak/HIL 未执行，不能声明硬件全面通过。
- breaking change：全新 CLI 和 JSONL schema v2；不兼容旧 Deep Sleep 命令或 schema v1
  消费者。回退方式是恢复整个 `app_sensor_test/` 旧目录，不做混合兼容。
- 非目标：自动设备写入/部署、量产替代、算法语义擅自修改、无 HIL 证据的硬件通过声明。

## 2. 验收标准

| ID | 标准 | 证据 |
| --- | --- | --- |
| AC1 | taxonomy 支持 level/approach/type/target/tag | host unit + descriptor schema |
| AC2 | catalog 唯一性、tag、terminal 和 board approach 自检 | host unit + board pre-init gate |
| AC3 | repeat/duration/interval/fail-fast/failure budget 有界 | host unit |
| AC4 | 全部未授权 duration-run 不忙循环 | `risk_blocked` regression |
| AC5 | Sensor 真实生产算法进入 white-box binary | `test_sensor_whitebox` |
| AC6 | req/rep/telemetry 公共契约由 host 与 board 共用 | `sensor_test_contract.*` |
| AC7 | 25种 DeviceType 有公共安全 negative 覆盖 | board protocol matrix |
| AC8 | 关键 lifecycle/identity/IMU/ToF/media 有 black-box case | board catalog |
| AC9 | 控制、malformed、IMU toggle 有压力与资源预算 | stress catalog |
| AC10 | soak 强制显式 duration，输出 stop reason | host unit + board catalog |
| AC11 | ASan/UBSan host 三组通过，ARM 定向构建通过 | 验证命令 |
| AC12 | 当前覆盖、缺口、HIL 阶梯和制品边界有文档 | README/design/matrix |

## 3. Checkpoints

| 阶段 | Owner | 状态 | 完成判据 | 证据 |
| --- | --- | --- | --- | --- |
| CP1 边界审计 | Codex | complete | Sensor public、pure logic、Proto、ZMQ、SHM、build 已定位 | source scan |
| CP2 Framework core | Codex | complete | taxonomy/filter/budget/catalog/schema v2 绿灯 | core test |
| CP3 Host layers | Codex | complete | unit/contract/production-whitebox 绿灯 | 三个 host binary |
| CP4 Board catalog | Codex | implemented | 22 case + stress/soak + cleanup 编译通过 | ARM build |
| CP5 Review/docs | Codex | complete | blocker/major 修复，矩阵与恢复状态同步 | review ledger |
| CP6 Board smoke | Device owner | pending | single smoke/functional 通过 | JSONL+dmesg |
| CP7 Stress/soak/HIL | Device owner | pending | 分级压力、资源、媒体、power 证据 | HIL report |

## 4. TDD 与验证证据

| 命令/场景 | Exit | 结果 | 层 |
| --- | ---: | --- | --- |
| 扩展 taxonomy/budget 后首次 `make ... check` | 2 | 预期红灯：缺 TestLevel/filter/duration API | TDD red |
| production white-box 首次执行 | 2 | DataFilter 小变化预期与真实零方差 outlier 语义不一致 | Contract discovery |
| 首次扩展 ARM build | 2 | `error_code` uint32→int32 narrowing 被 `-Werror` 捕获 | Cross red |
| review regression：未授权 duration | 2 | 3个断言证明会重复 skip/忙循环 | Review red |
| `rtk make -C app_sensor_test/tests check` | 0 | core/contract/white-box 全部通过 | Host |
| `rtk make -C app_sensor_test/tests sanitizer` | 0 | 三组 ASan/UBSan 通过 | Host sanitizer |
| `rtk make -C app_sensor_test/tests thread-sanitizer` | 2 | 本机缺 `libtsan_preinit.o`，TSan 未执行 | Tool gap |
| `rtk make app_sensor_test_app_all` | 0 | ARM32 EABI5 hard-float ELF 构建通过 | Cross |
| `file/readelf out/arm/app/prog_sensor_test` | 0 | BuildID `b566063bad8947fb26ce7fff8229e78ae115de84` | Artifact |
| `nm -C ... | rg Task/Bridge/IoT/Navigation` | 1 | 零命中，未链接禁用模块符号 | Artifact |
| trailing whitespace 定向 `rg` | 1 | 零命中 | Static |
| `rtk git diff --check` | 0 | 已跟踪 diff 无空白错误；app 仍为 untracked | Static boundary |
| 板端 smoke/stress/soak/power | 未执行 | 缺当前设备端点和设备操作授权 | HIL gap |

TSan target保留为长期门禁入口，但当前环境不能把链接失败写成 race-free 证据。并发
`MediaFlowGate` 已有4线程×1000次 white-box 回归，仍不等价于 ThreadSanitizer。

## 5. Review 闭环

| ID | Severity | 发现 | 处理 | 状态 |
| --- | --- | --- | --- | --- |
| R1 | major | 非法选择会提前 truncate output | 所有 preflight 移到 open 前 | fixed |
| R2 | major | terminal 掉电可能无起始证据 | fixture 前同步写 run_start | fixed |
| R3 | major | fixture/ZMQ exception 可能越界 | 统一收敛为 fixture error | fixed |
| R4 | major | enable/open 失败 cleanup 不完整 | 各媒体/telemetry 失败分支补 cleanup | fixed |
| R5 | major | suite/case 语义含混 | CLI 强制互斥 | fixed |
| R6 | major | duration + 全部风险拒绝会重复 skip 忙循环 | 风险在 runner 前置分类，skip一次后 `risk_blocked` | fixed |
| R7 | major | stress IMU disable 失败后无第二次清理 | 增加独立 cleanup retry | fixed |
| R8 | major | 宽泛 `.gitignore` 会忽略新增 test source | 改为逐个 binary 精确忽略 | fixed |
| R9 | major | suite/type 相同会生成重复 tag | catalog tag 统一去重并加启动自检 | fixed |
| R10 | minor | TSan 工具链不完整 | 保留 target，记录环境缺口 | accepted gap |

复审结论：代码级 blocker=0、major=0；板端和算法 owner 结论仍是开放证据/决策，不由 AI
review 代替。

## 6. 当前开放项

1. Device owner 执行单次 smoke、5轮 functional、media、stress、短 soak。
2. Sensor algorithm owner 判断 DataFilter 零方差窗口持续抑制小变化是否符合预期。
3. CI/toolchain owner 补齐可运行 TSan 或提供等价 race detector。
4. 为 Laser/IR/Display/Audio quality/Motor movement/DVR/OTA 建立夹具和专用测试。
5. app 如需进入 image/OTA，必须重生制品并逐级核对身份。

## 7. 风险台账

| 风险 | 影响 | 控制 |
| --- | --- | --- |
| 与正式应用并行 | UART/HDI/IPC 冲突、假失败或崩溃 | 停 daemon/watchdog，独占 Sensor |
| stress operation batch 过大 | duration 只能在 case 边界停止 | 分级放大，限制 operations，先短测 |
| cleanup 失败继续压力 | 状态泄漏叠加 | fail-fast/max-failures=1，立即停止 |
| end RSS 看不到瞬时峰值 | 漏掉峰值内存 | HIL 同步采样 RSS/CPU/OOM；后续加 peak metric |
| host white-box 被误当硬件证据 | 错误放行 | matrix 明确 host/board/HIL 边界 |
| Proto/Channel 演进 | catalog/断言陈旧 | 14天 staleness + 变更触发重扫 |
| app 目录仍 untracked | 资产未进入版本控制 | 由 owner 审查后整体纳管，不自动 commit |

## 8. Anti-stall 与恢复

- retry_budget：同类 host/cross 失败最多2轮；仍无根因切换系统化调试。
- staleness_threshold：14天或 Sensor Proto/Channel/handler 变更。
- heartbeat：每完成 checkpoint 更新本文件证据与 open items。
- stop_condition：pass/replan/split/blocked/abort。
- HIL terminal stop：core、fatal dmesg、cleanup failure、资源超预算、身份漂移、设备失联。

恢复时最多三步：

1. 重跑 host check、sanitizer、ARM build，核对 BuildID。
2. 获得设备端点和显式授权后，只执行单次 smoke。
3. smoke 通过后按 matrix 放大，并把原始 JSONL/dmesg/制品身份写入 HIL evidence candidate。
