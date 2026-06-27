# Projects

项目知识唯一主入口。

## 项目界定

长期项目入口按三层管理：

- 产品组 / 项目组：例如 `pcr02`、`mcu`，负责跨仓集成视图、共同决策和跨仓验证。
- Git 仓库项目：例如 `pcr02-ssc305`、`xcrz-sigmastar-demo`、`hc32f072`、`llm-agent`，负责该 remote 边界内的当前事实、决策、验证和归档。
- 组件：没有稳定 Git remote 或只是源码树局部目录时，登记到 `registry/components.json`，不单独成为事实主入口。

路由规则：

- 当前事实优先按 Git remote key 路由到 `registry/repositories.json` 中的 `project_id`。
- 产品组只聚合成员项目，不替代成员仓库的事实边界。
- 本机源码路径只允许出现在未纳入 Git 的本地 workspace 适配文件；Hub 内长期 registry 使用 `workspace://...`、`project://...`、`kh://...` 或仓库 `remote_key`。

## 目录约定

每个 Git 仓库项目使用：

```text
projects/<project>/
  current/
  decisions/
  validation/
  archive/
```

产品组也使用同样目录，但只存放跨仓集成信息和组级决策。

新增项目长期资产必须登记 `registry/items.jsonl`，并同步核心索引。
