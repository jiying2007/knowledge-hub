---
title: SigmaStar SDK 升级 Playbook
doc_type: runbook
knowledge_type: process
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [sigmastar, sdk, upgrade, abi, regression]
related: [../architecture/sigmastar-platform-internal-overview.md, ../architecture/sigmastar-platform-capability-matrix.md, sigmastar-platform-development-workflow.md, embedded-build-reproducibility-guide.md]
validation_refs: [../standards/embedded-artifact-provenance-standard.md]
---

# 背景

SDK 升级通常同时影响工具链、头文件、动态库、内核模块、rootfs、示例代码和平台默认配置。本文用于把升级过程拆成可回滚、可验证的步骤，避免只替换库文件后出现 ABI 不匹配或运行期随机崩溃。

# 前置条件

1. 保存旧 SDK 版本、commit、构建参数和发布 manifest。
2. 明确升级目标：bugfix、平台支持、性能优化或安全修复。
3. 准备可回滚分支或独立 worktree。
4. 准备最小回归样机和基础 smoke 用例。
5. 禁止把原始 SDK 压缩包直接提交到 Git。

# 升级步骤

## 1. 建立基线

记录旧版本信息：

```bash
rtk bash scripts/generate-release-manifest.sh --root out/arm/app --out /tmp/before-sdk-upgrade-manifest.csv
rtk bash tools/debug/audit-binary-deps.sh --bin out/arm/app/prog_pcr02.debug.full --sysroot out/arm/target --out /tmp/before-sdk-upgrade-deps.txt --allow-missing
```

## 2. 分层替换

按顺序替换并验证：

1. 工具链与构建配置。
2. SDK headers。
3. SDK libraries。
4. kernel modules 与 firmware。
5. rootfs 运行依赖。
6. 示例配置、模型、脚本和 profile。

每层替换后都执行一次最小构建或静态检查，避免把多个风险混在一起。

## 3. ABI 与依赖检查

检查二进制依赖：

```bash
rtk bash tools/debug/audit-binary-deps.sh --bin out/arm/app/prog_pcr02.debug.full --sysroot out/arm/target --out /tmp/after-sdk-upgrade-deps.txt
```

重点关注：

1. `NEEDED` 动态库是否存在。
2. 目标架构是否一致。
3. 旧库是否被错误搜索路径命中。
4. `debug.full` 与 strip 后二进制是否来自同一构建。

## 4. Smoke 验证

至少覆盖：

1. 启动与退出。
2. Sensor 到编码或显示链路。
3. AI 推理链路。
4. 音频输入输出链路。
5. 长跑 30 分钟资源趋势。
6. 异常退出后是否产生 core 和可符号化栈。

# 回滚方案

1. 回退 SDK 替换 commit 或 worktree。
2. 恢复旧 manifest 中记录的运行产物。
3. 若设备已烧录新 rootfs，必须同步恢复 kernel module 与 rootfs 动态库。
4. 保留失败日志、manifest、依赖报告，用于后续二次升级。

# 验证记录

升级结论必须附：

1. 新旧 SDK 标识。
2. 构建命令和关键环境变量。
3. `generate-release-manifest.sh` 输出。
4. `audit-binary-deps.sh` 输出。
5. smoke 用例结果和失败项。
