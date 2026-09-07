# Owners

## 默认维护者

- `team-core`：知识库结构、文档治理、通用规范、公共工具。

## 维护规则

- `docs/governance/`、`scripts/`、`.agents/skills/` 变更需要团队核心维护者复核。
- `docs/archive/*/manifest.*` 变更必须包含制品 URI 与 SHA256 校验依据。
- 公共脚本变更必须运行 `rtk bash scripts/check-all.sh`。
