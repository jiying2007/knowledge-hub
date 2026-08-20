---
aliases:
- GD32L235 高温回桩热态充电治理策略
related:
- projects/gd32l235/decisions/charge-temperature-soft-hard-protection.md
- projects/gd32l235/decisions/charge-temperature-configurable-soft-hard-protection.md
- projects/gd32l235/README.md
supersedes_candidates:
- gd32l235-charge-temperature-soft-hard-protection-20260812
- gd32l235-charge-temperature-configurable-soft-hard-protection-20260812
id: gd32l235-charge-temperature-thermal-governor-20260818
title: GD32L235 高温回桩热态充电治理策略决策候选
kind: decision
domain: projects/gd32l235
path: projects/gd32l235/decisions/charge-temperature-thermal-governor-20260818.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: design-review-and-working-tree-inspection
  from: GD32L235 charge-temperature design review and working-tree inspection, 2026-08-18
  source_sha256: b1ff320e9008ca27bb58074b138ce3df6524bbe5b4f7d787bf45be18c045d6e2
review_after: '2026-09-18'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- charge
- temperature-protection
- thermal-governor
- hil-pending
validation_refs:
- projects/gd32l235/decisions/charge-temperature-thermal-governor-20260818.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/decisions/charge-temperature-thermal-governor-20260818.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-18'
updated_at: '2026-08-18'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-18'
manual_validation_pending: true
summary_zh: 49℃以上允许受控慢充仅限于确认降温的热态窗口；预停充线由热惯性和测温误差标定，52℃为独立硬锁，PRE_STOP/HARD_LOCK 均需降至46℃稳定后才进入受控慢充恢复。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# GD32L235 高温回桩热态充电治理策略决策候选

## 决策

机器人在寻宠、逗宠或回充后带着较高电池温度上桩时，允许在受控条件下补电，但不把 52℃当作常规充电许可线。采用以下热态治理状态机：

1. `HARD_LOCK`：任一新鲜的原始温度达到硬上限 `T_hard`（候选 52℃）时，立即关闭 PB10、记录事件并锁定热态充电。仅当温度不高于 46℃连续 60 秒、温度数据新鲜且趋势不升时，才进入 `RECOVERY_SLOW`。
2. `PRE_STOP`：温度达到预停充线 `T_pre_stop`，或热态慢充期间温度不再下降时，立即关闭 PB10。恢复条件与 `HARD_LOCK` 相同：不高于 46℃连续 60 秒、数据新鲜且趋势不升。
3. `HOT_SLOW`：仅在 49℃至 `T_pre_stop` 之间、温度趋势经确认下降、热态预算未耗尽时，允许 1.25A 慢充；快充禁止。任一趋势转为上升或持平、温度达到 `T_pre_stop`、温度失效或预算耗尽，立即进入 `PRE_STOP`。
4. `RECOVERY_SLOW`：从 `PRE_STOP` 或 `HARD_LOCK` 恢复后，仅允许 1.25A 慢充并观察 2 至 5 分钟。期间温度上升或持平即回到 `PRE_STOP`。仅当温度满足独立的常规快充资格线并稳定后，才允许 2A 快充。

46℃是热保护的恢复资格线，而不是完全解除限制的常规充电线。现有的 45℃慢充进入、38℃快充恢复分层可作为常规档位策略的基础，但不得绕过热态状态机。

## 参数和安全约束

- 49℃为推荐安全线，超过后只允许 `HOT_SLOW`，不得快充。
- `T_hard` 的候选值 52℃必须由电芯/电池包供应商书面确认；若 49℃是绝对规格上限，本策略不得启用热态慢充。
- `T_pre_stop` 不固定为 51℃，必须经热测试满足：`T_pre_stop + 停充后最大余温 + 测温最大正误差 < T_hard`。在缺少数据时，不得以 51℃作为已验证安全值。
- 52℃硬停和温度失效/超过 10 秒未更新必须使用原始新鲜样本立即生效，不经趋势滤波。
- 趋势仅用于授权 `HOT_SLOW`，不能用于延迟硬停。控制实现必须保留至少 0.5℃分辨率的原始温度并使用 30 至 60 秒窗口；现有整度温度值不满足这一条件。
- 热态预算为附加约束而非安全屏障。仅在 PB10 已开启且实际充电电流得到确认时累计；不得因桩检测抖动、短暂温度波动或重启无条件重置。
- 温度无效时保留电量计供电恢复窗口，以解决电池过放后“电量计无供电、无温度样本、温度门禁禁充”的启动死锁：仅在 PA7 已检测到上桩、PA11 与上层门禁均允许、电量计尚未就绪且本运行期未进入 `PRE_STOP`/`HARD_LOCK` 时，以慢充档开启最多 30 秒、关闭 30 秒后重试，单次上桩最多 3 个窗口；首个有效温度样本到达后立即退出并重裁正常温度保护。该有界例外在跨复位且温度未知时仍存在残余热风险，应由电池包/BMS 的独立硬件过温保护兜底。
- 禁止复用现有充电脉冲通知逻辑做高频热管理占空比控制，除非充电器、电量计和电池包方确认这种开关方式安全且兼容。

## 实现边界

- 温度源应确认是可代表电芯最热点的 TS/NTC；单一温度源不足时，由硬件/BMS 提供独立硬件级过温保护。
- 充电电流档位当前仅有 1.25A 与 2A；若 1.25A 在热态仍使温度上升，策略只能停充，不能假设慢充安全。
- `HARD_LOCK`、`PRE_STOP`、`HOT_SLOW`、`RECOVERY_SLOW` 以及预算、趋势窗口和恢复计时必须显式诊断上报，供热测试和现场追溯。
- 任何协议配置都不得提高 `T_hard` 或绕过状态机；参数变更需要范围校验和版本化记录。

## 验收门槛

软件实现前必须先完成或确认：

1. 电芯/电池包方确认 49℃以上短时低电流充电的许可边界，或确认不能允许；
2. 传感器位置、精度、分辨率、采样周期及与电芯真实温度的偏差；
3. 在不同环境温度、SOC、老化状态和 1.25A/2A 电流下，测得停充后的最大余温，用于推导 `T_pre_stop`；
4. 验证复位、温度读取失败、桩检测抖动和充电器异常时的 PB10 行为；电量计供电恢复窗口必须能解除过放启动死锁，且在同一运行期 `PRE_STOP`/`HARD_LOCK` 后不可绕过热保护；
5. 热箱与实机回桩场景验证：49℃以上下降曲线可受控补电，温度上升时立即停充，52℃硬停可靠，46℃稳定恢复后不会振荡；
6. 软件行为模型、构建、打包和固件检查通过后，再进行硬件在环验收。

## 当前证据与未决风险

已核对当前代码具备 49/50/51℃分段确认、52℃硬停、46℃稳定恢复、温度失效门禁及 1.25A/2A 电流切换；相关静态行为测试与电量计恢复契约测试于 2026-08-18 通过。该证据不覆盖本决策新增的趋势、余温、预算、精度或跨复位约束。

当前温度读取路径将温度整度化，且温度失效时存在有界的电量计供电恢复窗口。因此本决策仍为 `reviewing`，不得据此宣称热安全已经验证、固件已经完成或可以发布。

## 来源与边界

- captured_at：2026-08-18（Asia/Hong_Kong）
- last_verified：2026-08-18
- source：高温回桩充电策略评审、GD32L235 工作树静态检查和相关本地测试
- 排除：原始聊天记录、完整日志、设备标识、二进制制品、凭据和私有端点
- supersedes 候选：2026-08-12 两份充电温度软硬保护候选；旧条目保持 `reviewing`，须由 owner 决定是否正式 superseded
