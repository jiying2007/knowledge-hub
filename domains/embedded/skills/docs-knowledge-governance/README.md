# docs-knowledge-governance

## 触发词

- 修改 `docs/` 结构、模板、标准、runbook 或治理脚本
- 新增知识库文档、迁移项目文档、修复文档链接
- 调整 `docs/AGENTS.md` 或 `.agents/skills/docs-knowledge-governance/*`

## 工作流

1. 明确文档归属：通用知识进本仓，项目强绑定内容留在项目仓。
2. 复用 `docs/templates/` 模板创建文档。
3. 更新 `related` 与 `validation_refs`，避免孤儿知识资产。
4. 执行 `rtk bash scripts/check-all.sh`。

## 输出要求

- 说明新增/修改文档清单。
- 说明验证命令与结果。
- 若存在无法自动验证的引用，明确人工复核点。
