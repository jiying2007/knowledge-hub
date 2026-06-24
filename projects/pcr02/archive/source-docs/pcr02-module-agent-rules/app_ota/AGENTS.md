# AGENTS.md

本文件约束 Codex 在 `app_ota` 独立仓库内工作。上层全局规则仍然适用；若冲突，优先遵循用户当前明确要求和更高层规则。

## 仓库定位

- 本目录是独立 Git 仓库，外层 SDK 仓库不是本仓的提交边界。
- 默认只修改 `app_ota/` 内文件，不触碰外层 SDK 的无关变更。
- 构建目标为 `prog_ota`，但构建依赖外层 SDK 的 `BUILD_TOP` 和 `build/app_light_common.mk`。

## 工作原则

- 所有 shell 命令必须通过 `rtk` 执行。
- 修改源码、脚本、配置和 Markdown 时必须使用 `apply_patch`。
- 先读 `README.md`、`docs/TECHNICAL_DESIGN.md`、`docs/OTA_OPERATION_GUIDE.md` 和相关源码，再做行为性修改。
- 不批量删除或覆盖历史编译产物、`.o`、`.d`、PDF、zip/tgz 和备份文件，除非用户明确要求。
- 发现未跟踪文件或已有改动时，默认视为用户成果，不回退、不清理。

## 常用上下文

- 仓库入口：`README.md`
- 技术设计：`docs/TECHNICAL_DESIGN.md`
- 运行指南：`docs/OTA_OPERATION_GUIDE.md`
- 开发计划：`docs/DEVELOPMENT_PLAN.md`
- Codex skill：`.codex/skills/app-ota/SKILL.md`
- skill 参考图谱：`.codex/skills/app-ota/references/repo-map.md`

## 团队协作开发

- 默认按模块 ownership 协作，不新增独立协作文档。
- `app_ota.c`、`ota_start.sh`、`ota_upgrade.sh`、`ota_end.sh`、`app_ota.mk` 是共享契约，默认禁止多方并行写入。
- 修改 `ota_status`、`ota_phase`、脚本环境变量、包格式或版本策略时，必须同步更新 `docs/` 下的文档和 skill repo map。
- 确需并行时，先写清每个任务的 `scope_write`、`scope_read`、`must_not_touch`、验证命令和停止条件。
- 子任务完成后必须由主线程或集成 owner 统一查冲突、跑最终验证并更新 `docs/DEVELOPMENT_PLAN.md`。

## 验证规则

文档或 Codex 资产修改后至少运行：

```bash
rtk git diff --check
rtk rg --hidden -n "[ \t]+$" -g "*.md" -g "*.yaml"
rtk rg --hidden -n "^(<<<<<<<|=======|>>>>>>>)$" -g "*.md" -g "*.yaml"
rtk python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .codex/skills/app-ota
```

脚本改动后至少运行：

```bash
rtk sh -n ota_start.sh ota_upgrade.sh ota_end.sh
```

代码改动后按风险补充：

- 外层 SDK app 构建或明确设置 `BUILD_TOP` 后的定向构建。
- 板端 OTA 冒烟和失败恢复验证。
- 对状态/phase 改动，检查 `docs/TECHNICAL_DESIGN.md` 和 `docs/OTA_OPERATION_GUIDE.md` 是否同步。

## 提交边界

- 如果用户要求提交，先在本仓执行检查，再提交本仓变更。
- 不自动提交外层 SDK gitlink 或外层仓库改动，除非用户明确要求。
- commit summary 使用中文动词开头，格式遵循全局规则。
- 团队协作提交前必须确认相关文档、agent 和 skill 与实际改动同步，并补齐构建或板端验证证据。
