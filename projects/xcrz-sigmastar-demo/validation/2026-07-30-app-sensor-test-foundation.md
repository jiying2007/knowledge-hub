---
id: pcr02-app-sensor-test-foundation-20260730
title: PCR02 Sensor 全面测试资产基线
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-foundation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project
  from: xcrz_sigmastar_demo
  source_sha256: 8cc49f2f8026219d6cf43863cc5b5bf9d4d4731b0dc9161b47b0182020a73220
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
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-foundation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-30-app-sensor-test-foundation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-30'
updated_at: '2026-07-30'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex
ai_generated_at: '2026-07-30'
manual_validation_pending: true
summary_zh: app_sensor_test 已完成全新 CLI、18 个测试用例、风险门禁、JSONL 证据链、主机单测与 ARM 交叉构建；板端 HIL 尚待授权设备执行。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Sensor 全面测试资产基线
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# app_sensor_test 开发与恢复状态

## 1. 需求基线

- 需求类型：现有单用途程序的架构增强，按新功能/共享契约风险处理。
- 优先级：P1。Sensor 是设备核心模块，测试入口缺失会直接扩大回归与现场验证风险。
- goal_statement：建立可长期维护、默认安全、覆盖 Sensor 正式外部契约的全面测试程序。
- 非目标：产测替代、自动部署、自动设备写操作、无 HIL 证据的硬件完成声明。

## 2. 验收标准

| ID | 标准 | 验证 |
| --- | --- | --- |
| AC1 | `list`/help 不初始化 Sensor | host CLI test + 板端观察 |
| AC2 | runner 支持 suite/case/repeat/fail-fast/terminal | host unit |
| AC3 | risk 未授权时 executor 不执行，skip 非零退出 | host unit |
| AC4 | JSONL 对引号、换行和 metrics 稳定编码 | host unit |
| AC5 | 25 种 DeviceType 至少有安全协议覆盖 | `protocol.missing-payload-matrix` |
| AC6 | 身份、静态信息、IMU、ToF 有正向链路 | board smoke/functional |
| AC7 | Camera/Mic/Video 有风险门禁和强制 cleanup | board media |
| AC8 | Deep Sleep 是 destructive/terminal 独占用例 | host selection + board power HIL |
| AC9 | ARM app 可在现有 SDK 定向构建 | `rtk make app_sensor_test_app_all` |
| AC10 | 文档明确当前覆盖、缺口和制品链边界 | README/design/matrix review |

## 3. Checkpoints

| Checkpoint | Owner | 状态 | 完成判据 | 证据 |
| --- | --- | --- | --- | --- |
| CP1 现状审计 | Codex | complete | public API、Proto、topic、SHM、构建入口已核对 | 源码路径与本设计 |
| CP2 Host contract | Codex | complete | 先红灯、后 core/CLI 单测绿灯 | host test 输出 |
| CP3 Board implementation | Codex | implemented | fixture + 18-case catalog + result writer | `app_sensor_test/*.cpp` |
| CP4 Cross build | Codex | pass | ARM 编译链接成功 | 构建命令输出 |
| CP5 Board smoke | Device owner | pending | AC1/AC5/AC6 板端通过 | JSONL、串口、dmesg |
| CP6 Media/power HIL | Device owner | pending | AC7/AC8 逐级验证 | HIL 报告、制品身份 |

## 4. 验证证据索引

| 命令/路径 | 退出码 | 结果 | 层级 |
| --- | --- | --- | --- |
| `rtk make -C app_sensor_test/tests check`（首次） | `2` | 预期红灯：runner/CLI 源文件尚不存在 | Test/TDD |
| `rtk make -C app_sensor_test/tests check`（实现后） | `0` | host contract 全部通过 | Test |
| ASan/UBSan host build + `/tmp/test_sensor_test_core_asan` | `0` | 无 sanitizer 报告 | Test |
| `rtk make app_sensor_test_app_all` | `0` | ARM32 EABI5 hard-float ELF 构建成功 | Build |
| `rtk file out/arm/app/prog_sensor_test` | `0` | BuildID `8967c9edbf6c49de70f9be4257d7a2dd03c35558` | Artifact |
| `rtk git diff --check` | `0` | 仓库已跟踪 diff 无空白错误 | Static |
| trailing whitespace 定向扫描 | `1` | `rg` 零命中；新增源码/Markdown 无行尾空白 | Static |
| `clang-format --dry-run --Werror ...` | `1` | 工具不支持根配置 `SpaceBeforeParens: Custom`，未改共享配置 | Tool gap |
| 板端 smoke/functional/media/power | 未执行 | 缺少本轮明确设备端点、部署授权和 HIL 环境 | HIL gap |

负结果说明：host 测试扩展期间还捕获过一次局部测试变量重名编译失败，已最小修复并由
host test 与 sanitizer 复验。`clang-format` 失败属于仓库配置与本机工具版本不兼容，不作为
源码通过证据，也不通过修改根配置规避。

## 5. Review 闭环

| ID | Severity | 发现 | 处理 | 状态 |
| --- | --- | --- | --- | --- |
| R1 | major | 非法 case/参数会在校验前 truncate `--output` | 把 selection/参数 preflight 移到打开文件之前 | fixed |
| R2 | major | terminal 成功掉电时结果文件可能没有任何记录 | fixture 前同步写脱敏 `run_start` | fixed |
| R3 | major | fixture/ZMQ 构造异常可能越过统一结果 | 捕获标准/非标准异常并输出 `fixture.sensor` error | fixed |
| R4 | major | enable/open ACK 失败时可能遗漏 best-effort cleanup | IMU/ToF/Camera/Mic/Video 失败分支补 cleanup | fixed |
| R5 | major | suite 与 case 同时出现时语义含混 | CLI 明确互斥并补 host test | fixed |
| R6 | minor | 根 clang-format 配置与本机版本不兼容 | 记录工具缺口，不修改 shared root config | accepted gap |

复审结论：代码级 blocker=0、major=0；板端 HIL 未执行是交付证据缺口，不是用交叉构建替代。

## 6. Goal closure

- completion_claim：代码与 host/cross-build 资产已实现；板端功能、媒体和 power 行为尚未完成 HIL，
  当前不能声明硬件全面通过。
- required_evidence：host 单测、ARM 定向构建、`git diff --check`、板端 JSONL、串口/dmesg、
  power 外部证据。
- claimant：实现者。
- verifier：执行完成前门禁的主 Agent；板端部分由设备/HIL owner 核验原始证据。
- open_items：CP5、CP6，以及 `TEST_MATRIX.md` 标出的 actuator/DVR/OTA/标定缺口。

## 7. Anti-stall

- retry_budget：同一 host/cross-build 失败最多 2 次；两次仍无根因转系统化调试并更新风险。
- staleness_threshold：本文件超过 14 天未更新且源码继续变化时，恢复前重新扫描 Proto、
  ChannelList 和 Sensor handler。
- heartbeat：每完成一个 checkpoint 更新状态、验证命令和 open items。
- stop_condition：`pass`、`replan`、`split`、`blocked` 或 `abort`。
- terminal stop：core、fatal dmesg、cleanup 失败、设备身份漂移、ADB/serial 失联时停止放大。

## 8. 风险台账

| 风险 | 影响 | 控制 |
| --- | --- | --- |
| 与 `prog_pcr02` 并行运行 | UART/HDI/IPC 冲突，结果失真或崩溃 | 运行前停 daemon/watchdog，独占 fixture |
| safe 被误解为“无任何硬件动作” | Sensor init 本身会初始化硬件 | 文档将 safe 定义为无有意破坏/长期状态修改 |
| cleanup 主路径失败 | 后续用例建立在未知状态上 | cleanup 失败升级为 fail，推荐 fail-fast |
| terminal 成功无 summary | 自动系统误判缺失结果 | power 依赖外部 HIL，文档明确无 summary 是预期之一 |
| 后编译 app 未进入 image | 板端跑到旧二进制 | 核对 staged/installed/image/OTA 的 MD5/BuildID |
| Proto/Channel 演进 | matrix 漏测或元数据断言过期 | 14 天 staleness + 变更时更新 catalog/matrix |
| 大量既有 dirty/untracked | 误覆盖用户资产 | 仅修改 `app_sensor_test/`，不清理外部文件 |

## 9. 恢复入口

下一会话最多执行以下三步：

1. 运行 host test、ARM 定向构建和静态门禁，核对当前源码证据。
2. 在确认设备端点和显式写权限后，执行单次 smoke，再做 5 次 functional。
3. 生成 HIL evidence/candidate；media 与 power 必须继续分开、逐项授权。

恢复时禁止自动 deploy 或终止设备进程；必须先核对安装制品身份、自动 standby/watchdog 和
当前运行状态。
