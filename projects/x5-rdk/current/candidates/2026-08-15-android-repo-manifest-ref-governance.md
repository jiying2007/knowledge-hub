---
related:
- projects/x5-rdk/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
maturity: null
security_classification: null
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
id: x5-rdk-android-repo-ref-governance-20260815
title: X5 Android repo 引用治理与安全清理
kind: project-current
domain: projects/x5-rdk
path: projects/x5-rdk/current/candidates/2026-08-15-android-repo-manifest-ref-governance.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 来自 X5 repo 工作区分支迁移与本地引用清理的脱敏工程总结
  source_sha256: 68775bd5dc006985341ca28b46ed04a033e262dacbdea74efdb8973dea650896
review_after: '2026-11-15'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- android-repo
- git-refs
- runbook
validation_refs:
- projects/x5-rdk/current/candidates/2026-08-15-android-repo-manifest-ref-governance.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/x5-rdk/current/candidates/2026-08-15-android-repo-manifest-ref-governance.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-15'
updated_at: '2026-08-15'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-15'
manual_validation_pending: true
summary_zh: 区分实际远端跟踪引用与 manifest 快照引用，解释 detached HEAD，并给出 topic 分支提交及精确清理旧引用的可回滚门禁。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 Android repo 引用治理与安全清理
---

# X5 Android repo 引用治理与安全清理

## 摘要

Android `repo` 工作区同时暴露项目 Git 远端跟踪引用和 manifest 快照引用。它们名称相似但权威性不同；工作区项目处于 detached HEAD 也是固定 manifest 的正常结果。修改、提交与清理必须按引用类型分别处理。

## 引用模型

- `refs/remotes/internal/...`：项目 Git 仓中名为 `internal` 的实际 remote-tracking ref，随项目 fetch 更新。
- `refs/remotes/m/...`：`repo` 为 manifest 解析结果维护的工作区快照，用于描述本次同步选择；它不等于额外 Git 远端。
- detached HEAD：项目检出固定提交点时的预期状态，不应直接在其上形成长期开发提交。

两类引用可能短暂不一致。判断远端真实分支以项目 remote 的回读结果为准；判断本次工作区配置以 manifest revision 和固定提交点为准。

## 修改与提交协议

1. 在目标项目内从当前固定提交创建有含义的 topic 分支。
2. 修改前核对项目路径、remote URL 归一化结果、目标基线和工作区 dirty 状态。
3. 提交后推送到受治理的 `vs/dev-x5/<sdk-version>` 或经批准的 topic ref。
4. 更新 manifest 固定 SHA，并在独立目录执行 `repo init`、`repo sync` 与项目计数/提交点校验。
5. 不通过移动已发布 tag 或覆盖旧 release manifest 来传播修改。

## 精确清理协议

- 先枚举完整 ref 名并保存脱敏清单；禁止使用宽泛通配符或目录级删除。
- 普通 ref 使用 `git update-ref -d <exact-ref>`；悬空符号引用使用 `git symbolic-ref --delete <exact-ref>`。
- 每次只删除已确认属于旧命名空间的 ref，保留 `vs/dev-x5/<sdk-version>` 等新引用。
- 清理后同时检查 `for-each-ref`、`show-ref`、manifest revision 和 `repo status`；期望旧引用为零，新引用和固定提交点不变。
- 本地 topic 分支仅在其提交已由新分支或固定 manifest 可达后删除。

## 风险与回退

- 直接编辑 `.git` 或批量删除 `refs/remotes/m` 可能破坏 `repo` 的工作区认知，不属于允许操作。
- 引用清理不删除远端分支；如误删本地跟踪引用，应从已核验 remote 重新 fetch，而不是创建猜测 SHA。
- 不同 `repo` 版本的内部布局可能变化，新 SDK 首次执行前须重新做只读枚举。

## Review

- owner：leiwenjun
- review_after：2026-11-15
- 下一次复核：新 SDK 的 `repo` 版本、引用布局、manifest 固定点和清理前后精确计数。
