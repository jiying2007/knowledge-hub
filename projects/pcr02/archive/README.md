# PCR02 归档入口

本目录保存 PCR02 历史归档和工程排障材料。它是 Knowledge Hub 终态归档入口，不再使用旧 `~/embedded/engineering_archive/pcr02/` 或旧 source 迁移副本作为新增归档路径。

## 首选路径

- 工程归档主题索引：`projects/pcr02/archive/engineering-archive/pcr02/README.md`
- 旧 PCR02 docs/knowledge/tools/source 正文剪枝账本：`artifacts/manifests/pcr02-source-docs-body-prune-20260625.md`
- owner 决策落地后的计划和报告：`projects/pcr02/archive/plans/`、`projects/pcr02/archive/reports/`

## 旧路径映射

```text
~/embedded/engineering_archive/pcr02/boot-flash/
-> ~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/boot-flash/

~/embedded/engineering_archive/pcr02/ubifs-squashfs/
-> ~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/ubifs-squashfs/

~/embedded/engineering_archive/pcr02/validation/
-> ~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/validation/

~/embedded/engineering_archive/pcr02/session/
-> ~/knowledge-hub/projects/pcr02/archive/engineering-archive/pcr02/session/
```

## 使用边界

- 旧过渡正文副本已按剪枝账本移除，不是新增知识入口，也不作为查询入口。
- 历史 `AGENTS.md` 正文副本已按剪枝账本移除，源项目当前 `AGENTS.md` 由源项目 Git 管理。
- 新会话总结、阶段性结论和排障记录如需长期保留，应新增到本目录的主题分区，并同步 registry/index。
- 不能把旧 archive 中的阶段性结论直接提升为 `current/` 事实；需要先补证据、owner 或验证记录。
