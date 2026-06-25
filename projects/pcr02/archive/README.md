# PCR02 归档入口

本目录保存 PCR02 历史归档和工程排障材料。它是 Knowledge Hub 终态归档入口，新增归档不得写回外部旧目录或旧 source 迁移副本。

## 首选路径

- 工程归档主题索引：`projects/pcr02/archive/engineering-archive/pcr02/README.md`
- PCR02 旧正文剪枝账本：`artifacts/manifests/pcr02-*-body-prune-20260625.md`
- owner 决策落地后的计划和报告：`projects/pcr02/archive/plans/`、`projects/pcr02/archive/reports/`

## 归档主题路径

- Flash / SPI NAND / FSP / QSPI / pad drive / clock：`engineering-archive/pcr02/boot-flash/`
- `/customer`、SquashFS、UBIFS、ubiblock、warmup read failed、解压失败：`engineering-archive/pcr02/ubifs-squashfs/`
- 老化测试、板端命令、验证步骤、验收记录：`engineering-archive/pcr02/validation/`
- 会话进展、阶段性总结：`engineering-archive/pcr02/session/`

## 使用边界

- 旧过渡正文副本已按剪枝账本移除，不是新增知识入口，也不作为查询入口。
- 历史 `AGENTS.md` 正文副本已按剪枝账本移除，源项目当前 `AGENTS.md` 由源项目 Git 管理。
- 新会话总结、阶段性结论和排障记录如需长期保留，应新增到本目录的主题分区，并同步 registry/index。
- 不能把旧 archive 中的阶段性结论直接提升为 `current/` 事实；需要先补证据、owner 或验证记录。
