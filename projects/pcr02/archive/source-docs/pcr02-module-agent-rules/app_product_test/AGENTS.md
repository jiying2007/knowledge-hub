# AGENTS.md

本文件约束 Codex 在 `app_product_test` 独立仓库内工作。上层全局规则仍然适用；若冲突，优先遵循用户当前明确要求和更高层规则。

## 仓库定位

- 本目录是独立 Git 仓库，外层 SDK 仓库不是本仓的提交边界。
- 默认只修改 `app_product_test/` 内文件，不触碰外层 SDK 的无关变更。
- 构建目标为 `prog_product_test`，但构建依赖外层 SDK 的 `BUILD_TOP` 和 build mk。

## 工作原则

- 所有 shell 命令必须通过 `rtk` 执行。
- 修改源码、脚本、配置和 Markdown 时必须使用 `apply_patch`。
- 先读 `README.md`、`docs/TECHNICAL_DESIGN.md`、`docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` 和相关源码，再做行为性修改。
- 不批量删除或覆盖历史编译产物、`.o`、`.d`、PDF、zip/tgz 和备份文件，除非用户明确要求。
- 发现未跟踪文件或已有改动时，默认视为用户成果，不回退、不清理。
- 文档必须区分“当前主线已实现”和“补丁/计划待合入”。当前蓝牙能力只存在于 `pt_bt.patch` 与 `pt_hw_bt.backup`，不得写成主线已支持。

## 常用上下文

- 配置模板：`product_test.ini`
- 配置说明：`docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md`
- 设计说明：`docs/TECHNICAL_DESIGN.md`
- 计划与待验证：`docs/DEVELOPMENT_PLAN.md`
- Codex skill：`.codex/skills/app-product-test/SKILL.md`
- skill 参考图谱：`.codex/skills/app-product-test/references/repo-map.md`

## 团队协作开发

- 默认按模块 ownership 协作，不新增独立协作文档。
- PCBA/半成品改动优先由 `pt_common.c`、`product_test.ini` 和 `docs/PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` 的 owner 串行处理。
- AGING 改动优先由 `pt_hw_aging.c`、`pt_hw_record.c`、`pt_common.c` 和 `docs/TECHNICAL_DESIGN.md` 的 owner 串行处理。
- CALIBRATION 改动优先由 `pt_calibration_*`、`pt_common.c` 和标定相关配置文档的 owner 串行处理。
- `pt_common.c`、`product_test.ini`、`app_product_test.mk`、`.codex/skills/app-product-test/SKILL.md` 是共享契约，默认禁止多方并行写入。
- 确需并行时，先写清每个任务的 `scope_write`、`scope_read`、`must_not_touch`、验证命令和停止条件。
- 子任务完成后必须由主线程或集成 owner 统一查冲突、跑最终验证并更新 `docs/DEVELOPMENT_PLAN.md`。

## 验证规则

文档或 Codex 资产修改后至少运行：

```bash
rtk git diff --check
rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-product-test
```

代码改动后按风险补充：

- 外层 SDK app 构建或明确设置 `BUILD_TOP` 后的定向构建。
- 板端验证 AGING、CALIBRATION、MIC 或 diag 行为。
- 对 `product_test.ini` 改动，检查 `PROFILE_<Stage>_<Station>` 与源码 feature mask 是否一致。

## 提交边界

- 如果用户要求提交，先在本仓执行检查，再提交本仓变更。
- 不自动提交外层 SDK gitlink 或外层仓库改动，除非用户明确要求。
- commit summary 使用中文动词开头，格式遵循全局规则。
- 团队协作提交前必须确认相关文档、agent 和 skill 与实际改动同步，并补齐构建或板端验证证据。
