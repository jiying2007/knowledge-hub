---
id: pcr02-sensor-cpp17-standard-tooling-closure-20260907
title: Sensor C++17规范与LLVM Tooling门禁归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-09-07-sensor-cpp17-standard-tooling-closure.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: published-source-commits-and-tooling-validation
  from: embedded Knowledge e57f0f9、Sensor 5e3fbc6与LLVM tooling 0494c03的已推送实现及本地复验
  source_sha256: 6162815e21e1476c3f1cea602d418d632202b0f108a8093ca031c5c8ba486891
  temporary_source_retained: false
review_after: '2026-12-07'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- sensor
- cpp17
- coding-standard
- llvm-tooling
- format-gate
- source-ready
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-07-sensor-cpp17-standard-tooling-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-07-sensor-cpp17-standard-tooling-closure.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-07'
updated_at: '2026-09-07'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-09-07'
manual_validation_pending: true
summary_zh: 归档团队C++17基线、Sensor框架规范、锁定LLVM格式门禁的双仓落地、验证证据及存量格式债务边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# Sensor C++17 规范与 LLVM Tooling 门禁归档

## 背景

Sensor 已包含服务编排、线程、状态机、低功耗事务、媒体数据流、显示框架和异步 callback，仅靠
`.clang-format` 不能约束接口、资源 owner、生命周期、并发和验证边界。本轮将通用规则与模块专用规则
分层，并把格式检查接入锁定 LLVM tooling。

## 最终分层

```text
团队 C++17 编码基线
  -> Sensor 框架、生命周期、并发和平台边界增补
  -> module-ai 锁定工具解析与只读格式门禁
  -> 模块构建、行为测试和按需 Board/HIL
```

- 团队发布正文由 embedded Knowledge 维护，Sensor 不复制通用规范。
- Sensor 仓只保留本模块的框架增补、入口和验证矩阵。
- `.clang-format` 是共享格式配置，本轮未修改。
- 集成工程 `tools/llvm-tooling.lock.json` 固定 tooling 版本、revision 和禁止 fallback 契约。
- LLVM tooling 是独立嵌套仓，不复制到业务模块，也不形成父仓 gitlink。

## 落地提交

| 仓库 | 提交 | 内容 |
| --- | --- | --- |
| embedded Knowledge | `e57f0f91cc576c7a97ba5a2f862b7571e6b2969f` | C++17 团队规范、module-ai 格式门禁、测试和知识入口 |
| Sensor | `5e3fbc6c25941d3c311fbae88004f1ef224532c2` | Sensor 框架规范、AGENTS/Skill/开发/验证入口 |
| LLVM tooling | `0494c03c1dc5d7b80c09022b68b2c1fb9216172f` | LLVM 18.1.8 工具、manifest、doctor 和只读格式检查 |

归档只绑定以上提交。归档时 Sensor 分支已在其后出现独立 display 修复提交，不把后续业务改动纳入本轮
规范归档，也不从当前分支头反推本轮提交内容。

## 工具契约

模块统一使用：

```bash
rtk bash tools/ai.sh format-config
rtk bash tools/ai.sh format-check <changed-file.cpp> [more-files...]
```

入口必须：

1. 从独立模块向上解析集成工程 lock；
2. 拒绝绝对路径、`..` 和解析后逃逸集成工程的 tooling 路径；
3. 确认 tooling 是独立 Git 根；
4. 确认 HEAD 等于 lock revision 且工作树干净；
5. 执行 doctor，核验二进制大小、SHA256、版本和动态依赖；
6. 用锁定 clang-format 解析共享配置；
7. 对模块内 C/C++ 文件执行 `--dry-run --Werror`；
8. 不执行 `-i`，不回退系统 clang-format。

## 验证证据

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| Knowledge `scripts/check-all.sh` | PASS，88 项测试 | 文档、工具、schema、链接、Skill、shell 和 secret 门禁 |
| module-ai 定向测试 | PASS，16 项 | lock 缺失、revision 漂移、tooling 脏改、成功调用顺序及既有模块契约 |
| Sensor `tools/ai.sh doctor` | PASS | 独立仓身份和团队工具契约 |
| Sensor `tools/ai.sh check` | PASS，扫描 166 个源码文件 | 文档、Skill、include 字面边界和 Git 空白 |
| Sensor `tools/ai.sh format-config` | PASS | LLVM 18.1.8、锁定 revision、tooling doctor 和配置解析 |
| `format-check main/sensor_entry.cpp` | NEEDS-FIX | 证明存量源码格式债务；返回 `modified=false` |
| 两仓 Git 推送后读回 | PASS | Knowledge HEAD 等于 origin/main；Sensor 目标提交已进入 origin/master |

共享配置身份：

```text
modules/sensor/.clang-format
SHA256 c5b7cef765c97afdb22b3d40a8bf8c260e51d62a4b2cb315392e429b8441a6e3
```

`main/sensor_entry.cpp` 格式检查前后 SHA256 均为
`84e62b50c5ea34bafa19d9f1fcdbaf7a6a0bd6e6cf28635a16924c119f926582`，确认门禁没有修改源码。

## 边界与未关闭项

- 团队 C++17 规范保持 draft，仍需 owner 内容复核。
- Sensor 存量 C++ 文件尚未全部满足共享 `.clang-format`；必须使用独立机械提交处理，不能通过修改配置或
  回退工具隐藏。
- clang-tidy 只有在准确 compile database、目标宏、include 和规则集明确后才能启用。
- 本轮没有修改 C++ 业务逻辑，没有执行固件构建或 Board/HIL；不能据此声明产品行为变化或设备验证完成。
- Knowledge 检查中的既有非阻断过期 review item 与本轮规范实现无关。

## 回滚与后续

- 团队规范回滚：revert Knowledge 提交 `e57f0f9`。
- Sensor 入口回滚：revert Sensor 提交 `5e3fbc6`。
- LLVM tooling 版本回滚必须修改 lock、保留供应链 manifest 并重新执行 doctor/config-check，不允许静默换用系统工具。
- 后续先做 owner review，再单独盘点和机械格式化 Sensor 存量 C++，最后在可复现 compile database 上评估 clang-tidy。

## 脱敏说明

归档不包含设备端点、凭据、raw log、SDK、二进制、客户资料、完整会话或个人身份信息。只记录受管仓库
提交、工具 revision、配置 hash、验证摘要和可复用决策边界。
