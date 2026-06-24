# pcr02-project-docs 迁移计划

## 终态

该 source 必须通过 `sources/pcr02-project-docs/` 在 Hub 内可恢复、可搜索、可审计。

## 当前批次

- 建立 source 主控目录。
- 登记最小 inventory root row。
- 保留 source 原文边界，不批量复制 raw、大文件、二进制或源码树。

## 后续批次

- 将高价值 Markdown 或可读知识迁移到 `projects/`、`domains/` 或 `notes/`。
- 将 raw session/history/log 压缩为中文摘要、时间线、决策和候选。
- 将 artifact、binary、PDF、zip、源码树和脚本正文转为 artifact-ref、命令契约、接口说明或 hash 清单。
