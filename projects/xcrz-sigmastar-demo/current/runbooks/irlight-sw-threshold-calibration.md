---
doc_type: runbook
knowledge_type: process
maturity: verified
created: 2026-05-12
last_updated: 2026-05-12
id: pcr02-irlight-sw-threshold-calibration
title: SW 光敏（软光敏）阈值标定流程
kind: project-current
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/current/runbooks/irlight-sw-threshold-calibration.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: retired-source-provenance
  source_id: pcr02-project-docs
  source_path: runbooks/irlight-sw-threshold-calibration.md
  source_sha256: 1f82c6a5b6307083376466d4e78805ecff7344462681cb17c33b55e70235acae
review_after: '2026-10-16'
review_status: delegated-review-closed-reference-boundary
promotion: none
promotion_decision: none; archived reference boundary, no owner decision generated
tags:
- pcr02
- current
- irlight
- sensor
- calibration
validation_refs:
- projects/xcrz-sigmastar-demo/current/runbooks/irlight-sw-threshold-calibration.md
- rtk bash tools/knowledge-check.sh --dry-run
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
evidence_refs:
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md
- artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.jsonl
created_at: '2026-06-16'
updated_at: '2026-07-19'
summary_zh: '> 适用于：modules/sensor/ir/irlight.h 中的 SW_D2N_IR_OFF/ON 和 SW_N2D_IR_OFF/ON 四个常量。该条目当前为 archived retired-source
  provenance，仅作历史项目材料检索入口，不代表当前项目事实、active 决策或 owner 签收。'
---

# SW 光敏（软光敏）阈值标定流程

> 适用于：`modules/sensor/ir/irlight.h` 中的 `SW_D2N_IR_OFF/ON` 和 `SW_N2D_IR_OFF/ON` 四个常量

---

## 背景

SW 软光敏使用摄像头 ISP 内部的 AE 亮度统计值（`u32LumY`）判断日夜，不依赖外部 ADC。由于 `u32LumY` 范围受 sensor 型号、IQ bin 配置、镜头透光率影响，默认估算值（600/800/1200/1500）需要在实际硬件上测量后替换。

**阈值语义：**

| 常量 | 含义 |
|------|------|
| `SW_D2N_IR_OFF` | IR 灯灭时：`LumY < 此值` → 触发日转夜（开灯） |
| `SW_N2D_IR_OFF` | IR 灯灭时：`LumY >= 此值` → 触发夜转日（关灯） |
| `SW_D2N_IR_ON`  | IR 灯亮时：`LumY < 此值` → 触发日转夜（维持夜间）|
| `SW_N2D_IR_ON`  | IR 灯亮时：`LumY >= 此值` → 触发夜转日（关灯） |

> 设计约束：`N2D > D2N`（迟滞防抖），`IR_ON > IR_OFF`（补光抬高 luma）

---

## 前置条件

1. 设备**连接充电器**（触发 `u8Status=1`，启用软光敏）
2. 开启 `hdi_vi.c` 的 DBG_INFO 输出，确认能看到 `LumY` 打印
3. 可调光源（建议色温 4000~5000K，照度范围 1~1000 Lux）
4. ISP AE 处于自动模式（`bIsStable=TRUE` 后再读值）

---

## 步骤 1：确定白天基准 LumY

**场景：** IR 灯关闭，正常白天室内照明

1. 光源调至 500~1000 Lux
2. 等待 AE 稳定（日志出现 `bIsStable=1`，约 3~5 秒）
3. 连续读取 5 次 `LumY`，记录均值 → **白天基准 LumY_day**

---

## 步骤 2：确定 `SW_D2N_IR_OFF`（IR 灯关时，日→夜触发阈值）

**场景：** IR 灯关闭，逐步降低光线

1. 从 500 Lux 开始，每步降低约 50%（500→250→100→50→20→5 Lux）
2. 每档调光后等待 AE 稳定，记录 `LumY`
3. 找到人眼刚感觉"应该开灯"时的 Lux 对应的 `LumY` → 记为 `LumY_threshold`
4. **`SW_D2N_IR_OFF = LumY_threshold × 0.9`**（留 10% 安全裕量，避免边界误触发）

---

## 步骤 3：确定 `SW_N2D_IR_OFF`（IR 灯关时，夜→日触发阈值）

**场景：** IR 灯关闭，从黑暗逐步恢复光线

1. 从步骤 2 的最低照度出发，逐步升高光线
2. 每档等 AE 稳定，记录 `LumY`
3. 找到人眼感觉"自然光够用，不需要开灯"时的 `LumY` → 记为 `LumY_n2d`
4. **`SW_N2D_IR_OFF = max(LumY_n2d, SW_D2N_IR_OFF × 1.3)`**
   （至少比 D2N 高 30%，确保迟滞区间）

---

## 步骤 4：确定 `SW_D2N_IR_ON`（IR 灯亮时，日→夜触发阈值）

**背景：** IR 灯开启后，红外光照到被摄物反射入镜头，使 `LumY` 人为抬高，需要更高的阈值才能正确判断环境变暗。

**场景：** IR 灯开启（手动设置夜间模式），调整光线

1. 手动设置设备为夜间模式（IR 灯常亮）
2. 从低照度（5 Lux）逐步增加光线
3. 每档等 AE 稳定，记录 `LumY`
4. 在 IR 灯亮的情况下，找到"环境已足够明亮可以关灯"时的 `LumY`
5. **`SW_D2N_IR_ON = LumY × 0.9`**

> 参考：通常 `SW_D2N_IR_ON ≈ SW_D2N_IR_OFF × 1.5~2.0`（补光增量因硬件而异）

---

## 步骤 5：确定 `SW_N2D_IR_ON`（IR 灯亮时，夜→日触发阈值）

**场景：** IR 灯开启，从黑暗逐步升高光线

1. 继续步骤 4 的场景，继续提高光线
2. 找到"即使有 IR 灯补光，自然光也明显足够"时的 `LumY`
3. **`SW_N2D_IR_ON = max(LumY, SW_D2N_IR_ON × 1.3)`**

---

## 标定结果填表

| 常量 | 含义 | 实测值 | 当前估算值 |
|------|------|:------:|:---------:|
| `SW_D2N_IR_OFF` | IR灯灭：日→夜阈值 | ___ | 600  |
| `SW_N2D_IR_OFF` | IR灯灭：夜→日阈值 | ___ | 800  |
| `SW_D2N_IR_ON`  | IR灯亮：日→夜阈值 | ___ | 1200 |
| `SW_N2D_IR_ON`  | IR灯亮：夜→日阈值 | ___ | 1500 |

**一致性验证：**
- `SW_N2D_IR_OFF > SW_D2N_IR_OFF` ✓（迟滞）
- `SW_N2D_IR_ON > SW_D2N_IR_ON` ✓（迟滞）
- `SW_D2N_IR_ON > SW_D2N_IR_OFF` ✓（补光抬高）
- `SW_N2D_IR_ON > SW_N2D_IR_OFF` ✓（补光抬高）

---

## 更新代码

将实测值填入 `modules/sensor/ir/irlight.h`：

```cpp
// SW 软光敏阈值：IR 灯亮时补光抬高 luma，需要用更高的阈值
static constexpr VS_U32 SW_D2N_IR_OFF = <实测值>;   // 无红外补光时日转夜阈值
static constexpr VS_U32 SW_N2D_IR_OFF = <实测值>;   // 无红外补光时夜转日阈值
static constexpr VS_U32 SW_D2N_IR_ON  = <实测值>;   // 红外补光开时日转夜阈值
static constexpr VS_U32 SW_N2D_IR_ON  = <实测值>;   // 红外补光开时夜转日阈值
```

---

## 验证

标定后，观察实际切换行为：

```bash
# 查看 LumY 和日夜切换日志（hdi_vi.c DBG_INFO 需开启）
grep "LumY\|D2N\|N2D\|setRelight\|ColorToGray" /tmp/app.log | tail -20
```

正常切换应表现为：
- 光线变暗 → 日志出现 `Check BV` → `DayNightStateCallback(VS_TRUE)` → `setRelight(true)`
- 光线变亮 → 日志出现 `Check AWB` → `DayNightStateCallback(VS_FALSE)` → `setRelight(false)`
- 切换后画面：夜间灰度、白天彩色
