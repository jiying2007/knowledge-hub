# PCR02 项目知识入口

本目录是 PCR02 在 Knowledge Hub 中的项目级入口。新增项目事实、归档、验证记录和决策时，优先落到本目录下的对应分区，不再写回源项目 `docs/`、`knowledge/` 或 `tools/`。

## 当前入口

- 当前事实和 runbook：`projects/pcr02/current/`
- 当前项目决策：`projects/pcr02/decisions/`
- 验证记录和可复跑证据：`projects/pcr02/validation/`
- 历史归档和工程排障材料：`projects/pcr02/archive/`
- 迁移证据、owner gate、source coverage：`artifacts/manifests/` 中 `pcr02-*` 与 `knowledge-hub-*pcr02*`

## 归档主题路径

- Flash / SPI NAND / FSP / QSPI / pad drive / clock：`projects/pcr02/archive/engineering-archive/pcr02/boot-flash/`
- `/customer`、SquashFS、UBIFS、ubiblock、warmup read failed、解压失败：`projects/pcr02/archive/engineering-archive/pcr02/ubifs-squashfs/`
- 老化测试、板端命令、验证步骤、验收记录：`projects/pcr02/archive/engineering-archive/pcr02/validation/`
- 会话进展、阶段性总结：`projects/pcr02/archive/engineering-archive/pcr02/session/`

## 跨项目和跨会话关联

- 项目维度恢复：看 `indexes/by-project.md` 的 PCR02 分区。
- 主题维度恢复：看 `indexes/by-topic.md`，再用 `knowledge-search` 查关键词。
- source 迁移和边界恢复：看 `indexes/by-source.md` 与 `sources/<source_id>/`。
- owner decision 和人工签收恢复：看 `indexes/by-decision.md` 与 `tools/knowledge-owner-gates.sh`。
- 最新链路体检：运行 `rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json`。

## 新增材料规则

- 稳定项目事实写入 `current/`。
- 历史排障、阶段总结和工程归档写入 `archive/`。
- 验证记录写入 `validation/`。
- owner 签收或决策写入 `decisions/` 或对应 owner-gate manifest。
- raw log、core、SDK 包和 release binary 不写入正文层；只登记摘要、hash、路径或 artifact-ref。
