---
name: app-product-test
description: 维护 SigmaStar SSC305 app_product_test 产测固件仓库。适用于更新或审查 app_product_test 文档、product_test.ini 阶段/profile 规则、PCBA/半成品协作边界、AGING/CALIBRATION 行为、MIC 阈值、diag perf 桥接、项目 AGENTS 和验证规则。
---

# app_product_test 技能

## 快速开始

处理任务前先读：

1. `README.md`
2. `AGENTS.md`
3. `docs/` 下的任务相关文档或对应源码

需要快速定位模块、文档和验证命令时，读取 `references/repo-map.md`。

## 任务路由

- 修改 `product_test.ini`、stage、station、operator、profile 或阈值时，检查 `product_test.ini`、`docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`、`pt_common.c` 和 `pt_common.h`。
- 修改 PCBA 或半成品行为时，检查 `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`、`docs/TECHNICAL_DESIGN.md`、`product_test.ini` 和 `pt_common.c` 中的绑定/profile/组件控制逻辑。
- 修改 AGING 行为时，检查 `pt_hw_aging.c`、`pt_hw_record.c`、`pt_hw_ircut.c`、`pt_hw_motor.c`、`pt_hw_lcd.c`、`pt_common.c` 和 `docs/TECHNICAL_DESIGN.md`。
- 修改 CALIBRATION 行为时，检查 `pt_calibration.h`、`pt_calibration_mgr.c`、`pt_calibration_tof.c`、`pt_calibration_imu.cpp`、`pt_calibration_camera.cpp` 和 `pt_common.c`。
- 修改 MIC 行为时，检查 `pt_hw_mic.c`、`product_test.ini` 的 `[THRESHOLD]` 和 `docs/TECHNICAL_DESIGN.md` 中的 MIC 说明。
- 修改 diag perf 行为时，检查 `pt_diag_bridge.c` 和 `pt_common.c` 中的 `bridge/diag/perf/*` handler。
- 准备团队协作改动时，检查 `README.md`、`AGENTS.md`、`docs/DEVELOPMENT_PLAN.md`、模块 ownership 和验证状态。
- 修改 Codex agent 或 skill 时，同步更新 `AGENTS.md`、本 `SKILL.md`、`agents/openai.yaml` 和 `references/repo-map.md`。

## 仓库规则

- 把本目录视为独立 Git 仓库。
- 所有 shell 命令使用 `rtk`。
- 手工修改文件使用 `apply_patch`。
- 除非用户明确要求，不删除或覆盖对象文件、依赖文件、PDF、压缩包、备份文件或补丁文件。
- 文档必须贴合当前主线代码；若能力只存在于 `pt_bt.patch` 或 `pt_hw_bt.backup`，只能写成待合入或草案。
- 保持外层 SDK 构建边界：`app_product_test.mk` 依赖 `BUILD_TOP` 和外层 build mk 文件。
- 不新增独立协作文档；协作规则沉淀在 `README.md`、`AGENTS.md`、`docs/DEVELOPMENT_PLAN.md` 和本 skill。
- 临时参考目录不进入项目文档、agent 或 skill 的正式索引。
- `pt_common.c`、`product_test.ini`、`app_product_test.mk` 和本 skill 属于共享契约，默认串行修改，除非明确声明 scope ownership。

## 验证

仅修改 Markdown、AGENTS 或 skill 时运行：

```bash
rtk git diff --check
rtk rg --hidden -n "[ \t]+$" -g "*.md" -g "*.yaml"
rtk rg --hidden -n "^(<<<<<<<|=======|>>>>>>>)$" -g "*.md" -g "*.yaml"
rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-product-test
```

修改代码或 `product_test.ini` 行为时，补充最小必要的构建或板端验证。若本地因缺少 `BUILD_TOP` 或外层 SDK build 文件无法构建，必须说明该边界，不能声称构建通过。

## 高风险行为

- AGING 验收依赖连续运行、TF 存储健康、零失败位和复位门禁；本地静态检查不足以签收。
- CALIBRATION 完成后可能按 `PT_CALIBRATION_COMPLETE_AUTO_FORMAT_REBOOT` 格式化 TF 卡并重启。
- MIC 的 `header.sequence` 携带诊断细分状态，`mic_valid` 仍是布尔结果。
- 蓝牙当前不是主线可用能力，除非草案补丁已合入并完成验证。
- 模块 owner、最终整合验证或板端/构建证据未闭环时，不应声明协作开发可提交。
