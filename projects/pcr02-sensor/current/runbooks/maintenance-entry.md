---
id: pcr02-sensor-readiness-runbook-20260713
title: PCR02 Sensor Module 维护入口
kind: runbook
domain: projects/pcr02-sensor
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
review_after: '2026-10-13'
review_status: human-reviewed-accepted
promotion: none
tags:
- pcr02-sensor
- project-readiness
- runbook
- ai-generated
- owner-review-pending
- manual-validation-pending
- no-active-promotion
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
manual_validation_pending: true
decision_owner: unassigned
summary_zh: 定义 PCR02 Sensor Module 的 Knowledge Hub 预检、候选写入、验证与授权边界，不生成未经源项目确认的工程命令。
promotion_decision: none; structural readiness asset only, no active promotion or owner decision
path: projects/pcr02-sensor/current/runbooks/maintenance-entry.md
project_id: pcr02-sensor
readiness_slot: runbook
aliases:
- pcr02-sensor runbook
- pcr02-sensor-runbook
related:
- projects/pcr02-sensor/README.md
- projects/pcr02-sensor/current/project-profile.md
- projects/pcr02-sensor/decisions/project-boundary-decision-candidate.md
- projects/pcr02-sensor/validation/project-readiness.md
---

# PCR02 Sensor Module 维护入口

> 本 runbook 只定义 Knowledge Hub 维护流程，不提供未经源项目验证的构建、刷机、设备或发布命令。

## 1. 预检

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "pcr02-sensor 当前事实与验证" --task-type validation --json
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "pcr02-sensor" --json --limit 10
```

确认 route 的 `selected_project_id=pcr02-sensor`，并区分 `current`、`recent` 与 archive-only provenance。若本机只有 `workspace://` 而没有 local mapping，先补只读映射或由 owner 提供源码证据，不猜测路径。

## 2. 变更分类

- 当前事实：先在源项目验证，再捕获为 `draft/reviewing` candidate。
- 决策：补真实 decision owner、备选方案、影响范围、回滚和验证后进入 owner review。
- 验证：保留版本/commit、环境、命令、返回码、关键日志、制品 hash 和结论边界。
- 历史材料：只进入 archive/provenance，不自动提升 active。

## 3. Hub 写入

```bash
rtk bash ~/knowledge-hub/tools/knowledge-capture.sh --help
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --json --strict
```

capture 只允许创建 `draft/reviewing/personal`。promotion、retire、owner decision、memory write、source project write 和远端发布必须走独立授权门禁。

## Related

- [项目画像候选](../project-profile.md)
- [边界决策候选](../../decisions/project-boundary-decision-candidate.md)
- [readiness validation](../../validation/project-readiness.md)
- [项目入口](../../README.md)
- route、检索、链接、registry 和正文镜像一致。
- 项目特有构建/设备/发布证据由真实执行方补齐，当前文档不代签。
