# app_product_test 仓库图谱

## 文档

| 文件 | 用途 |
| --- | --- |
| `README.md` | 仓库入口、边界、模块图谱和验证入口 |
| `AGENTS.md` | 本独立仓库内的 Codex 工作规则 |
| `docs/TECHNICAL_DESIGN.md` | 运行架构与行为设计 |
| `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` | 产线配置规则 |
| `docs/DEVELOPMENT_PLAN.md` | 当前状态、验证待办和后续计划 |

## 核心源码

| 领域 | 文件 |
| --- | --- |
| 进程入口 | `pt_main.c` |
| 配置/阶段/profile/消息生命周期 | `pt_common.c`, `pt_common.h` |
| AGING 计时与状态 | `pt_hw_aging.c` |
| 录像 | `pt_hw_record.c` |
| LCD | `pt_hw_lcd.c`, `pt_font_*.h`, `pt_ss_font_info.h` |
| IR / IR-cut / IR recv / IR distance | `pt_hw_ir.c`, `pt_hw_ircut.c`, `pt_hw_irrecv.c`, `pt_hw_irdistance.c` |
| 电机 | `pt_hw_motor.c` |
| MIC / 喇叭 | `pt_hw_mic.c`, `pt_hw_spk.c` |
| 电池 / ADC / 激光 / TOF / IMU | `pt_hw_battery.c`, `pt_hw_adc.c`, `pt_hw_laser.c`, `pt_hw_tof.c`, `pt_hw_imu.c` |
| 工厂键/复位/关机 | `pt_hw_factory.c`, `pt_hw_shutdown.c` |
| 标定 | `pt_calibration.h`, `pt_calibration_mgr.c`, `pt_calibration_async.*`, `pt_calibration_tof.c`, `pt_calibration_imu.cpp`, `pt_calibration_camera.cpp` |
| Diag perf | `pt_diag_bridge.c`, `pt_diag_bridge.h` |

## 配置事实

- 运行配置路径：`/var/run/media/mmcblk0p1/vstrong/product_test.ini`
- 老化状态路径：`/var/run/media/mmcblk0p1/vstrong/aging_state.ini`
- Profile 查找规则：`PROFILE_<Stage>_<Station>`
- 支持阶段：`PCBA`、`SEMI_FINISHED`、`AGING`、`CALIBRATION`、`ACOUSTIC`
- 代码接受 `CALIBRATE` 作为标定别名，但产线文档应优先使用 `CALIBRATION`。
- 协作规则沉淀在 `README.md`、`AGENTS.md`、`docs/DEVELOPMENT_PLAN.md` 和本 skill；除非用户明确要求，不新增独立协作文档。
- 共享契约：`pt_common.c`、`product_test.ini`、`app_product_test.mk`、`.codex/skills/app-product-test/SKILL.md`。
- 临时参考目录不进入正式文档、agent 或 skill 索引。

## 验证命令

```bash
rtk git status --short --branch
rtk git diff --check
rtk rg --hidden -n "[ \t]+$" -g "*.md" -g "*.yaml"
rtk rg --hidden -n "^(<<<<<<<|=======|>>>>>>>)$" -g "*.md" -g "*.yaml"
rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-product-test
```

涉及代码变更时，优先使用外层 SDK 构建路径；若单独调用 `app_product_test.mk`，必须正确设置 `BUILD_TOP`。

## 待确认事项

蓝牙扫描在当前仓库状态中仍是草案：

- `pt_bt.patch`
- `pt_hw_bt.backup`

在补丁合入 `pt_common.c`、`pt_common.h`、`product_test.ini` 并形成真实 `pt_hw_bt.c` 构建路径前，不要把 `EnableBt` 写成主线可用 profile 开关。
