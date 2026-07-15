# XCRZ SigmaStar Demo 应用归档

本目录是 `xcrz-sigmastar-demo` 的唯一应用归档入口，保存应用、诊断、媒体、显示应用层、模块联调和会话证据。

## 主题入口

- `debug/`：应用运行态、core/GDB、显示和摄像头问题排障。
- `plans/`：应用架构、协议、诊断和模块改造的历史计划。
- `reports/`：应用联调、会话收口和历史验证报告。

## 使用边界

- SDK、kernel、boot、镜像、OTA、存储、板级硬件和平台集成材料进入 `projects/pcr02-ssc305/`，不在本目录复制。
- 新增正文必须同步 registry/index；未登记历史语料只能由显式冻结的 archive corpus 覆盖。
- 源项目当前 `AGENTS.md`、源码、动态分支和构建状态仍由源项目 Git 管理。
- archive 中的阶段性结论不能直接提升为 `current/` 事实；需要先补证据、owner 或验证记录。
- `pcr02` 只作为产品组 ID，不是备用正文 domain、目录或 route。
