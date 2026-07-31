---
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
target_version: null
test_environment: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: pcr02-motor-uart-timestamp-sync-implementation-validation-20260727
title: PCR02 电机 UART 时间戳同步实施与离线验证
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 2026-07-27 MCU/SoC working-tree implementation and offline validation
  source_sha256: 21383d3c228cbf679e64e8ec1ed7ec35de74b1486fd8cf8889b7599425569f30
review_after: '2026-10-27'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- motor
- uart
- timestamp
- time-sync
- implementation
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-27-pcr02-motor-uart-timestamp-sync-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-27'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-27'
manual_validation_pending: true
summary_zh: 记录 0x1A 时间同步、固定 40 字节 0x16、MCU RX-end 采集时间映射到 MotorData.header.timestamp、事件驱动速度持久状态、app_uart/hdi_uart 实时链路与 BOOTTIME
  公共 API 的工作区实施；MCU/SoC 离线构建通过，板级时延、循环、soak 与组合 image/OTA 仍待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 电机 UART 时间戳同步实施与离线验证
---

# PCR02 电机 UART 时间戳同步实施与离线验证

## 验证目标

验证已人工确认的设计归档 `projects/xcrz-sigmastar-demo/archive/reports/2026-07-26-pcr02-motor-uart-timestamp-sync-plan.md` 是否已在 MCU 与 SoC 工作区形成可编译实现，并记录实施阶段按 owner 最新意见将 60 字节多时间字段草案收敛为 40 字节单采集时间戳的最终差异，同时保留 OTA 构建边界。

本报告只证明工作区源码契约、定向编译、MCU 内存预算和离线 package 门禁；不证明板级实时性能、同步精度、升级窗口、组合 image/OTA 身份或发布可用性。

## 验证对象

- SoC baseline：`workspace://xcrz-sigmastar-demo` HEAD `1c699666dcc3b97f2778ed289c6085e65f348a19` 加当前未提交工作区 diff。
- MCU baseline：`workspace://gd32l235` HEAD `6fd343dbab7413e35d4d3d621dffd64824802be6` 加当前未提交工作区 diff。
- SoC 主要落点：`hdi_uart`、`app_uart`、`app_uart_packet`、Sensor、Proto、Bridge 和公共头文件镜像。
- MCU 主要落点：`protocol`、`motor_protocol`、主循环和协议契约测试。

## 已实现契约

- 新增 `0x1A` PROBE/COMMIT；SoC 以 `CLOCK_BOOTTIME` 为统一时钟，启动 8 次探测、稳态每 5 秒 3 次探测，MCU 锚点有效期 15 秒。
- MCU 在接收下级电机固定反馈帧末字节时记录左右独立 `_micros()` tick，并按帧结束绝对字节序号与解析结果精确匹配；伪帧头或坏 CRC 候选不会消费未来有效帧的时间戳。该时间表示 GD32 UART RX-end，不表示电机控制器内部 ADC/控制周期采样点。
- `0x16` payload 固定 40 字节、version 1；只保留一份 `sample_boottime_us`，取左右有效电机 RX-end 映射时间中较新者；旧长度和错误版本不再兼容。
- MCU 在 18 ms 双侧新样本时可提前上报，20 ms 到期上报 latest，单侧 50 ms 未更新后清除该侧 valid；只有发送成功才消费 sequence/new。
- SoC RX 改为单次 read 后立即打接收时间、增量解帧、ACK fast path 和完整帧 dispatch；坏长度/坏 CRC 后从缓冲区内下一组 `AA 55` 滑动重同步，50 ms 只作为残帧组帧超时；`0x16` 使用 latest slot，不积压历史电机反馈。RX 统计改为原子访问，消除接收线程与诊断读取间的数据竞争。
- `CLOCK_BOOTTIME` 获取下沉为 `hdi_os_time` 公共接口 `VSHDIOS_GetBoottimeUs()`；`hdi_uart` RX 记录 read 完成时刻，TX 记录 `TIOCSER_TEMT` 首次确认时刻，并修复无效 fd 门禁和错误的 termios `c_lflag` 赋值。
- `0x12` 速度下发使用事件驱动持久状态和 latest-wins；当前最新速度不按年龄丢弃，也不因超期自动 stop。发送端记录 published/delivered version，marker 入队或 UART 写瞬时失败后保留 pending，队列恢复后重试最新版本；零速、混合零速和非零速度遵循同一状态语义，独立急停仍走最高优先级命令。
- MCU OTA 与电机 OTA 顶层流程成对持有 app_uart maintenance gate；窗口内仅 maintenance owner 可投递通用命令，其他线程返回 `BUSY`，后台 `0x1A` 时间同步暂停，速度变化只更新 latest pending；退出后立即恢复同步和未送达最新速度。
- Sensor 将 MCU `sample_boottime_us` 按当前 BOOTTIME/Unix 偏移换算为 Unix 微秒，写入 `MotorData.header.timestamp`；同步无效、source 未来或传输年龄超过 50 ms 时回退 SoC 接收时刻并清除 `SYNC_VALID`。
- Proto/Bridge/Vosen 只新增 `timing_flags=18`，采集时间统一使用 `header.timestamp`，`header.sequence=report_seq`。

## 验证命令

| Command | Exit Code | Result Summary | Layer |
| --- | ---: | --- | --- |
| `rtk python3 build/check_motor_uart_timestamp_contract.py` | 0 | 40 字节 golden layout、固定偏移、错误长度/版本拒绝、source/receive 时间门禁、BOOTTIME 分层和跨模块字段检查通过 | SoC contract |
| `rtk make modules/hdi_obj_all modules/app_obj_all modules/proto_obj_all modules/sensor_obj_all modules/bridge_obj_all -j20` | 0 | 受影响 SoC 库全部编译通过 | SoC modules |
| `rtk make app_ota_app_all pcr02_app_all -j20` | 0 | OTA 应用与 PCR02 整机目标编译通过 | SoC integration |
| `rtk bash scripts/codex-check.sh --full` | 0 | MCU 全部 Python 测试、Stage0/Stage1/App 构建、正式 bundle build/package 检查通过 | MCU full gate |
| `rtk git diff --check` 与 `rtk bash build/check_public_headers.sh` | 0 | SoC 根仓、app、hdi、sensor 和 MCU 空白检查通过，三组公共头镜像一致 | Source hygiene |
| `rtk python3 tools/diag/checks/check_diag_layer_deps.py` 等 3 个 AGENTS 指定检查 | 2 | 仓库中不存在对应脚本，无法执行；已确认没有同名替代脚本 | Negative/tooling gap |

- date：2026-07-27
- cwd：`workspace://xcrz-sigmastar-demo`、`workspace://gd32l235`
- scope：离线源码、编译、预算和 package；无设备写入

## 结果矩阵

| case | 期望 | 实际 | 状态 |
| --- | --- | --- | --- |
| MCU 新协议与上报 | `0x1A`、40 字节 `0x16`、RX-end tick、成功后消费 | 源码契约测试及全量构建通过 | pass |
| MCU Flash 门禁 | App 余量至少 4096 B | FLASH 47060/51200 B，余量 4140 B | pass，仅高于门禁 44 B |
| MCU RAM | 不超过 24 KiB | 14592/24576 B | pass |
| MCU OTA 构建边界 | Stage0/Stage1/App 和 bundle 均可生成 | Stage0 2280 B，Stage1 12936 B，bundle check 通过 | pass |
| SoC 受影响模块 | hdi/app/proto/sensor/bridge 可编译 | 定向目标全部通过 | pass |
| SoC OTA/整机依赖 | 通用 UART API 变更不破坏 app_ota/pcr02 编译 | 两目标通过 | pass |
| 协议负向输入 | 39/41 字节和 version 2 被拒绝 | contract test 通过 | pass |
| UART 流故障注入 | 伪帧头包住有效帧、坏 CRC 和 50 ms 残帧后恢复 | Python reference contract 与 C 源码契约检查通过 | pass（离线） |
| 事件驱动速度 | 不依赖刷新；入队/发送失败保留最新 pending；不按年龄 stop | published/delivered version 契约测试和 app 编译/整机链接通过 | pass（离线） |
| OTA 排他 | OTA 中仅 owner 可投递通用命令，不插入后台 0x1A 或合并速度，结束后恢复 | maintenance owner/gate 源码契约和 app_ota/pcr02 链接通过 | pass（离线） |
| 算法时间门禁 | 无效同步、未来 source、超过 50 ms source 回退 receive | contract test 通过 | pass |
| 板级 P99/同步误差/循环/soak | 满足设计验收阈值 | 未执行 | pending |
| 组合 image/OTA | 重生并核对各级制品身份 | 未执行 | pending |

## 失败路径证据

首次 MCU 完整实现构建得到 App FLASH 47336 B，余量 3864 B，低于 4096 B 门禁而失败。收敛到 40 字节单采集时间戳后一度为 46940 B；增加帧结束绝对字节序号精确匹配后为 47084 B，随后移除 ISR 每字节端口分支降到 47060 B、余量 4140 B并通过。该记录证明 Flash 预算失败路径实际生效，不是只记录成功路径。

SoC 规范要求的 `tools/diag/checks/check_diag_layer_deps.py`、`check_diag_naming.py`、`check_diag_interface_coverage.py` 三个脚本均不存在，实际执行均返回 exit 2；`rg --files` 也未找到同名或明确替代项。该缺口不影响已执行的 app/hdi/sensor/bridge/proto 编译证据，但不能声称这些 diag 专项门禁通过。

## 算法使用边界

本仓只发现 Sensor 到 Bridge/Vosen 的电机数据出口，没有实际融合算法实现。Sensor 已完成 source/receive 门禁与 Unix 时间换算；下游算法直接使用 `MotorData.header.timestamp`，并用 `timing_flags.bit0` 判断它是 MCU 采集时间还是 SoC 接收时间回退。receive time 只在 Sensor 内部用于质量/传输延迟门禁，不再作为 Proto 业务字段扩散，也不与 source time 求平均。

## 结论

结果为“源码实施和离线构建通过，HIL 与发布验收待完成”。`0x1A`、40 字节 `0x16`、MCU 采样时间戳、SoC 收发链路、`header.timestamp` 和 Proto/Bridge 质量标志已形成可审查工作区实现。由于没有板级和最终制品证据，不能声明实时指标达标、升级窗口闭环或可发布。

## 剩余风险

- MCU App Flash 仅比 4096 B 门禁多 44 B；后续任何 App 增量都必须重跑预算检查，建议后续单独安排进一步瘦身。
- 115200 8N1 下 50 字节完整帧线时约 4.34 ms，50 Hz 占链路约 21.7%；仍需要板级拥塞和控制优先级验证。
- Linux read 时间戳包含内核调度延迟，GD32 timestamp 也只是下级帧 RX-end；是否需要线时反推或额外补偿由 HIL 决定。
- `VSHDIUART_WaitTxDone()` 依赖目标串口驱动支持 `TIOCSERGETLSR/TIOCSER_TEMT`；交叉编译通过不等于板上 ioctl 已验证，必须在目标板确认成功路径和 200 ms 超时路径。
- app_ota/pcr02 编译通过只证明依赖未破坏；后编译 app、库或 MCU bundle不会自动进入已经生成的 image/OTA。
- 工作区包含用户既有未提交改动，本报告不把全部 dirty diff 归因于本任务。

## 后续动作

1. 板级测量 `0x16` 周期、GD32 RX-end 到 SoC callback、同步 uncertainty、`header.timestamp` 误差和下发延迟 P99。
2. 执行 SoC/MCU 重启、逐字节/粘包/坏 CRC 注入、1000 次循环和 2 小时 soak。
3. 演练先 MCU、后 SoC 的混合版本业务屏蔽门禁。
4. 重生组合 image/OTA，并逐级核对 MCU bundle、SoC app、image 和 OTA 的 size、MD5、BuildID 和生成时间。

```yaml
manual_validation_pending: true
manual_validation_reason: 缺少板级时延、同步误差、循环、soak、升级窗口和最终组合制品身份证据
required_followup: HIL、升级门禁演练和组合制品身份核对
owner: leiwenjun
review_after: 2026-10-27
```
