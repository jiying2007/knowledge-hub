---
title: 排障记录规范
summary_zh: 规定排障记录中事实、观察、推断、根因、验证、未决项和下一步的分层写法，避免 raw log 或未经证实结论进入长期事实。该 active 规范不证明具体故障已修复，也不替代实机/回归验证。
tags:
- governance
- debug-record
- evidence
- zh-cn
id: knowledge-hub-debug-record-rules
kind: standard
domain: governance
path: governance/debug-record-rules.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- 排障记录规范
related:
- indexes/obsidian-home.md
---

# 排障记录规范

## 目标

排障记录用于保存问题定位过程和证据边界。排障记录本身默认不是 active 事实，稳定结论必须经过 owner review 后再提升为 runbook、validation、decision 或 current fact。

## 必填结构

- `现象`：用户可见症状、错误码、时间、频率。
- `影响范围`：项目、设备、版本、模块、是否量产或现场。
- `环境`：硬件、固件、配置、工具、输入数据。
- `时间线`：关键观察、操作和状态变化。
- `证据`：日志摘要、命令摘要、artifact 引用和 hash；不落 raw 大文件正文。
- `假设与排除`：每个假设、验证动作和结果。
- `根因`：确认根因；未确认时写“未确认”。
- `修复或规避`：已执行动作、适用范围和副作用。
- `验证`：复现前后对比、命令和通过/失败判据。
- `后续动作`：是否提升、归档、继续验证或交给 owner。

## 证据边界

- raw log、core、SDK 压缩包、release binary 不进入文本知识层。
- 大文件只进入 artifact manifest 或 artifact-ref。
- 现场路径、客户名称、账号、凭证和私有 URL 必须脱敏。
- 未确认根因不得写成结论。

## 提升规则

- 复现步骤稳定后，可提升为 runbook 候选。
- 修复验证充分后，可提升为 validation report。
- 设计或流程选择明确后，可提升为 decision。
- 只反映历史现场状态时，保留为 project archive。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
