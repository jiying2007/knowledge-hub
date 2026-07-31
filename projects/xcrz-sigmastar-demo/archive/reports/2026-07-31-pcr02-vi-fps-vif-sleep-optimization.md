---
id: pcr02-vi-fps-vif-sleep-optimization-20260731
title: PCR02 SSC305 物理1fps/30fps VIF Sleep切换优化归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-07-31-pcr02-vi-fps-vif-sleep-optimization.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: device-hil-and-source-validation
  from: 2026-07-31当前源码、项目探索记录、单台PCR02设备HIL和增量内核日志的脱敏摘要
  source_sha256: fa187b6fdd57746ab80014d5dfe4a449147e05895bb97666b3a0f3c752ebffa9
  temporary_source_retained: false
review_after: '2026-10-31'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- sc5336p
- hdi-vi
- 1fps
- 30fps
- vif-sleep
- hot-switch
- cmdq
- device-hil
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-31-pcr02-vi-fps-vif-sleep-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-07-31-pcr02-vi-fps-vif-sleep-optimization.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-31'
updated_at: '2026-07-31'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-31'
manual_validation_pending: true
summary_zh: 固化PCR02 SSC305/SC5336P物理1fps/30fps切换的低帧VIF sleep与1000ms单帧重唤醒方案、已证伪CMDQ路径、同步API性能、首帧、PTS及5/20/3×10轮设备验证边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 SSC305 物理 1fps/30fps VIF Sleep 切换优化归档

## 归档目的与结论边界

本文固化 PCR02 SSC305、SC5336P Sensor 在 RAW preview 与 H26x main/sub
同时工作的 HOT profile 下，物理 1fps/30fps 同步切换的根因、最终实现和板级
验证证据。

当前可确认：

- 低帧 profile 与高帧 profile 均实际修改物理 Sensor FPS，不以应用丢帧模拟。
- 低帧图采用 VIF sleep 加 1000ms 单帧重唤醒后，1→30fps 最坏同步 API
  时间已低于 1.8s，RAW/main/sub 首帧均低于 2.0s。
- 公开同步 API 的签名和完成语义未改变；调用返回时目标 Sensor FPS、目标图和
  运行时策略已经应用。
- 5 轮正式验收、20 轮长循环和额外 3 组×10 轮资源探测均通过，未观察到
  PTS 回退、CMDQ reset、timeout 或资源指标单调增长。
- 最终候选只部署到设备临时分区，未修改持久分区。

结论范围：

- 证据来自单台 PCR02 SSC305 样机和 SC5336P 配置。
- HOT 路径是“完整关闭消费者和旧低图后保留 ISP Device/Channel/IQ 的组件
  事务”，不是在运行中的 Sensor/LDC/CMDQ 图上原位改 FPS。
- `sensor_fps=29` 是平台对目标 30fps 的查询取整结果。
- 资源验证说明本轮未观察到泄漏，不等同于跨设备、跨驱动版本的形式化无泄漏
  证明。
- 本文不保存设备 IP、真实 SN、凭证、二进制、raw 日志或本机绝对路径。

## 根因

物理 1fps 低图持续处于 armed 状态时，销毁 SCL、解绑边或停止源会等待一个
或多个低帧周期。实机阶段测量证明：

- 并行关闭不同消费者只能把约 1s 等待移动到源解绑或后续销毁。
- 提前停止 VIF 会使下游 CMDQ 缺少最终 trigger，性能退化且增加 reset 风险。
- output UserFrc、input FRC、buffer depth 和 teardown 顺序不能稳定消除总等待。
- 在 live graph 上修改 Sensor、LDC、SCL 或绑定关系，功能输出可能恢复，但
  干净增量内核日志会出现 CMDQ reset，因此不能作为可交付优化。

问题本质不是某一个 Stop API 本身固定很慢，而是旧低帧事务仍在等待物理帧
trigger。要缩短同步销毁时间，必须让旧图在切换开始前进入可安全停止的静默态。

## 最终方案

### 低帧运行策略

切到 `ACTIVE_LOW_1` 后：

1. Sensor 设置为物理 1fps。
2. 低帧轻量图继续使用 `ISP realtime port0 -> SCL`，不创建 LDC。
3. VIF 配置为输出 1 帧后进入 sleep。
4. 周期任务每 1000ms 执行一次
   `sleep disable -> sleep enable(frameCntBeforeSleep=1)`。
5. 每次重唤醒只供应一个物理低帧，然后重新进入静默态。

该行为参考 SigmaStar AOV 示例中的 VIF sleep/re-arm 合约，但不引入平台
suspend 或软件丢帧语义。

### 1→30fps 事务

1. lifecycle gate 串行化 FPS 请求。
2. 将周期任务标记 inactive，执行 TaskStop、TaskClose 和 thread join。
3. 保持 VIF sleep，按 sink-to-source 顺序关闭 H26x、RAW、SCL 和旧低图。
4. 停止 ISP 输出与 VIF，并解绑 VIF→ISP realtime edge。
5. 在旧图已经不存在、VIF 已停止且解绑的 CMDQ-free 窗口关闭 VIF sleep。
6. 设置 Sensor 30fps。
7. 启动保留的 ISP Channel/IQ，绑定目标边并创建 LDC/SCL/VENC/RAW。
8. 请求 main/sub IDR，更新 generation，校验目标图和运行时状态后返回。

该顺序同时满足：

- 不在 live CMDQ 图上修改 Sensor FPS；
- 不让睡眠 VIF 阻止 Sensor VTS 提交；
- 不等待旧 1fps graph 的下一帧完成销毁；
- API 仍保持同步完成语义。

### 失败恢复

- 周期任务配置或启动失败时，立即关闭已经启用的 VIF sleep，避免留下
  “VIF 已睡眠但没有重唤醒任务”的半应用状态。
- FPS 事务失败时恢复旧 FPS、旧 graph 与旧运行策略；回滚失败才将 topology
  标记 invalid 并拒绝后续控制请求。
- deinit 和 FPS 事务都会停止并 join 周期任务，避免后台 re-arm 与 graph
  生命周期并发。

## 已证伪路径

以下路径均未进入最终实现：

| 路径 | 结果 | 处理 |
| --- | --- | --- |
| 并行停止 H26x/RAW/SCL | 等待点转移，总切换仍约 2.2s | 撤回 |
| 提前关闭 VIF | 低图 drain 退化，首帧显著变慢 | 撤回 |
| output/input FRC 改为 30→30 | API 成功，但 teardown 仍约两个低帧周期 | 撤回 |
| SCL/ISP depth 调整 | 无稳定收益，极端配置被平台拒绝 | 撤回 |
| Sensor/VENC live update | 功能时序变快，但出现 CMDQ reset | 删除 |
| 保留 LDC 的 same-topology 原位切换 | 干净增量日志出现 CMDQ reset | 删除 |
| source-first 或 edge unbind/rebind | 存在 CMDQ reset/递归 reset 风险 | 删除 |
| SCL stop→LDC stop→ISP stop 同拓扑切换 | 输出可恢复，但 CMDQ 安全性不通过 | 删除 |
| 700ms VIF re-arm | 3.5s 内输出 6 帧，物理帧率过高 | 恢复 1000ms |

## 验证证据

### 本地验证

| 验证 | 结果 |
| --- | --- |
| HDI pipeline host contract test | PASS |
| HDI object build | PASS |
| HDI static/dynamic library build | PASS |
| `prog_test` 强制重链接 | PASS |
| 最终主机与设备二进制 MD5 对比 | 一致：`724849aa53f37dacabab139583c2295e` |

### 正式 5 轮 HOT/both 验收

| 指标 | 最坏值 |
| --- | ---: |
| 30→1fps 同步切换 | 0.539609s |
| 1→30fps 同步切换 | 0.873710s |
| RAW 首帧 | 1.007596s |
| main 首 IDR | 1.004928s |
| sub 首 IDR | 1.007531s |
| main/sub PTS rollback | 0/0 |

5 轮共 10 次切换全部 PASS，低帧状态为 Sensor=1、LDC off、VIF sleep on；
高帧状态为 Sensor=29、LDC on、VIF sleep off。

### 长循环和物理帧率

- 最终候选连续 20 轮全部 PASS：
  - 最大同步切换 0.922258s；
  - 三路首帧最大 1.061776s；
  - main/sub PTS rollback 为 0/0。
- 低帧驻留 2.5s：
  - Sensor 查询为 1fps；
  - RAW/main/sub 各收到 4 帧，符合切换首帧加 1s 周期单帧重唤醒；
  - 恢复高帧后 Sensor 查询为 29fps，三路驻留期各约 38 帧；
  - 1→30fps 为 0.872564s，首帧约 1.005s。
- 1000ms re-arm 边界竞争压力 5 轮全部通过：
  - 最大切换 1.053349s；
  - 三路首帧最大 1.192857s；
  - PTS rollback 为 0/0。

### 资源与内核安全

最终候选额外连续执行 3 组×10 轮，三组均为 10/10 PASS。每组结束后的指标：

| 组 | Slab | SUnreclaim |
| ---: | ---: | ---: |
| 1 | 14248kB | 11728kB |
| 2 | 14260kB | 11740kB |
| 3 | 14208kB | 11688kB |

指标没有单调增长。每组测试使用清空后的增量内核日志检查，均未出现：

- `CmdqResetCount`
- `WAIT_TRIG_TIMEOUT`
- `POLLNEQ_TIMEOUT`
- VIF wake/re-arm failure
- Call trace、BUG 或 Oops

ISP 初始化阶段仍会打印板级无马达配置和部分受限 AF ioctl 的既有诊断；这些
日志在基线和最终版本中均存在，没有导致 HIL 失败，也不属于本次 CMDQ/FPS
问题。

## 实现与回退定位

主要实现：

- `modules/hdi/src/hdi_video/hdi_vi.c`
  - VIF sleep enable/disable；
  - 1000ms 单帧重唤醒任务；
  - 任务启动失败清理；
  - FPS/deinit 前 TaskClose/join；
  - 旧图销毁后的 VIF wake + Sensor 30fps 顺序。
- `modules/hdi/src/hdi_video/hdi_vi_pipeline.c`
  - `ACTIVE_LOW_1` 保持 ISP port0 直连 SCL 的轻量拓扑。
- `app_test/app_test_vi_fps_hil.c`
  - 验证低帧 VIF sleep on/LDC off、高帧 VIF sleep off/LDC on；
  - 验证 Sensor FPS、generation、首帧、IDR 和 PTS 单调性。

回退方式：

1. 保留 VIF sleep/re-arm 之前的安全全重建候选，仅用于回归比较。
2. 若新 Sensor/SDK 组合不支持 VIF sleep contract，禁用新策略并恢复安全全重建；
   不得回退到任何已证伪的 live/in-place 路径。
3. 回退后的预期代价是 1→30fps 回到约 2.24–2.30s，而不是接受 CMDQ reset。

## Supersedes 候选

本文建议部分替代以下旧结论，但在 owner 复核前只保持 `reviewing`，不修改旧文：

- `projects/pcr02-ssc305/archive/design/2026-07-27-active-low-1-pipeline-architecture.md`
  - `ACTIVE_LOW_1` 的 `VIF sleep` 不再为 Off，而是“首帧后 sleep +
    1000ms 单帧重唤醒”。
  - 1fps/30fps 不再限定为完全 COLD rebuild；当前 HOT 组件事务已通过本轮
    单机 HIL，但 live/in-place Sensor/LDC 更新仍禁止。
- `projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-full-optimization-closeout.md`
  - 以本文最终 MD5 和 5/20/3×10 轮数据更新性能及稳定性证据。
- `projects/xcrz-sigmastar-demo/current/decisions/active-low-1-hot-switch-experiment.md`
  - HOT 路径已取得本配置的板级通过证据，但是否从 experiment 提升为正式能力
    仍需 owner 决定，不由本归档自动完成。

旧文保留为历史 provenance。

## 后续验证

1. 在另一台 PCR02 和另一批次 SC5336P 上重复 5/20 轮 HIL。
2. 在 SDK/驱动升级后复测 VIF sleep/re-arm contract 和增量内核日志。
3. 增加 VIF TaskOpen/ConfigTimer/StartMonitor 失败注入，验证清理和旧 graph 回滚。
4. 若准备把 HOT 从 experiment 提升为正式能力，单独生成 owner decision，
   不以本归档的 `reviewing` 状态替代人工决策。

## Provenance

- captured_at：2026-07-31
- source：当前源码、项目内探索记录、单机 HIL、增量内核日志和构建结果的脱敏摘要
- source workspace：`xcrz-sigmastar-demo`
- evidence state：source-build-device-hil-validated
- manual validation：仍需 owner 复核归档内容和跨设备适用范围
