---
name: embedded-build-release-check
description: 执行嵌入式构建可复现与发布前检查，覆盖源码状态、工具链、二进制依赖、release manifest、产物 hash 和 smoke 验证证据。
version: 1.0.0
last_updated: 2026-05-18
---

# Embedded Build Release Check

## 1. 触发条件

- 用户准备发布固件、应用、模型、rootfs 或调试符号。
- 用户要求检查构建可复现、release manifest、产物 hash 或发布前风险。

## 2. 处理范围

- 处理发布包完整性、二进制依赖、manifest 校验和构建证据。
- 不替代人工 smoke 测试；无法运行设备测试时必须降级说明。

## 3. 工作流

1. 读取 `docs/runbooks/embedded-build-reproducibility-guide.md`。
2. 读取 `docs/standards/embedded-artifact-provenance-standard.md`。
3. 检查源码状态：`git status --short --branch` 与 commit。
4. 生成并校验 manifest：`rtk bash scripts/generate-release-manifest.sh --root <dir> --out <dir>/release-manifest.csv`。
5. 审计主二进制：`rtk bash tools/debug/audit-binary-deps.sh --bin <elf> --sysroot <dir>`。
6. 输出发布阻塞项、可接受风险和缺失验证。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk bash scripts/check-release-manifest.sh --manifest <manifest> --root <dir>`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出 release 目录、manifest 路径、缺失依赖、hash 校验结果、设备 smoke 状态。
