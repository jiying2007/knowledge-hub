# Knowledge Hub manual recovery and boundary hardening 2026-06-21

## 结论

本轮把三个子代理发现的可自动修复 gap 收敛为人工入口和项目边界加固：

- 新会话恢复入口补充 HEAD、branch 和 worktree 状态命令，防止旧 handoff 被误当当前事实。
- `knowledge-new.sh --source` 增加 source 枚举速查和已传入枚举预校验；`project-archive` / `archive-note` 的 registry 与 status index 草稿默认使用 `archived`。
- 高频模板补可选 `manual_validation_pending` 块，离线手工维护时能保留 pending 原因、followup 命令、owner 和 review_after。
- PCR02 “第三方库引用基线”迁移副本补项目边界提示，明确不是团队级标准，不进入 `domains/embedded/standards/`。
- `indexes/by-source.md` 增加 PCR02 source 边界速查，人工恢复 owner、review_after 和 final_disposition 时不必只依赖全量 JSON。

## 范围

| 文件 | 动作 |
|---|---|
| `AGENTS.md` | 明确不得生成 owner decision、关闭 owner gate 或把 owner-ready 当签收 |
| `README.md` | 新会话恢复命令补 HEAD、branch/worktree 状态 |
| `tools/README.md` | 搜索和恢复入口补 HEAD、branch/worktree 状态 |
| `tools/knowledge-new.sh` | 补 source 枚举速查/预校验；归档类草稿默认 `archived` |
| `tools/knowledge-regression.sh` | 新增归档默认状态、离线模板占位、source 枚举速查回归 |
| `templates/*.md` | 高频模板补可选离线待验证块 |
| `domains/projects/pcr02/current/third-party-libraries-reference.md` | 补 PCR02 project-only 边界说明 |
| `indexes/by-source.md` | 补 PCR02 source 边界速查和本 manifest 入口 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不生成 owner decision | enforced |
| 不关闭 owner gate | enforced |
| 不修改 PCR02 源项目 | enforced |
| 不复制 owner-gated source 正文 | enforced |
| 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/` | enforced |
| 不启用自动化写操作 | enforced |
| 不写 `~/.codex/memories` | enforced |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `cross-session-restore-audit` | 0 | 发现恢复入口缺 HEAD/branch/worktree 状态、AGENTS 未显式写 owner gate 不得关闭 | subagent `019eeaa2-c7f8-71b1-a8be-f1ecea22f52d` | Subagent evidence | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| subagent `cross-project-linking-audit` | 0 | 确认机器边界 pass，建议补 PCR02 “standard/基线”项目边界提示和 source 主索引可读摘要 | subagent `019eeaa3-269f-7d10-a1d8-1bfb9e9e5b6a` | Subagent evidence | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| subagent `offline-manual-maintenance-audit` | 0 | 发现归档类草稿默认 reviewing、模板缺离线 pending 占位、source 枚举需速查 | subagent `019eeaa3-8055-78b3-891d-13bdd44fd7a8` | Subagent evidence | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-new.sh --kind project-archive --domain projects/pcr02 --owner team-core --id pcr02-archive-status-default --path domains/projects/pcr02/archive/status-default.md` | 0 | 输出 `status=archived` 和 `indexes/by-status.md` archived bucket 草稿 | `tools/knowledge-new.sh` | Smoke | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id example-source-enum --source-path /tmp/example-enum --role project-current-docs-source --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "classify-first pending source coverage"` | 0 | 输出 source 枚举速查并通过已传入枚举预校验 | `tools/knowledge-new.sh` | Smoke | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-new.sh --source --source-id bad-source-enum --source-path /tmp/bad-enum --role bad-role --authority legacy-project-current-docs --write-policy read-only-unless-explicitly-approved --no-check-reason "classify-first pending source coverage"` | 2 | 非法 `role` 被 source enum 预校验阻断 | `tools/knowledge-new.sh` | Negative smoke | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-21` | 0 | 76 个回归场景全部 pass，包含归档默认状态、离线模板占位和 source enum 速查/非法枚举阻断 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-21` | 0 | 全仓知识门禁通过，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk git diff --check` | 0 | 无 whitespace 或 conflict marker 问题 | Git | Diff check | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-21` | 1 | `final_status=needs-owner-review`，自动治理 `complete-except-owner-review`，唯一 blocker 是 7 个 owner gate open | `tools/knowledge-final-gate.sh` | Final gate | `knowledge-hub-manual-recovery-boundary-hardening-20260621` |

## 下一步

- 继续保留 7 个 PCR02 owner gate open，等待真实 owner decision。
- 后续如新增 source，优先使用 `knowledge-new.sh --source` 输出的枚举速查与 `registry/schema.md` 对齐。
