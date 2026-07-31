---
id: pcr02-active-low-1-no-h26x-light-meter-power-gate-20260727
title: PCR02 ACTIVE_LOW_1无H26x流关闭light-meter决策
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/active-low-1-no-h26x-light-meter-power-gate-20260727.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: internal-project-doc
  from: xcrz_sigmastar_demo_dev/DESIGN.md
  source_sha256: a8991aebb1dfd71852d376b9a78abda659a25e237a21fd95412d54bbc3ac6cb8
review_after: '2026-10-25'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- camera-pipeline
- low-power
validation_refs:
- projects/pcr02-ssc305/decisions/active-low-1-no-h26x-light-meter-power-gate-20260727.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/active-low-1-no-h26x-light-meter-power-gate-20260727.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-27'
updated_at: '2026-07-27'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-27'
manual_validation_pending: true
summary_zh: 补充并收紧同日ACTIVE_LOW_1架构候选：30fps AUTO仅在充电且H26xStreamGate effective时启用soft-light；无H26x编码流时强制白天、回退ADC并关闭light-meter，避免ISP最小链路被无效保活。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1无H26x流关闭light-meter决策
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI VI 组件化 Pipeline 与光敏策略设计

## 1. 结论

本设计只保留三种 profile：

| Profile | 物理 FPS | SOC | LDC | VIF sleep | 软光敏 | 实际日夜状态 | RAW/VENC |
|---|---:|---|---|---|---|---|---|
| `OFF` | 无活动 Sensor | 常醒 | Off | Off | Off | 白天 | 全部关闭 |
| `ACTIVE_LOW_1` | 1 | 常醒 | Off | Off | Off | 强制白天 | 严格按需 |
| `NORMAL_30` | 30 | 常醒 | 有媒体流时 On | Off | 仅充电且 AUTO | 按下述策略 | 严格按需 |

`LIGHT_ONLY_1` 和平台 AOV/suspend 语义均删除，不保留兼容别名。1fps 与 30fps 是物理 Sensor FPS，不用软件丢帧冒充。

SSC305 当前没有通过验证的 Sensor FPS 热切换能力，因此 1fps/30fps 使用安全 COLD rebuild。保留的 retained executor 只是能力受控的未来扩展点；`sensorFpsHotSwitch=0` 时不可进入。

## 2. 光敏选择

光敏源选择函数为：

```text
soft_light = (fps == 30) && charging && (light_mode == AUTO) && h26x_gate_effective
```

其余组合全部使用 ADC 硬光敏。光敏检测状态与最终应用到 IR/IQ 的日夜状态分离：

| FPS | 充电 | 模式 | H26x 编码流 | 光敏源 | 应用状态 | HDI light-meter demand |
|---:|---|---|---|---|---|---|
| 1 | 任意 | 任意 | 任意 | ADC | 强制白天 | 禁止 |
| 30 | 是 | AUTO | 有效 | ISP AE 软光敏 | 检测结果 | On |
| 30 | 否 | AUTO | 有效 | ADC | 检测结果 | Off |
| 30 | 任意 | AUTO | 持续无流 | ADC | `H26xStreamGate` 强制白天 | Off |
| 30 | 任意 | DAY/NIGHT | 任意 | 手动状态，不使用软光敏 | 显式 DAY/NIGHT | Off |

`VSHDIVI_SetLightMeterDemand(true)` 在非 30fps profile 直接返回 invalid-state，planner 也会拒绝 `ACTIVE_LOW_1 + LIGHT_METER`，形成 public API 和 graph compiler 两层约束。

软光敏使用 D2N/N2D 迟滞阈值和 3 秒单调时钟驻留确认。它不再按 task 调度次数假设“稳定帧”，因此调度抖动或重复读取同一 AE 样本不会缩短确认时间。日夜回调只发布确认后的边沿。

`ACTIVE_LOW_1` 仍可低成本采集和上报 ADC，但检测结果不驱动 IR、IRCUT、灰度模式或夜间 IQ；切入 1fps 后不等待 AUTO 最小驻留，下一次策略检查即应用白天状态。AUTO worker 的检查周期为 500ms，非 AUTO 也使用 500ms 带超时等待，避免显式 NIGHT 在 FPS 改变后无限维持补光。获取 FPS 失败时也按非 30fps 处理并强制白天，避免状态不明时维持高功耗补光。

## 3. Demand 与资源编排

独立 demand：

- `MAIN`
- `SUB`
- `RAW_PREVIEW`
- `LIGHT_METER`，仅 `NORMAL_30`

资源规则：

| Demand | Backbone SNR/VIF/ISP | ISP port1 | LDC | SCL | VENC |
|---|---|---|---|---|---|
| 无 | Off | Off | Off | Off | Off |
| 仅 `LIGHT_METER` | On | Off | Off | Off | Off |
| 1fps RAW/VENC | On | On | Off，ISP 直连 SCL | 按需 | 按需 |
| 30fps RAW/VENC | On | On | On | 按需 | 按需 |
| 30fps 媒体 + light | 复用媒体 backbone | 复用 | 复用 | 复用 | 按需 |

MAIN、SUB 不再隐式同时编码。SUB-only 在平台声明 `subDirect` 时可独立创建；RAW 与两路 VENC 可任意组合。

## 4. 组件职责

### 4.1 Planner

`hdi_vi_pipeline.[ch]` 只负责：

- 将 profile + demand 编译为目标 graph；
- 校验 1fps 禁止 LDC/软光敏；
- 计算 COLD/HOT/QUIESCED route；
- 输出按“先停 monitor、再拆消费者，先建媒体、最后启 monitor”排序的操作计划。

Planner 不直接调用 SigmaStar API。

### 4.2 Executor

`hdi_vi.c` 负责：

- 执行 SNR/VIF/ISP/LDC/SCL/VENC 生命周期；
- 维护 exact demand、active mask 和失败回滚；
- 在最后一个媒体 demand 关闭时，仅当 30fps 软光敏仍有效才保留最小 backbone；
- 在 graph/ISP 拆除前停止并 join light monitor；
- 应用 LDC、AWB、VIF sleep 等 runtime policy。

### 4.3 IR policy

`IrLight` 负责业务选择，不直接编排媒体节点：

- 接收充电状态、AUTO/DAY/NIGHT 模式和当前 FPS；
- 选择 ADC 或 HDI light-meter；
- 将软光敏回调转换为 IR/IQ 状态切换；
- 仅在 30fps 应用夜间状态；1fps 无条件应用白天；
- 30fps AUTO 复用 `H26xStreamGate`，编码流持续不存在时应用白天；
- 30fps AUTO 无 H26x 流时关闭 light-meter，避免 soft-light 单独保活 ISP；
- 切回 ADC 时重置中值滤波和迟滞状态。

UART charge callback 只更新原子状态并唤醒 worker，不同步执行 ISP 初始化/反初始化，避免阻塞串口分发线程。worker 最迟在约 100ms 内处理充电状态变化；稳定状态仍按 500ms 周期检查。

### 4.4 Diagnostics

`diag.hdi.vi.isp.dump` 输出：

- `soft_light.requested`
- `soft_light.active`
- `current_light`、`last_light`
- `stable_ms`
- D2N/N2D threshold
- 当前 FPS、LDC 状态和 ISP 生命周期耗时

`requested=1, active=0` 只允许出现在 FPS/lifecycle 事务窗口或错误恢复过程中，便于定位实际 graph 与业务 demand 不一致。

## 5. 切换事务

### 5.1 30fps 到 1fps

1. lifecycle gate 关闭；
2. 停止 light monitor；
3. drain VENC/RAW 消费者；
4. 解绑并销毁 LDC/SCL；
5. 停止并反初始化 ISP/VIF/SNR；
6. 以物理 1fps 重建；
7. 只重建目标 RAW/VENC demand，ISP 直连 SCL；
8. 保持 VIF sleep off，应用低频 AWB policy；
9. lifecycle gate 打开；
10. IR worker 确认 soft-light demand 为 Off，保留 ADC 采样并立即应用白天状态。

不在运行中的 ISP/LDC graph 上修改 Sensor FPS 或重绑端口，避免 CMDQ wait、延迟、花屏和首帧不可控。

### 5.2 1fps 到 30fps

流程相反。媒体创建完成后 VENC 请求 IDR，再开放数据回调。若处于充电 + AUTO，IR worker 随后打开 light-meter；已有媒体 graph 时只启动 monitor，不重建 ISP。

### 5.3 30fps 光敏源切换

- 媒体 graph 活跃：ADC 与软光敏切换只增删 monitor demand，不 deinit ISP/LDC。
- 无媒体 demand：打开软光敏会创建 SNR/VIF/ISP 最小 backbone；关闭软光敏会销毁该 backbone，因此会产生 ISP deinit 耗时。

设备不会频繁改变充电状态或 1/30fps profile，故选择严格释放资源，不为罕见切换长期保留 ISP。若未来实测充电抖动导致频繁 init/deinit，应在 IR policy 增加充电状态去抖/最小驻留，不应绕过 demand 模型永久保活。

## 6. 并发、失败与回滚

- FPS、媒体 demand、light-meter demand 共用单一 lifecycle gate，冲突请求返回 busy。
- 媒体 topology 由 VI mutex 串行化。
- soft-light 状态使用独立 mutex；monitor 不持有 VI mutex 执行 AE 查询。
- graph 拆除先将 monitor 标记 inactive，再 stop/join，防止 ISP deinit 与 AE query 并发。
- demand 更新失败恢复旧 requested state；回滚也失败时将 FPS/topology state 标记 invalid，后续控制请求拒绝继续运行。
- callback 在 soft-light mutex 外执行，避免 sensor 回调与 threshold/state API 形成锁递归。

## 7. ISP deinit 耗时处理

本设计不把“避免 deinit”当成默认正确路径：

- 物理 1/30fps 切换：当前必须 deinit/reinit，平台热切换尚未通过 HIL。
- 30fps 媒体活跃时的硬/软光敏切换：不 deinit。
- 最后一个 demand 关闭：为功耗目标执行 deinit。

诊断保留 ISP stop/destroy、LDC deinit 和总切换耗时。优化顺序应是先测量具体阶段，再评估：

1. 平台是否支持稳定的 ISP device/channel retained；
2. Sensor mode、IQ、capture geometry 是否保持同一 lifetime key；
3. VIF source-gated rebind 是否在长稳和异常注入下无 CMDQ reset；
4. 首帧是否为受控 IDR、PTS 是否单调、RAW 是否无旧 session 帧。

上述条件未全部通过前，禁止仅为缩短耗时启用 retained fast path。

## 8. 已冻结应用策略

- `ACTIVE_LOW_1` 的实际状态固定为白天，不因 RAW/VENC demand、充电状态、AUTO 检测结果或显式 NIGHT 改变；策略收敛上界约 500ms，不包含底层 IR/IQ 调用自身耗时。
- `NORMAL_30 + AUTO` 保留 `H26xStreamGate`：编码流停止后经过既有 6 次检查宽限，强制切回白天并关闭 light-meter；强制切换不再叠加 AUTO 的 3 秒最小驻留。
- `NORMAL_30 + DAY/NIGHT` 是显式人工覆盖，不受 H26x gate 影响。
- H26x gate 只决定是否应用检测出的夜间状态，不参与 ADC/软光敏源选择。

若未来要求 1fps 夜视补光，或要求 30fps 显式 NIGHT 也必须受编码流 gate 限制，应作为新的产品策略变更，并重新评估功耗和状态机验收，不能隐式修改 pipeline profile。

## 9. 验收

- host contract test 覆盖 OFF、1fps RAW-only/VENC-only/组合、1fps 拒绝 LDC/light、30fps light-only 和 media+light。
- HDI 与 app 使用目标 ARM 工具链编译。
- sensor 至少证明 `irlight.cpp` 目标 object 成功生成；整模块若被无关 protobuf 版本错位阻塞，必须保留原始失败证据。
- 模块头与根公共头逐字节一致。
- 负向扫描不得出现 `LIGHT_ONLY_1`、`PROFILE_AOV_1` 或旧软光敏状态机符号。
- 设备 HIL 后续至少覆盖 30→1 立即关补光、1fps 持续强制白天、1→30 恢复策略、30fps AUTO 无编码流回白天、MAIN/SUB 独立 demand、RAW-only、充电切换、首帧 IDR、花屏和各阶段耗时。
