# 证据写法规范

## 目标

长期知识条目必须能被复核。本文约束结论、证据、推断、建议、命令和外部资料的写法。

## 事实边界

- `结论`：已经由证据支持，可以被后续复用。
- `证据`：命令输出、日志摘要、artifact 引用、source path、hash、owner review 或官方资料。
- `推断`：基于证据的判断，但尚未直接验证，必须显式标注为推断。
- `建议`：下一步动作或方案，不等同于事实。
- `开放问题`：需要 owner、测试或外部资料继续确认的问题。

## 命令证据

记录命令证据时至少包含：

- `cwd`：执行目录。
- `date`：执行日期。
- `command`：完整 `rtk ...` 命令。
- `exit_code`：退出码。
- `scope`：命令覆盖范围。
- `result_summary`：中文摘要结果。
- `artifact_refs`：日志、JSON、截图或报告引用；大文件只登记引用，不写正文。

不得只写“已验证”或“测试通过”，必须写清验证对象和证据。

## Evidence Index

长期条目、manifest 和验证报告建议使用同一张命令级证据索引表，方便人工复核和后续迁移：

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk ...` | `0` | 中文摘要。 | `artifacts/manifests/<id>.md` 或日志引用 | Knowledge Hub / Project / Tool | registry id、manifest 或制品引用 |

写表时遵循：

- `Command` 必须是完整 `rtk ...` 命令。
- `Result Summary` 用中文说明证明了什么，不只写 pass。
- `Evidence Path` 指向本仓相对路径、artifact ref 或外部 URI；大文件只写引用、size 和 hash。
- `Layer` 说明证据属于 Knowledge Hub、Project、Tool、Device、Owner Review 或 External Reference。
- `Related Artifact` 关联 registry id、manifest id、commit、日志或制品引用。
- 如果命令无法执行，要写明 `Exit Code`、失败原因、影响和后续 owner。

## 证据强度

建议使用以下强度标记：

| 标记 | 含义 |
| --- | --- |
| `official` | 官方资料或权威发布 |
| `direct-command` | 本地命令直接验证 |
| `direct-log` | 设备或服务日志直接证据 |
| `human-review` | owner 或人工复核结论 |
| `external-reference` | 外部文章、项目或资料 |
| `inference` | 推断，不能单独提升为 active |

## active 条件

条目标为 `active` 前必须满足：

- 有 owner。
- 有 source。
- 有 review_after。
- 有可回溯证据或 registry 引用。
- 已通过 secret scan。
- project-specific 内容未进入团队标准目录。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
