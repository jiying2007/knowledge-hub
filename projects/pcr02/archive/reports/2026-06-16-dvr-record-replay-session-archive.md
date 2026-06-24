---
title: DVR 录像回放解耦会话归档
doc_type: owner-approved-target
status: archive-only
owner: leiwenjun
source_id: pcr02-project-docs
source_path: reports/2026-06-16-dvr-record-replay-session-archive.md
source_sha256: 266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc
source_size: 6697
owner_decision: archive-only
worksheet_id: pcr02-owner-decision-worksheet-007
review_after: 2026-09-17
generated_at: 2026-06-24
---

# DVR 录像回放解耦会话归档

## Hub 边界

仅归档 session archive；handoff、dirty-state 和 memory candidates 不进入 active facts，不写 memory。

## 来源

- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source path: `reports/2026-06-16-dvr-record-replay-session-archive.md`
- Source SHA256: `266a1c2706da87b39d9e4b204ccece61b0ec9c7a95183c64324e95f606c1dadc`
- Owner decision: `archive-only`
- Worksheet: `pcr02-owner-decision-worksheet-007`

## 原始正文

# DVR 录像回放解耦会话归档

- captured_at: 2026-06-16 10:56:24 +0800
- source_thread: Codex 本地会话
- project: xcrz_sigmastar_demo / modules/api / modules/sensor
- archive_type: session-wrap + knowledge-archive + memory-candidates
- status: active handoff

## 目标与边界

本次工作围绕 DVR 录像回放从旧架构迁移到新架构：

- 旧实现：`xcrz_sigmastar_demo_old/xcrz_application` 由应用直接调用 `api_dvr`。
- 新架构：业务应用层通过 `proto` 发控制消息，由 `sensor` 承接并调用 `api_dvr`；`modules/api/src/api_dvr` 保持底层 DVR 能力。
- 应用层边界：这里的应用层指 `task` 和 `iot` 模块，不是 `app_main` 或 `app_product_test`；`task/iot` 由其他团队负责。
- 生命周期原则：`api_dvr_record.c` 不再维护 `VSAPIDVR_RecordTiming_t astRecordTiming`，也不再按 record type 自行轮询启动/停止录像；所有 `VSAPIDVR_RecordType_e` 的开始和结束统一由 `task/iot -> proto -> sensor -> VSAPIDVR_RecordStart/Stop` 控制。
- 事件更新保留：`VSAPIDVR_RecordSetEvent` 必须保留，用于 active event record 的事件 metadata 更新时间，不再隐式启动或停止事件录像。

## 已落地改动

设计与计划：

- 新增 `docs/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`，记录差异梳理、接口设计、实施计划、验证方式和风险。

`modules/proto`：

- `sensor_ctrl.proto` 新增 `DvrRecordPayload` 和 `DvrReplayPayload`。
- `DeviceCommand.DeviceType` 新增 `DVR_RECORD = 18`、`DVR_REPLAY = 19`。
- `DeviceCommand.Payload` oneof 新增 `dvr_record = 27`、`dvr_replay = 28`。
- `sensor_info.proto` 新增 `DvrReplayEntry`、`DvrReplayListResult`，`DeviceCommandResult` 支持回放列表返回。
- 已运行 `modules/proto/build_proto.sh` 生成对应 pb 代码。

`modules/sensor`：

- `hardware/hardware_api.h/.cpp` 新增 DVR record/replay 封装，集中调用 `VSAPIDVR_RecordStart`、`VSAPIDVR_RecordSetEvent`、`VSAPIDVR_RecordStop` 和 replay 相关 API。
- `main/sensor_entry.cpp` 新增 `DVR_RECORD`、`DVR_REPLAY` 控制分发，完成 proto 到 DVR API 参数映射。
- `LIST_FETCH` 同步返回最多 128 条回放项。

`modules/api`：

- `src/api_dvr/api_dvr_record.c` 删除 timing/event 自动生命周期维护相关结构和轮询逻辑。
- `VSAPIDVR_RecordSetEvent` 调整为只更新 active `DVR_RECORD_TYPE_EVENT` 的事件信息和最近事件时间。
- `include/api_dvr.h` 更新接口注释。

根应用仓公共头：

- `include/api/api_dvr.h` 同步更新 `VSAPIDVR_RecordSetEvent` 注释。

## 分支与当前证据

相关仓库当前分支均已切换到联调分支：

- 应用仓：`dev/dvr_record_replay`
- `modules/api`：`dev/dvr_record_replay`
- `modules/sensor`：`dev/dvr_record_replay`

当前 `git log -1 --stat` 证据：

- 应用仓：`02b7383c feat(dvr): add DVR record and replay control messages`
  - 涉及 `include/api/api_dvr.h`、`modules/proto/sensor_ctrl.proto`、`modules/proto/sensor_info.proto` 和构建产物。
- `modules/api`：`cad7d30 refactor(api_dvr): remove event timing infrastructure and simplify record event handling`
  - 涉及 `include/api_dvr.h`、`src/api_dvr/api_dvr_record.c`。
- `modules/sensor`：`56e0f51 feat(hardware): add DVR record and replay APIs`
  - 涉及 `hardware/hardware_api.cpp`、`hardware/hardware_api.h`、`main/sensor_entry.cpp`。

工作区注意事项：

- 根仓存在较多既有未跟踪目录和构建产物，不能在未确认前清理或回退。
- `modules/sensor` 仍有两个未跟踪 serial 配置文件，和本次 DVR 改动无直接关系。

## 验证记录

已执行并通过：

- `rtk bash -lc "modules/proto/build_proto.sh"`
- `rtk bash -lc "./make.sh --jobs 8"`
- `rtk bash -lc "python3 build/check_api_dvr_refcount.py"`
- `rtk rg -n "astRecordTiming|_DVR_RecordCheckNextTiming|g_stEventParam|_DVR_RecordGetEvent" modules/api/src/api_dvr/api_dvr_record.c`
  - 退出码为 1，无匹配，符合预期。
- `rtk rg -n "VSAPIDVR_RecordStart|VSAPIDVR_RecordStop|VSAPIDVR_Replay" modules/sensor modules/proto`
  - 匹配集中在 `modules/sensor/hardware/hardware_api.cpp`，符合 sensor 封装目标。
- `rtk bash ~/codex/scripts/final-ready.sh`
  - 退出码 0，状态 pass。

已知验证提示：

- 构建仍有既有 `app_product_test` 警告，包括 `snprintf` 截断风险、unused variable、implicit declaration；这些不是本次 DVR 改动引入。
- `final-ready.sh` 提示 `HOT`、`CTX_PRESSURE`、`LARGE_DELTA`，属于会话长度和改动规模提醒。

## 剩余风险与联调重点

- `task/iot` 尚未接入新 proto 控制消息；需要其他团队实现真正业务触发。
- `DvrReplayPayload` 的回放数据通道当前只完成控制面封装，数据回调在 sensor hardware 层为占位处理；后续需要按实际播放链路接入。
- `LIST_FETCH` 目前限制返回 128 条，若业务需要分页或大列表，需要扩展 proto 契约。
- `VSAPIDVR_RecordSetEvent` 新语义要求调用前已有 active event record；`task/iot` 需要先 start，再 update，最后 stop。
- 根仓构建产物已变化，后续提交前需按团队规则决定是否纳入提交。

## Memory Candidates

以下仅为长期记忆候选，未直接写入 `~/.codex/memories`：

1. 在 `xcrz_sigmastar_demo` DVR 录像回放迁移中，业务应用层边界指 `task` 和 `iot`，不是 `app_main` 或 `app_product_test`；`app_diag` 可保留诊断直调边界。
2. `modules/api` 和 `modules/sensor` 是独立 Git 仓库，`modules/proto` 属于应用仓根仓；涉及 DVR 联调时三个相关仓需统一使用 `dev/dvr_record_replay` 分支。
3. 新 DVR 生命周期约束：`api_dvr_record.c` 不维护 timing/event 自动开始结束，所有 record type 由 `task/iot -> proto -> sensor -> VSAPIDVR_RecordStart/Stop` 控制。
4. `VSAPIDVR_RecordSetEvent` 必须保留，但语义是更新 active event record 的事件 metadata；不能再作为隐式事件录像启动入口。
5. 本仓 AGENTS 规则要求所有 shell 命令通过 `rtk` 执行，手工修改仓库文件必须使用 `apply_patch`，不得自动 commit/push。

## 下一步建议

- 与 `task/iot` 团队对齐 `DvrRecordPayload`、`DvrReplayPayload` 字段语义和失败处理。
- 增加 task/iot 调用样例或联调脚本，覆盖 manual/timing/event start-stop、event update、replay list/start/seek/pause/resume/speed/stop/delete。
- 在板端联调前确认回放数据回调链路是否需要由 sensor 透传到上层或独立媒体通道。
- 提交前再次检查三个仓的 dirty 状态，明确构建产物和历史未跟踪内容的提交边界。
