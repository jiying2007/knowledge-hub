---
id: pcr02-active-low-1-warm-switch-experiment-20260728
title: PCR02 ACTIVE_LOW_1 WARM切换实验决策
kind: decision
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/decisions/active-low-1-warm-switch-experiment.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-validation
  from: xcrz-sigmastar-demo
  source_sha256: b628ef7738a4329c363634bf90fa8ce6478314c67537a781789646469086e4a4
review_after: '2026-08-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- ssc305
- hdi-vi
- warm-switch
validation_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-warm-switch-experiment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/current/decisions/active-low-1-warm-switch-experiment.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: SSC305物理1/30fps默认保持COLD；显式环境变量可启用保留ISP Device、重建Channel/IQ/下游graph的WARM实验，板级最大切换2.281秒，未完成24h长稳、故障注入和功耗资格。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 ACTIVE_LOW_1 WARM切换实验决策
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# HDI VI ACTIVE_LOW_1 完成前门禁

## 1. 范围与结论

验证覆盖组件化 graph planner、HDI runtime/demand API、物理 1/30fps COLD rebuild、低帧率 AE
预热、generation callback barrier、LDC cache、低帧率 teardown boost、目标 LDC 并行预热、
MAIN/SUB/RAW 独立 demand、首个 IDR、PTS 单调性、soft-light/IR policy、app diagnostics、
快速板测工具和 ARM 完整应用链接。

结论：

- host contract、目标 ARM 构建、快速工具和 172.16.16.43 设备 HIL：PASS。
- 平台 AOV/suspend、24h soak、功耗仪数值和真实 IR/充电硬件联动：不在本轮完成声明内。
- 生产默认保持 COLD capability。`HDI_VI_EXPERIMENTAL_WARM_SWITCH=1` 可显式启用
  ISP Device-retained/Channel-rebuild 实验；它已通过本板短压测，但未取得量产默认资格。
- 没有用在线解绑改属性或旧 ISP Channel Stop/Start 冒充已验证的热切换。

## 2. 设备与安全边界

- 设备：`172.16.16.43`。
- NFS：设备 `/mnt` 对应主机 `~/nfs/app`。
- 测试程序：`/mnt/prog_test.hdi_vi_final`、`/mnt/prog_tool.hdi_vi_final`。
- 测试前 `prog_daemon`、`prog_pcr02` 均未运行；测试完成后保持同一基线。
- 用户已授权在单元/压力测试期间停止这两个进程；通用 runbook 必须先记录原状态，结束后只恢复原来运行的进程。
- 未覆盖 `/customer`，未替换设备持久程序。

## 3. Host/构建证据

| 验证 | 结果 | 说明 |
|---|---|---|
| `rtk make -C tests/hdi_vi_pipeline run` | PASS | OFF/ACTIVE_LOW_1/NORMAL_30、demand 与 route contract |
| `rtk make -C tests/sensor_ir_policy run` | PASS | 1fps 强制白天、30fps AUTO/H26x gate、ADC/软光敏选择 |
| `rtk make modules/hdi_lib_all modules/app_lib_all -j20` | PASS | HDI runtime 与 app diag ARM library |
| `rtk make app_test_app_all app_tool_app_all -j20` | PASS | 快速 HIL/诊断工具 |
| `rtk make pcr02_app_all -j20` | PASS | 完整应用链接 |
| 公共头 SHA-256 | PASS | `modules/hdi/include/hdi_vi.h` 与 `include/hdi/hdi_vi.h` 一致 |
| runtime 负向扫描 | PASS | 无固定 RAW hold、无临时 warmup probe、app_test 不直接改 Sensor FPS |
| 相关仓 `diff --check` | PASS | 无 whitespace error |
| HDI diag 三项专项脚本 | UNAVAILABLE | `modules/hdi/AGENTS.md` 指定路径在当前工作树不存在，全仓搜索无同名脚本 |

最终哈希与完成前复跑时间见本文件第 8 节。

## 4. 板端 HIL 证据

### 4.1 RAW-only

命令：

```text
/mnt/prog_test.hdi_vi_final vi_fps_hil 5 100 none 5000
```

结果：

- 5/5 轮 PASS。
- 1fps API：2.073～2.090 秒。
- 30fps API：3.298～3.354 秒；优化前基线为 4.812 秒。
- 最大首 RAW：3.739 秒。
- 每轮 1fps：`ldc=0`、`h26x_active_mask=0`、soft-light Off、VIF sleep Off。
- 每轮 1fps：`low_fps_warmup_used=1`、AE count=11、warmup 约 0.596 秒。
- 每轮 1→30fps：`cold_teardown_boost_ret=0`、`cold_ldc_prewarm_ret=0`；
  LDC prewarm 约 0.843～0.845 秒，join wait 4～5 微秒。

### 4.2 独立 VENC demand

| 用例 | 结果 | 关键断言 |
|---|---|---|
| MAIN-only 2 轮 | PASS | SUB frame/IDR=0 |
| SUB-only 2 轮 | PASS | MAIN frame/IDR=0 |
| MAIN+SUB 10 轮 | PASS | 两路 requested/active/recv/thread mask=3，首 IDR mask=3 |

独立 demand 最终摘要：

| 用例 | 最大 switch | 最大首 RAW | 最大首 MAIN IDR | 最大首 SUB IDR | PTS rollback |
|---|---:|---:|---:|---:|---:|
| MAIN-only 2 轮 | 3.365s | 3.736s | 3.733s | 0 | 0 |
| SUB-only 2 轮 | 3.366s | 3.747s | 0 | 3.735s | 0 |
| MAIN+SUB 10 轮 | 3.426s | 3.800s | 3.789s | 3.790s | 0 |

MAIN+SUB 10 轮中，30→1fps API 为 2.166～2.223 秒，1→30fps API 为 3.323～3.426 秒；
优化前 1→30fps 基线为 5.845 秒。ISP `DestroyDevice` 每轮约 0.999 秒。

### 4.3 PTS 压力门禁

测试工具对每路完整 AU 的 PTS 做严格递增检查，发现 `current <= previous` 即打印两值并使 summary
失败。一次早期长循环曾捕获 MAIN/SUB 各 1 次非单调 PTS，因此 HDI 输出层增加了重复/回退 PTS
丢弃保护，未放宽测试。

最终命令：

```text
/mnt/prog_test.hdi_vi_final vi_fps_hil 10 100 both 5000
```

最终结果：

- 10/10 轮 PASS。
- `main_pts_rollback=0`、`sub_pts_rollback=0`。
- RAW/MAIN/SUB 各 51 帧、两路各 21 个 IDR。
- 最大 COLD switch `3426060us`。
- 最大 RAW first frame `3800158us`。
- MAIN/SUB first IDR 最大值分别 `3789280us`、`3789622us`。
- 10 次 LDC prewarm 均成功，单次约 0.843～0.846 秒，join wait 约 0.1ms。
- 测试日志无 CMDQ reset、fatal、assert 或崩溃；平台 AE/AWB 诊断 query 有 42 条
  `Operation not permitted` 噪声，未影响媒体或 summary。

R18 join 失败保护落地后的最终二进制另复跑 MAIN+SUB 2 轮：

- 2/2 轮 PASS。
- 最大 switch `3385016us`，最大 RAW/MAIN/SUB 首帧或首 IDR分别为
  `3757969us`、`3749216us`、`3750153us`。
- `main_pts_rollback=0`、`sub_pts_rollback=0`，无 prewarm failure/CMDQ reset/fatal。

### 4.4 app_tool smoke

命令：

```text
/mnt/prog_tool.hdi_vi_final session --mode=local --script=/mnt/app_tool_vi_smoke.diag
```

结果：`script_end ret=0, ok=1`。30→1→30 三次 dump 确认：

- app_tool 可按需本地初始化/反初始化 VI，不依赖 `prog_pcr02`。
- 1fps：LDC Off、VENC Off、soft-light Off、warmup AE count=11。
- 30fps：LDC 恢复，LDC calibration cache hit 增加。
- 三次 ISP dump 均包含 teardown boost、各 COLD teardown 分段和 LDC prewarm/join 指标；
  `isp_dump_too_large=0`，证明 8192-byte data 缓冲可以完整承载当前响应。

## 5. 延迟结论

- 原始物理 1fps 直接启动需要等待约 11 个 AE frame，首 RAW 约 9.6～9.7 秒。
- 新 graph 内部 30fps 有界预热后，首 RAW 降至约 3 秒，改善约 6.6 秒。
- COLD API 没有被包装成异步成功：返回前已经提交物理 1fps；callback 只在 lifecycle gate 打开后交付。
- 1fps 剩余约 0.9 秒主要是物理帧相位。
- ISP `DestroyDevice` 约 0.998 秒，是当前安全 COLD 的固定成本。
- 1→30fps RAW-only COLD API 从 4.812 秒降至 3.298～3.354 秒，改善约 30%。
- 1→30fps MAIN+SUB+RAW 从 5.845 秒降至 3.323～3.426 秒，改善约 41%～43%。
- 30→1fps 保持 2.07～2.23 秒，没有因 LDC 预热产生反向退化。
- 在线重复 bind 修改 FRC、预先 StopChannel 两项实验未降低总耗时，已从正式代码删除。
- realtime SCL/LDC/VENC 按需关闭的功耗方向成立，但本轮没有功耗仪，不能给出瓦特级收益声明。

## 6. Review、Breaking Change 与剩余风险

- blocker/major open：0；已修复项见 `REVIEW.md`。
- 删除 `LIGHT_ONLY_1`/AOV profile 语义，不提供兼容别名。
- `ACTIVE_LOW_1` 是唯一 1fps profile；RAW/MAIN/SUB 均按需。
- 1fps 禁止 LDC、soft-light、VIF sleep，实际 IR/IQ 固定白天。
- 回退必须成组恢复 HDI header/planner/runtime、sensor IR consumer、app diag 和快速工具。
- 剩余风险：功耗仪、真实 IR/充电联动、LDC 跨模块并发预热的 24h 长稳/温循/故障注入；
  diag 专项检查脚本在当前工作树缺失。

## 7. Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk make -C tests/hdi_vi_pipeline run` | 0 | planner contract PASS | `tests/hdi_vi_pipeline/` | Agent | pipeline planner |
| `rtk make -C tests/sensor_ir_policy run` | 0 | IR/light policy PASS | `tests/sensor_ir_policy/` | Agent | sensor IR policy |
| `rtk make modules/hdi_obj_all -j20` | 0 | 最终 HDI ARM object 编译通过 | `modules/hdi/src/hdi_video/hdi_vi.user.arm.o` | Agent | HDI runtime |
| `rtk make modules/app_obj_all -j20` | 0 | APP diag provider ARM 编译通过 | `modules/app/src/app_diag/provider/hdi/` | Agent | VI diagnostics |
| `rtk make app_test_app_all -j20` | 0 | 最终快速 HIL 工具链接通过 | `out/arm/app/prog_test` | Agent | `prog_test` |
| `rtk make app_tool_app_all -j20` | 0 | 最终诊断工具链接通过 | `out/arm/app/prog_tool` | Agent | `prog_tool` |
| `rtk make pcr02_app_all -j20` | 0 | 完整应用链接通过 | `out/arm/app/prog_pcr02` | Agent | `prog_pcr02` |
| `vi_fps_hil 5 100 none 5000` | 0 | RAW-only 5/5 PASS | 设备 `/tmp/vi_final_none5.log` | Workflow | 性能特征 |
| `vi_fps_hil 2 100 main 5000` | 0 | MAIN-only 2/2 PASS | 设备 `/tmp/vi_final_main2.log` | Workflow | exact demand |
| `vi_fps_hil 2 100 sub 5000` | 0 | SUB-only 2/2 PASS | 设备 `/tmp/vi_final_sub2.log` | Workflow | exact demand |
| `vi_fps_hil 10 100 both 5000` | 0 | both 10/10 PASS，PTS rollback=0 | 设备 `/tmp/vi_final_both10.log` | Workflow | stress/performance |
| `vi_fps_hil 2 100 both 5000` | 0 | R18 最终 join guard 2/2 PASS | 设备 `/tmp/vi_final_join_guard_both2.log` | Workflow | final binary |
| `prog_tool ... session --mode=local` | 0 | `script_end ok=1`，完整新增 diag 字段 | 设备 `/tmp/vi_final_tool_smoke.log` | Workflow | diagnostics |
| 三项 `tools/diag/checks/check_diag_*.py` | 2 | 负结果：脚本路径不存在；全仓无同名替代 | `modules/hdi/AGENTS.md` | Agent | missing gate |
| 重复 bind 修改 FRC | 0，但无改善 | 负结果：耗时不降，实验代码删除 | `DESIGN.md` 第 7 节 | Skill | rejected hypothesis |
| 预先 StopChannel | 0，但约 0.95s 等待迁移 | 负结果：收益约 0.05s，实验代码删除 | `DESIGN.md` 第 7 节 | Skill | rejected hypothesis |
| `rtk bash ~/codex/scripts/final-ready.sh` | 0 | final-ready PASS | `~/codex/.cache/session-coach-evidence.json` | Workflow | completion gate |

## 8. 最终复跑记录

最终复跑完成后记录：

- 日期：2026-07-28。
- 公共头哈希：`4134b2c8e15efb347f0e7f05ccb6b69108e9a3a0310adb92764e689338ad6449`。
- 最终 `prog_test` 哈希：`fc47bd23339f9bfedb6c08cc91eeb427456b95bf77cf14a83681d4ba2bc8ee33`；
  设备 `/mnt/prog_test.hdi_vi_final` 一致。
- 性能 10 轮所用 `prog_test` 哈希：`0a9f0f2f449bf7e55ed0705f176e15a290d1fdd6c03a27240ec40ab4cb33d40b`；
  最终哈希仅增加 R18 join 失败保护，最终版本已补跑 both 2 轮。
- ISP dump smoke 所用 `prog_tool` 哈希：`4d9980e587fce775017d9ec29b158ff4de1d9ab14dab914c0c8d64876a541f24`；
  设备 `/mnt/prog_tool.hdi_vi_final` 一致。
- 最终 `prog_tool` 哈希：`da5f9366d9e75054cd8fa8bce3bbf0ee2347c0eed742f63fd941db3a34727b94`。
- 最终 `prog_pcr02` 哈希：`2b3454704f942d809dc94e5c24657831417f5e17a6a4266366a40583ce5e5eba`。
- final-ready：PASS，退出码 0。
- session coach：`THREAD_LONG/CTX_PRESSURE` 要求本轮立即收口并在后续新线程继续；同时报告的
  `~/codex` skill/governance dirty 项不属于本项目变更，本轮未修改或清理。
- 最终门禁：PASS；open blocker=0、open major=0。未执行的 diag 专项脚本及长稳/功耗/IR 硬件项
  已明确列为基础设施缺失或后续资格验证，不冒充完成。

## 9. ISP Device-retained / Channel-rebuild 实验验证

### 9.1 实验边界

- Gate：`HDI_VI_EXPERIMENTAL_WARM_SWITCH=1`，仅影响当前进程。
- 默认无 Gate：planner capability 为 false，route=5 COLD。
- Gate 开启：route=6 QUIESCED；保留 SNR/VIF/ISP Device，销毁并重建 ISP Channel、IQ 和全部下游 graph。
- 失败边界：WARM 反向恢复旧 profile；失败再完整 COLD 恢复；两级恢复失败才标记 topology invalid。

### 9.2 失败假设与修正

第一版在 Sensor 已降到 1fps 后重建 Channel。API 约 0.346 秒，但 RAW-only 首帧约 8.48 秒，
both 在 5 秒内无新 RAW/IDR，判定失败。AE 仍按 1fps 递增，说明 Channel/3DNR 启动按物理帧逐帧
收敛，而非 API 卡住。

最终顺序在 30→1 时先以物理 30fps 重建新 Channel 和低 profile graph，启动 VIF 后等待 AE count=11，
再提交物理 1fps；generation drain 禁止预热帧进入 callback。1→30 复用 teardown boost，并把未绑定
LDC 初始化与旧低图排空并行。

### 9.3 板端结果

设备：172.16.16.43；程序：NFS `/mnt/prog_test`；测试前后 `prog_daemon`、`prog_pcr02` 均未运行。

| 用例 | 结果 | 最大 API switch | 最大 RAW first | 最大 MAIN IDR | 最大 SUB IDR | PTS rollback |
|---|---|---:|---:|---:|---:|---:|
| RAW-only 1 轮 | PASS | 2.168s | 2.558s | 0 | 0 | 0 |
| MAIN-only 2 轮 | PASS | 2.203s | 2.611s | 2.605s | 0 | 0 |
| SUB-only 2 轮 | PASS | 2.252s | 2.669s | 0 | 2.657s | 0 |
| MAIN+SUB 10 轮 | PASS | 2.281s | 2.686s | 2.671s | 2.671s | 0 |

both 10 轮共 20 次切换：

- 30→1 API 约 1.046～1.120 秒；
- 1→30 API 约 2.169～2.281 秒；
- 每轮 `isp_destroy_device_us=0`，Channel destroy 为约 3～6ms，Channel create/IQ/start 为约 9～14ms；
- 1fps 每轮 LDC=0、soft-light=0、VIF sleep=0、AE warmup count≥11；
- MAIN/SUB requested/active/recv/thread mask 与 demand 一致；
- 压测后内核日志未匹配 reset、timeout、CMDQ wait/error、recursive reset；
- 测试退出后 `prog_test`、`prog_daemon`、`prog_pcr02` 均未运行。

默认 COLD 回归 `/mnt/prog_test vi_fps_hil 1 100 both 10000`：PASS，route=5，30→1 为
2.194 秒、1→30 为 3.375 秒，证明实验 gate 未改变默认路径。

最终 `pthread_join` 失效保护后二进制 SHA-256 为
`f452fecba1647dccc3ac7929f0e8bb5cb2c54c69b6b506aba3590050394fcb32`，主机
`out/arm/app/prog_test` 与设备 `/mnt/prog_test` 一致。最终复跑结果：

- WARM both 2 轮：PASS，route=6，最大 API switch 2.227 秒，最大 RAW/MAIN/SUB 首帧或首 IDR
  为 2.632/2.622/2.623 秒，PTS rollback=0；
- 默认 COLD both 1 轮：PASS，route=5，最大 API switch 3.329 秒，最大 RAW/MAIN/SUB 首帧或首 IDR
  为 3.701/3.688/3.688 秒，PTS rollback=0；
- 复跑后 `dmesg` 未匹配 reset、timeout、CMDQ wait/error 或 recursive reset，且
  `prog_test`、`prog_daemon`、`prog_pcr02` 均未运行。

### 9.4 资格结论

当前证据授予“受控 opt-in 实验”资格，不授予“生产默认”资格。升级默认前至少仍需：

1. 24h soak 与更大切换轮次；
2. 温循和低照/高曝光边界；
3. Channel create/load-IQ、VIF bind/start、LDC prewarm 故障注入，验证两级回退；
4. 真实视频花屏/色彩/IQ 主观与自动图像质量检查；
5. 功耗仪比较 COLD 驻留与 WARM 切换瞬态。
