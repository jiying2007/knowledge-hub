---
name: sdk-upgrade-risk-review
description: 审查 SigmaStar SDK/BSP/工具链升级风险，覆盖 ABI、头文件、动态库、rootfs、kernel module、回归范围和回滚策略。
version: 1.0.0
last_updated: 2026-05-18
---

# SDK Upgrade Risk Review

## 1. 触发条件

- 用户准备升级 SDK、BSP、工具链、rootfs 或平台库。
- 用户需要评估升级风险、回归范围、ABI 兼容或回滚方案。

## 2. 处理范围

- 处理升级计划、差异面、依赖匹配、回归矩阵和回滚证据。
- 不直接认定升级安全；必须给出验证缺口。

## 3. 工作流

1. 读取 `docs/runbooks/sigmastar-sdk-upgrade-playbook.md`。
2. 记录旧版本 manifest 与二进制依赖。
3. 按工具链、headers、libraries、kernel modules、rootfs、profiles 分层审查。
4. 对主二进制执行 `rtk bash tools/debug/audit-binary-deps.sh --bin <elf> --sysroot <dir>`。
5. 输出 smoke 用例矩阵、阻塞风险、回滚条件。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk python3 docs/governance/check_docs_links.py --changed-only`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出升级目标、变更层级、ABI 风险、回归清单、回滚路径和未验证项。
