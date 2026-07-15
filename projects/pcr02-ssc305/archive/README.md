# PCR02 SSC305 平台归档

本目录是 `pcr02-ssc305` 的唯一平台归档入口，保存 SDK、kernel、boot、镜像、OTA、存储、板级硬件、平台集成和来源审计材料。

## 首选路径

- 工程归档主题索引：`projects/pcr02-ssc305/archive/engineering-archive/pcr02/README.md`
- 来源审计：`projects/pcr02-ssc305/archive/source-audit/`
- 应用、诊断、媒体、显示应用层、模块联调和会话证据：`projects/xcrz-sigmastar-demo/archive/`

## 归档主题路径

- Flash / SPI NAND / FSP / QSPI / pad drive / clock：`engineering-archive/pcr02/boot-flash/`
- `/customer`、SquashFS、UBIFS、ubiblock、warmup read failed、解压失败：`engineering-archive/pcr02/ubifs-squashfs/`
- 老化测试、板端命令、验证步骤、验收记录：`engineering-archive/pcr02/validation/`
- 会话进展、阶段性总结：`engineering-archive/pcr02/session/`

## 使用边界

- 新增正文必须符合本项目边界，并同步 registry/index；应用侧材料直接进入 `projects/xcrz-sigmastar-demo/`，不在本目录复制。
- 源项目当前 `AGENTS.md`、源码、动态分支和构建状态仍由源项目 Git 管理。
- 不能把 archive 中的阶段性结论直接提升为 `current/` 事实；需要先补证据、owner 或验证记录。
- `pcr02` 只作为产品组 ID，不是本目录之外的备用正文入口。
