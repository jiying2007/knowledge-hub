# PCR02 OTA App

- 项目 ID：`app-ota`
- 所属组：`pcr02`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=app-ota` 的 Git remote key 为准。
- 当前知识：`projects/app-ota/current/`
- 决策：`projects/app-ota/decisions/`
- 验证：`projects/app-ota/validation/`
- 归档：`projects/app-ota/archive/`

OTA app 的发布、协议、升级验证和失败分析优先沉淀到本入口；跨 SDK 发布链结论再同步到 `projects/pcr02/`。
