---
doc_type: debug-record
knowledge_type: incident-learning
maturity: archived
created: 2026-07-11
last_updated: 2026-07-11
related:
- ../../current/runbooks/project-debug-tools-guide.md
- ../../../../domains/embedded/runbooks/gdb-debug-guide.md
- 2026-07-02-prog-pcr02-core-gdb-selection.md
id: pcr02-core-gdb-triage-20260623
title: PCR02 core/GDB 离线排障归档 2026-06-23
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-06-23-pcr02-core-gdb-triage.md
scope: project-specific
visibility: team-internal
status: archived
owner: leiwenjun
source:
  type: codex-archive-migration
  source_id: codex-archive
  source_path: domains/codex/archive/codex-archive/debug-notes/20260623-075032-pcr02-core-gdb-triage.md
  source_sha256: 88d4a2ab2ba7fc8a2039870f0d4135d545e90594709751b5ce6c179638b79c17
  coverage_row: CAFC-20260711-002
review_after: '2026-10-11'
review_status: human-reviewed-accepted
promotion: none
promotion_decision: none; historical crash evidence migration, no active promotion and no fix-complete claim
tags:
- pcr02
- prog_pcr02
- core
- gdb
- buildid
- motor-temperature
- navigation
- archive-only
- codex-archive-migration
- deleted-tombstoned
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-06-23-pcr02-core-gdb-triage.md
- rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 core GDB triage"
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
evidence_strength: codex-archive-source-plus-subagent-read-only-audit-plus-final-coverage-and-tombstone
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-06-23-pcr02-core-gdb-triage.md
- artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-002
- artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-042
- subagent:019f4cec-70fd-7360-b598-3c358ba58009
created_at: '2026-07-11'
updated_at: '2026-07-11'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-11'
summary_zh: 从旧 Codex archive 迁移 PCR02 core/GDB 离线排障：保留 BuildID 配对、MotorTemperatureController `context_` 空指针、`-77` under-temp
  路径、NaviCtrl/ObstacleMap 低置信边界和修复方向；archive-only，不声明修复完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 core/GDB 离线排障归档 2026-06-23

## 归档边界

本文从旧 Codex archive `debug-notes/20260623-075032-pcr02-core-gdb-triage.md` 抽取。它保留 BuildID 配对规则、关键崩溃证据和后续修复方向，不复制 raw core、完整 GDB 输出、二进制或私有构建产物，不声明修复完成。

## 主要结论

1. 离线 core 分析必须先核对 core、stripped binary 和 debug full binary 的 BuildID。同名 `prog_pcr02.debug.full` 不等于同源。
2. `core-prog_pcr02-914-13198` 的强证据指向 `controller::MotorTemperatureController::triggerUnderTempProtection(int)` 中对象内部 `context_` 为空后的二级解引用。
3. 该 core 的温度参数为 `-77`，低温阈值约为 `-10`，说明是一次真实 under-temp 保护路径触发，不是误入分支。
4. `core-prog_pcr02-914-9104` 只能限制在 `controller::NaviCtrl::follow(int)` 附近的函数/反汇编级判断，不能下源码级根因结论。
5. `core-nav.heartbeat-936-1782393863` 最终落点在 `libzmq.so`，但更有价值的线程证据是 `navigation::ObstacleMap::update(this=0xfffffff8, ...)`。不能把 `libzmq` 直接当根因。

## 推荐排障流程

- core 文件名只能作为线索，不能替代 BuildID。
- 同时检查 `out/arm/app/prog_pcr02`、`release/bin/prog_pcr02`、`out/arm/app/prog_pcr02.debug.full`。
- fastpass 包括 `bt 12`、`info registers`、`info threads`、`info proc mappings` 和 `p $_siginfo`。
- deeppass 针对崩溃函数反汇编，读取 `this` 指针关键字段，并核对函数参数是否符合业务状态。
- 最终结论必须分层记录崩溃落点、更可能的根因对象/状态、置信度和缺失证据。

## 关键证据摘要

`core-prog_pcr02-914-13198`:

- 进程为 `/customer/bin/prog_pcr02`。
- 崩溃函数为 `controller::MotorTemperatureController::triggerUnderTempProtection(int)`。
- 关键指令为 `ldr r0, [r3, #8]`，关键寄存器 `r3=0`。
- `this+0x24` / `this+0x28` 为空，符合 `std::shared_ptr<utils::Context>` 为空。
- 入参为 `-77`。

`core-prog_pcr02-914-9104`:

- stripped binary BuildID 与 stale debug full BuildID 不一致。
- 可信结论应限制在函数级和反汇编级。

`core-nav.heartbeat-936-1782393863`:

- 线程证据出现 `navigation::ObstacleMap::update(this=0xfffffff8, ...)`。
- `libzmq` 是崩溃落点，不足以证明库本身是根因。

## 修复方向

- `MotorTemperatureController::init()` 失败时不应保留可被回调访问的 controller。
- `onMotorData()`、`triggerUnderTempProtection()` 和 release/protection 函数应增加 `context_` 空值保护。
- navigation 方向需要匹配版本源码或完整符号包后，再检查 `ObstacleMap` 生命周期、初始化顺序和回调并发。
- 建议在 `Interface::heartbeatLoop()`、`VizPublisher::heartbeatLoop()`、`Interface::onTofData()`、`ObstacleMap::update()` 增加低噪声对象状态日志。

## 迁移记录

- Old source: `domains/codex/archive/codex-archive/debug-notes/20260623-075032-pcr02-core-gdb-triage.md`
- Old source SHA256: `88d4a2ab2ba7fc8a2039870f0d4135d545e90594709751b5ce6c179638b79c17`
- Old source size: `4456` bytes
- Old source lines: `81`
- Final coverage row: `artifacts/manifests/codex-archive-final-body-coverage-20260711.jsonl#CAFC-20260711-002`
- Tombstone: `artifacts/manifests/codex-archive-removal-execution-20260711-final-bodies.jsonl#CARE-20260711-042`
