# pcr02-project-agent-config Source 策略

## 终态

该 source 必须通过 `sources/pcr02-project-agent-config/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/pcr02-project-agent-config`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。

## 项目配置与执行权限边界（2026-10-23）

Hub 在此仅维护配置来源身份、风险说明和非执行性的审查证据；旧 agent 配置、工作流与可执行规则的运行权威仍属于各自源码仓和部署环境。通用的“新增归档、摘要和知识正文”不授权从历史配置复制敏感值、启用自动化、改动源码仓 `AGENTS.md` 或覆盖运行时设置。

如需产生规范知识，先按照当前项目路由落入唯一 canonical 候选，再取得适用版本、实际依赖和独立权限证明；`source-control` 文件存在不等于已验证运行配置。
