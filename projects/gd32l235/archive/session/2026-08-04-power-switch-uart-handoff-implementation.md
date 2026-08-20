---
id: gd32l235-power-switch-uart-handoff-implementation-20260804
title: GD32L235 与 PCR02 拨动开关 UART 快速交接实现归档
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/session/2026-08-04-power-switch-uart-handoff-implementation.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: source-project-session-summary
  from: workspace://gd32l235 + workspace://xcrz_sigmastar_demo implementation and verification
  source_sha256: 913e549d65e3415b1317800e16fe3ad08e0738df055c6a519b52ddb4ff3a2435
  temporary_source_retained: false
review_after: '2026-10-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- pcr02
- uart-handoff
- power-switch
validation_refs:
- projects/gd32l235/archive/session/2026-08-04-power-switch-uart-handoff-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/archive/session/2026-08-04-power-switch-uart-handoff-implementation.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-04'
updated_at: '2026-08-04'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-04'
manual_validation_pending: true
summary_zh: 沉淀拨动开关反复切换时 MCU 与 daemon 的 UART 同代快速交接、硬回退边界和验证证据。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 电源充电状态收敛与 PCR02 UART 交接实现归档

## 背景与范围

- Captured at: 2026-08-04（Asia/Hong_Kong）
- Source: GD32L235 分支 `dev/power-charge-state-convergence`、SigmaStar PCR02 当前实现、协议文档、契约测试和构建验证。
- Scope: 普通固件充电温度会话保护、仅 DEEP_SLEEP 的充电恢复，以及拨动开关关机过程中再次打开时由 daemon 短时接管 UART、按 MCU 最新物理目标快速恢复应用；不修改 PA8 长按 8010 ms 的硬性时序。
- Sanitization: 仅保留协议、状态机、验证命令和风险摘要；不包含原始会话、完整日志、二进制、凭据或运行时数据。

## 最终契约

复用 MCU/SOC UART 命令 `0x09` 的固定 3 字节载荷，新增两个关机阶段：

- `TARGET_STATE(0x06) = {stage, target, generation}`：MCU 在收到应用安全退出确认后发送最新物理目标，`target` 为 OFF 或 ON，`generation` 标识本轮拨动事务。
- `APP_EXITED(0x07) = {stage, flags, generation}`：daemon 在确认业务进程退出并接管 UART 后，同代回应已退出；flags bit0 表示快速重启已开始或已提交。

同代校验和有限状态接收是硬约束。MCU 只在“等待应用退出”“关机保持”或“等待 APP_READY”三个状态接受 `APP_EXITED`，避免旧确认跨代生效。

## 充电与休眠状态收敛

- 普通 profile 的充电温度阈值为低温 `-3°C` 切断/`0°C` 恢复，高温 `49°C` 切断/`46°C` 恢复；认证 profile 仍独立使用 `43°C/40°C`。
- 高低温保护只在检测到充电后建立会话锁存。未充电期间曾达到 `49°C` 不会污染下一次上桩；例如降到 `47°C` 后上桩，只要当前样本有效且新鲜，可以直接充电。
- 上桩时温度样本无效或超过 10 秒未更新时禁止充电；获得首个新鲜样本后按当前实际温度重新评估，不继承离桩期间的历史锁存。
- 只有 `DEEP_SLEEP` 智能留电状态支持充电恢复：充电电流至少 50 mA、连续 3 个有效样本且相邻样本不超过 3 秒后触发一次唤醒。
- `SLEEP` 是用户休眠，不参与充电恢复；只允许 WiFi 或 SOC RTC 唤醒。

## SOC 侧交接顺序

1. `prog_pcr02` 完成业务安全退出，发送既有 `SOC_CONFIRMED`，关闭 UART，并以专用退出码 64 退出。
2. daemon 的 `waitpid` 识别退出码，等待 200 ms，再检查当前仍是 APP 模式、业务/产测进程均不存在且 OTA flock `/tmp/prog_ota.lock` 未被占用。
3. 满足条件时，daemon 最小化打开 `/dev/ttyS1`，只解析 `TARGET_STATE`，不初始化 diag 或业务资源。
4. 目标为 OFF 时回应同代 `APP_EXITED` 后保持业务停止；目标为 ON 时先回应，再关闭 UART，随后启动 `prog_pcr02`。
5. daemon 只保留 5 秒短时交接窗口；超时、模式变化、OTA 占锁或协议异常均释放 UART，交给原有 MCU 硬回退。

`prog_ota` 保持原有“先持有 OTA lock，再停止父进程；父进程退出后才打开 UART”的顺序。因此方案不需要 UART owner 或 Unix Socket，也不允许 daemon 与业务进程同时持有 UART。

## MCU 收敛和回退

- 拨到 OFF 后先保留 300 ms 可取消窗口；窗口内恢复 ON 不启动应用退出。
- 拨动关机收到 `SOC_CONFIRMED` 后，进入等待 `APP_EXITED`，每 100 ms重发当前 `TARGET_STATE`。
- 原 2 秒应用反初始化等待已明确收窄并重命名为 `SOC_CONFIRMED_SLEEP_DEINIT_WAIT_MS` / `SOC_EXIT_WAIT_SLEEP_DEINIT`，只服务 `CHARGE_SLEEP`；拨动开关路径不经过该状态。
- 稳定 OFF：收到同代确认后进入关机保持，按既有逻辑控制 PA15。
- 退出过程中再次拨到 ON：MCU 发送同代最新 ON；daemon 启动应用后，MCU 复用既有 `BOOT_WAIT_READY` 等待新应用上报 `APP_READY`，不触发非必要的 PA8 8 秒脉冲。
- daemon/应用未升级、接管失败或确认丢失：仍在原有总计 5 秒截止点进入 PA8 硬回退。
- 快速启动后 60 秒未收到 `APP_READY`：最多执行一次 PA8 硬恢复，避免重复启动循环。
- PA8 长按 `8010 ms` 为硬件要求，未修改；长脉冲结束后保持 1000 ms 释放间隔，再发送 9 ms 正常唤醒脉冲。

## 兼容性和非目标

- 这是可回退的协议扩展，不移除旧阶段。任一侧未升级时，快速路径失效但原有 5 秒/60 秒/PA8 恢复路径仍在。
- daemon 不接管业务消息、不转发 diag、不引入 UART owner、不改变 OTA 脚本契约。
- `prog_ota` 仍通过 OTA lock 优先占用 UART；daemon 检测占锁后不接管，MCU 侧改动不改变 OTA payload 命令序列。
- PA8 8010 ms 硬时序保持不变；普通温度保护和 DEEP_SLEEP/SLEEP 语义按本归档的新契约收敛。

## 验证证据

- `rtk bash scripts/codex-check.sh --full`：通过；Stage0 2280 B、Stage1 12936 B、App 47088/51200 B，剩余 4112 B；普通 profile 的 build、package、check 全部通过。
- 普通包 manifest：OTA payload 为 `gd32l235_app.bin`，大小 47088 B，验证状态 `passed=true`；整包 SHA256 为 `457db4045965741aef9759fbaffaa980a7d84536bdfdcaa112fb2356e4ac6206`。
- `--debug-uart-printf --wakeup-diag` 独立调试构建通过，App 50588/51200 B；调试 profile 不作为 OTA 包。
- `rtk make daemon_app_all -j20`：通过。
- `rtk make pcr02_app_all -j20`：通过。
- `rtk make modules/app_obj_all -j20`：通过。
- `rtk python3 daemon/check_uart_handoff_contract.py`：通过。
- `rtk bash build/check_public_headers.sh app`：通过。
- 三个相关仓库的目标文件 `git diff --check`：通过。
- daemon 禁止依赖扫描无命中：生产代码未引入 diag、`VSAPPDIAG` 或 `CMD_SYS_DYNAMIC_CMD`。
- GD32L235 已提交并推送：`9aafa976a8905b6377b28826a018dab120e9ca20`（`fix(power): 收敛关机重启与诊断流程`），远端 `origin/dev/power-charge-state-convergence` 与本地完整哈希一致。
- 相对 `origin/master@06f375a03d0133362dc366593f5a6da72647432e` 落后 0、领先 2，`origin/master` 是该分支直接祖先，可 fast-forward 合并且无内容冲突；未实际合并 master。

## 复审与风险

- 复审发现并修复：稳定 OFF 期间若 PA8 硬脉冲已开始，宽泛的目标解析可能直接改状态但不拉低 PA8，并可能复用旧快速确认。最终实现删除宽泛解析器，仅在允许状态接受同代确认。
- 当前没有覆盖最终状态机的完整板级/HIL 证据。仍需实机验证反复 OFF/ON、OFF 保持、OTA 占锁、daemon/应用异常、60 秒 APP_READY 超时、温度会话门禁和 DEEP_SLEEP 充电恢复，并联合检查 UART 日志、PA8、PA15 与 PB10 波形。
- 普通 App 仅比 4096 B 门禁多 16 B，后续功能增加前必须复查 Flash 预算。
- 回退：撤销新增的 `TARGET_STATE/APP_EXITED` 快速交接代码即可恢复原流程；现场异常时原有 5 秒、60 秒和 PA8 8010 ms 兜底仍有效。

## 后续板级矩阵

1. 关机后应用退出期间拨 ON：不出现非必要 PA8 长脉冲，daemon 完成 acquire/release，新应用上报 APP_READY。
2. 持续 OFF：SOC_CONFIRMED 与 APP_EXITED 后，PA15 按既有关机逻辑收敛。
3. 快速反复 OFF/ON：只接受当前 generation，不被旧 APP_EXITED 影响。
4. OTA lock 已持有：daemon 不接管 UART、不重启业务。
5. daemon 异常或 APP_READY 缺失：分别命中 5 秒或 60 秒后既有 PA8 硬回退，且 APP_READY 超时恢复最多一次。
6. 温度会话：离桩达到 49°C 后降到 47°C 上桩可充；充电中达到 49°C 后须降到 46°C 才恢复；无效或超过 10 秒的样本禁止充电。
7. 休眠恢复：DEEP_SLEEP 满足 50 mA/3 样本条件后唤醒，SLEEP 在相同充电条件下保持休眠。

## 治理状态

- Archive candidate: reviewing
- Memory candidate: no；未经 owner 复核，不提升为规则或 memory。
- Provenance: GD32L235 提交 `99cb29809b3a4e7372a05b6e185b85537041694e`、`9aafa976a8905b6377b28826a018dab120e9ca20`，SigmaStar PCR02 当前实现及 2026-08-04 验证结果；不作为未来分支状态的永久证明。
