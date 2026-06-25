---
name: artifact-provenance-audit
description: 审计嵌入式固件、模型、配置、动态库、调试符号和发布包的来源追溯、hash、manifest、敏感信息与归档边界。
version: 1.0.0
last_updated: 2026-05-18
---

# Artifact Provenance Audit

## 1. 触发条件

- 用户要求检查固件、模型、配置、动态库、debug symbol 或发布包来源。
- 用户准备把制品索引、manifest 或归档记录写入知识库。

## 2. 处理范围

- 处理来源字段、hash、manifest、敏感信息、Git 入库边界。
- 不把大文件、core、SDK 原包或敏感日志写入 Git。

## 3. 工作流

1. 读取 `docs/standards/embedded-artifact-provenance-standard.md`。
2. 对制品目录执行 `rtk bash scripts/generate-release-manifest.sh --root <dir> --out <manifest>`。
3. 对 manifest 执行 `rtk bash scripts/check-release-manifest.sh --manifest <manifest> --root <dir>`。
4. 对仓库执行 `rtk bash scripts/check-secrets.sh` 与 `rtk bash scripts/check-artifacts.sh`。
5. 输出可入库索引、禁止入库内容和缺失来源字段。

## 4. 最小验证

- 构建：`rtk bash scripts/check-all.sh`
- 边界扫描：`rtk bash scripts/check-artifacts.sh`
- 规范检查：`rtk python3 docs/governance/check_agent_skill_consistency.py`

## 5. 输出要求

- 输出 manifest 路径、缺失字段、敏感风险、Git 禁止项和归档建议。
