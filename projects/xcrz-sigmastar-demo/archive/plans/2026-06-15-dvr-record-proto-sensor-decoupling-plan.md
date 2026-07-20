---
doc_type: owner-approved-target
source_id: pcr02-project-docs
source_path: plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
source_sha256: 9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3
source_size: 4786
owner_decision: archive-only
worksheet_id: pcr02-owner-decision-worksheet-005
generated_at: 2026-06-24
id: pcr02-dvr-plan-archive-only-20260624
title: PCR02 DVR proto/sensor 解耦计划归档目标 2026-06-24
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
scope: project-specific
visibility: team-internal
status: archived
owner: team-core
source:
  type: owner-approved-target-materialization
  source_id: pcr02-project-docs
  source_path: plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
  source_sha256: 9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3
  source_manifest: artifacts/manifests/knowledge-hub-source-control-unification-20260624.jsonl
review_after: '2026-09-17'
review_status: owner-approved-archive-only-target-materialized
promotion: none
promotion_decision: none
tags:
- pcr02
- dvr
- archive-only
- owner-decision
- source-control
validation_refs:
- projects/xcrz-sigmastar-demo/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
- artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl
- sources/pcr02-project-docs/inventory.jsonl
evidence_strength: owner-decision-landing-plus-source-sha-target-materialization
evidence_refs:
- artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl
- projects/xcrz-sigmastar-demo/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
- sources/pcr02-project-docs/inventory.jsonl
created_at: '2026-06-24'
updated_at: '2026-06-24'
generated_by_ai: true
ai_role: classified
ai_model_or_tool: Codex
ai_generated_at: '2026-06-24'
summary_zh: 按 owner 决策将 DVR proto/sensor 解耦计划作为 archive-only 目标落地；缺 completed 证据，不声明完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# DVR 录像回放 proto/sensor 解耦设计与实施计划

## Hub 边界

仅归档原计划；缺少 completed 证据，不声明完成，不作为 current baseline。

## 来源

- Source provenance: `registry/sources.json` origin_path for `pcr02-project-docs`; `registry/source-tombstones.jsonl`
- Source path: `plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`
- Source SHA256: `9134247182e7578eec8c2bb4d702ffaed6c75359039d549b679f058bf8532cb3`
- Owner decision: `archive-only`
- Worksheet: `pcr02-owner-decision-worksheet-005`

## 原始正文

---
status: active
date: 2026-06-15
owner: local-codex
scope: dvr-record-proto-sensor-api
last_verified: 2026-06-15
---

# DVR 录像回放 proto/sensor 解耦设计与实施计划

## 背景

旧 `xcrz_application` 由应用逻辑直接调用 `api_dvr` 接口完成录像、事件更新、回放控制、回放列表查询和文件删除。新架构要求业务应用层与 `api_dvr` 解耦：`task` 和 `iot` 模块通过 proto 向 `sensor` 发控制请求，`sensor` 再调用 `VSAPIDVR_RecordStart`、`VSAPIDVR_RecordSetEvent`、`VSAPIDVR_RecordStop` 和回放相关接口。

本仓当前没有 `modules/task`、`modules/iot` 目录，因此本计划只落地本仓负责的 proto、sensor 和 api_dvr 侧能力；`task/iot` 的业务调度由对应团队按契约接入。

## 范围

In:

- 扩展 `modules/proto/sensor_ctrl.proto`，提供 DVR 录像和回放控制命令。
- 扩展 `modules/proto/sensor_info.proto`，提供回放列表查询结果 ACK payload。
- 在 `modules/sensor/hardware/hardware_api.*` 中集中封装 DVR record/replay API。
- 在 `modules/sensor/main/sensor_entry.cpp` 中接入 DVR 控制分发。
- 收敛 `modules/api/src/api_dvr/api_dvr_record.c`：移除定时/事件自动 start/stop，保留显式 start/stop 和事件更新。
- 同步 public header 中 `VSAPIDVR_RecordSetEvent` 的语义注释。

Out:

- 不修改 `task` 和 `iot` 业务实现。
- 不把 `app_main`、`app_product_test` 视为本计划的应用层迁移目标。
- 不迁移 `modules/app/src/app_diag/provider/api/app_diag_api_dvr_provider.c`，它保留为 API 诊断入口；如需诊断也走 sensor/proto，应另开计划。

## 目标语义

录像开始和结束由 `task/iot` 显式控制：

```text
task/iot -> proto DeviceCtrl -> sensor -> HardwareApi -> VSAPIDVR_RecordStart/Stop
```

不管 `VSAPIDVR_RecordType_e` 是 `MANUAL`、`TIMING` 还是 `EVENT`，`api_dvr_record.c` 都不再维护业务时序。

事件更新接口必须保留：

```c
VSAPIDVR_RecordSetEvent(VSAPIDVR_RecordEventType_e enRecordEventType, VS_U64 u64StartTime)
```

该接口仅用于更新正在进行的事件录像：

- 不隐式启动事件录像。
- 不隐式停止事件录像。
- 可更新事件类型 bit 和最近事件时间。
- 如果当前没有 active event record，应返回失败。

## 接口设计

`sensor_ctrl.proto` 新增：

- `DvrRecordPayload`
  - `START`
  - `UPDATE_EVENT`
  - `STOP`
  - record type: manual/timing/event
  - event type
  - frame type
  - start/end time

- `DvrReplayPayload`
  - `START`
  - `STOP`
  - `PAUSE`
  - `RESUME`
  - `SEEK`
  - `SPEED`
  - `LIST_FETCH`
  - `DELETE`
  - start/end/seek time
  - speed rank
  - dir/file mode
  - days-without-start-time
  - path

`sensor_info.proto` 新增：

- `DvrReplayEntry`
- `DvrReplayListResult`
- `DeviceCommandResult.oneof dvr_replay_list`

## 实施步骤

1. 创建本计划文档，固定当前目标、范围和验证命令。
2. 扩展 proto 契约并生成 C++ 代码。
3. 扩展 `HardwareApi`，把 DVR record/replay 调用集中到 sensor。
4. 扩展 `SensorEntry::onDeviceCtrlMsg()`，接入 DVR record/replay 命令。
5. 收敛 `api_dvr_record.c`：
   - 移除 `VSAPIDVR_RecordTiming_t astRecordTiming`。
   - 移除 `_DVR_RecordCheckNextTiming()`。
   - 移除 `_DVR_RecordMainTask()` 中 timing/event 自动 start/stop。
   - 保留 SD 卡异常处理、卸载、格式化和异常时停止录像。
   - 保留 `VSAPIDVR_RecordSetEvent()`，改为 active event update。
6. 运行 proto 生成、构建和定向 grep 验证。

## 验证命令

```bash
rtk bash -lc "modules/proto/build_proto.sh"
rtk bash -lc "./make.sh"
rtk bash -lc "python3 build/check_api_dvr_refcount.py"
rtk rg -n "astRecordTiming|_DVR_RecordCheckNextTiming" modules/api/src/api_dvr/api_dvr_record.c
rtk rg -n "VSAPIDVR_RecordStart|VSAPIDVR_RecordStop|VSAPIDVR_Replay" modules/sensor modules/proto
```

## 风险

- `api_dvr_record.c` 的主线程同时负责 SD 卡异常检测，收敛录像业务逻辑时不能破坏热插拔、无空间、只读、卸载和格式化处理。
- 回放列表可能较大，同步 ACK 需要控制返回条目数量。
- 诊断 provider 仍直接调用 `api_dvr`，这是诊断边界，不代表业务应用层。
- `task/iot` 需要按新 proto 契约显式调度定时录像和事件录像，否则底层不会再自动 start/stop。

## 完成标准

- proto 能表达 DVR 录像、事件更新、回放控制、列表查询和删除。
- sensor 能执行 DVR record/replay 命令并返回 ACK。
- `api_dvr_record.c` 不再维护定时录像表，不再自动启动/停止 timing/event 录像。
- `VSAPIDVR_RecordSetEvent()` 保留且只更新 active event record。
- 构建和定向验证命令完成，结果记录在最终交付说明中。
