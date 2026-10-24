# pcr02-project-tools Source 策略

## 终态

该 source 必须通过 `sources/pcr02-project-tools/` 在 Hub 内可恢复、可搜索、可审计。

## 当前策略

- `registry/sources.json` 的 `path` 已收敛到 `sources/pcr02-project-tools`。
- 当前知识入口只使用 Hub 内路径。
- 通过 inventory 记录正文、附件、runtime input 或 hub-native 边界。

## 后续维护

- 新增归档、摘要和知识正文必须写入 Hub canonical 目录，不得写回旧 origin。
- runtime input 只抽取摘要、候选和证据索引；不复制 raw 全文，不把 raw 行提升为 active fact。

## 工具源码与Hub文本身份（2026-10-23）

此处只管理退役工具文档的来源、hash、候选摘要与可审计定位；真实脚本、可执行命令、构建/测试及工具链依赖继续归属于对应PCR02源码仓，不从旧工具目录复制代码或重新启用历史工作流。通用的“新增知识正文”只允许写入经当前项目路由确认的脱敏、不可执行的知识候选，不把源码路径本身提升为Hub Active。

如需使用工具，先由源仓责任人确认当前精确提交、调用参数、运行环境、权限、备份及结果证据；`coverage=hub-canonical` 仅说明Hub控制面已登记，不表示脚本的安全性、发布或设备执行资格已验证。
