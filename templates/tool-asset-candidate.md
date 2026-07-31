---
schema: knowledge-hub.tool-asset-candidate.v1
id: <导入时生成>
title: 工具资产候选
kind: validation
domain: projects/<project>
path: projects/<project>/validation/tool-asset-candidate-<date>-<name>.md
scope: project-specific
visibility: team-internal
owner: <registered-owner>
source:
  type: tool-asset-candidate
  from: <source_repo>@<source_commit>:<candidate_source_path>#<candidate_sha256>
review_after: <YYYY-MM-DD>
created_at: <YYYY-MM-DD>
updated_at: <YYYY-MM-DD>
promotion: none
promotion_decision: none; pending human review
tags: [tool-asset, candidate, validation]
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
review_status: automated-candidate-pending-human-review
evidence_strength: source-identity-and-offline-validation-summary
evidence_refs: []
generated_by_ai: false
ai_role: none
ai_model_or_tool: none
ai_generated_at: none
human_reviewed_by: none
human_reviewed_at: none
review_basis: pending
source_repo: <registry/repositories.json 中的 repo_id、remote_key 或 alias>
source_commit: <7-64 位小写十六进制 Git commit>
source_worktree_dirty: true
source_identity_verified: true
candidate_name: <稳定的 kebab-case 工具名>
candidate_source_path: codex_assets/<relative-path>
candidate_sha256: <源码资产 SHA256>
candidate_hash_scope: single-file
candidate_file_count: 1
candidate_score: 0
recommendation: keep-project-tool
recommended_target: 项目 codex_assets
validation:
  unit_tests: not-run
  cli_help: not-run
  dry_run: not-run
  non_repo_cwd: not-run
sanitization:
  endpoint_removed: true
  credentials_found: false
  raw_logs_archived: false
status: reviewing
summary_zh: <说明工具解决的问题、适用范围和当前结论，不复制源码>
risks_zh: <兼容性、维护、依赖或误用风险>
blockers_zh: <人工评审前仍需解决的问题；没有则写“无”>
---

# 工具资产候选

此文件由源仓候选检测器生成，仅作为 Hub 导入输入。正文可补充简短说明，但导入器只持久化经过白名单规范化的 front matter 字段，不复制本正文、源码、raw log、core、二进制、现场端点或凭证。
