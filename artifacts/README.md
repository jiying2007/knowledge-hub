# Artifacts

本目录保存非正文制品的结构化证据和受控附件副本。

- `manifests/`：artifact-ref、owner gate、验证、审计和终态证据；不等同于 `registry/items.jsonl`。
- `vault/`：仅保存经批准、体量受控、不可变且有逐文件 `size`/`sha256` 清单的附件副本。缺失、hash/size 漂移或无清单额外文件由 `knowledge-check` 阻断。

raw log、core、SDK、release binary、源码包和运行时 secret 不得进入 vault。清单中标为 `external-reference-only` 的对象只保留 URI/size/hash provenance，不得声称本地文件存在。

Do not store raw SDK packages, logs, core dumps, release binaries, credentials, private keys, tokens, cookies, or other secrets here.

## 历史清单的适用性（2026-10-20）

`manifests/` 中带日期的正文保存当时的观察、操作和边界，不是当前命令手册，也不是新的执行授权。复用前先确认当前 HEAD、工作区状态、项目归属及 [工具入口](../tools/README.md)，不要直接复制历史命令。

| 历史入口 | 已确认的适用性差异 | 当前使用边界 |
| --- | --- | --- |
| [2026-06-21 人工恢复与边界加固](manifests/knowledge-hub-manual-recovery-boundary-hardening-20260621.md) | 包含旧 `domains/projects/pcr02/` 路径和当时的 source 枚举。 | 当前项目按 `projects/<project>/` 归属区分；PCR02 的 `projects/pcr02-ssc305/` 与 `projects/xcrz-sigmastar-demo/` 不是可互换命名空间。先定位原始条目和实际项目，不做一对一全局路径替换；枚举以当前工具与 Registry 契约为准。 |
| [2026-06-22 恢复、搜索与人工入口加固](manifests/knowledge-hub-recovery-search-manual-hardening-20260622.md) | 仍描述 `knowledge-new.sh --source` 的 `--source-status` 参数。 | `--source-status` 已移除；当前回归契约要求它以退出码 2 和 `ERROR unknown argument: --source-status` 拒绝。不要恢复此参数，也不要把省略它解释为可自由选择 source 生命周期；当前默认值与合法字段以当前工具输出为准。 |

### 计划、历史结果与现行证据

“验证计划”“预期通过”“待执行”不等于实际执行结果；表格填有数值退出码，也不能单独证明命令已经执行。历史 `pass`、回归数量、日期排序的 latest、路径存在检查和目录清单，都不能替代当前正文审查、当前源码验证或设备/HIL/生产验收。

用于新的验收时，应另外取得同源提交、完整制品 SHA-256、执行日期、命令、实际退出码和适用范围；缺少证据就保留“需要补证”，不得补写成功结果。不要为消除审查告警改写历史原文、重签旧哈希、自动延后 `review_after`、提升 Active、代签 Owner 或关闭 owner gate。

本节只增加当前入口的适用性说明，不修改上述历史正文或原有证据，也不授予发布、设备操作、源项目写入或安全审批权限。具体正文审读收据与待办仍统一记录在 Issue #176；入口说明和机器检查通过不等于全库知识自动审查完成。
