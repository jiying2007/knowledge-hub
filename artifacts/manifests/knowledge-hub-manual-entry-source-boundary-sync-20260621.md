# Knowledge Hub manual entry and source boundary sync 2026-06-21

## 结论

本轮修复人工新增入口和 source 边界说明的可读性漂移：

- `knowledge-new.sh` 现在能为 `debug-record`、`external-source-note`、`owner-decision-worksheet`、`patent-disclosure` 和 `migration-record` 选择专用模板，并保留常用别名。
- `tools/knowledge-regression.sh` 的 `manual-entry-template-selection` 已覆盖这些 kind，防止后续回退到 `templates/item.md`。
- `README.md`、`tools/README.md` 和 `templates/README.md` 已补中文维护入口，明确 `owner-decision-worksheet` 只是人工签核草稿，不生成 owner decision、不代签、不关闭 gate。
- `governance/source-boundaries.md` 已从旧 6 类 source 摘要升级为当前 13 个 registered sources 的中文边界入口，PCR02 Level 2 七类 source 的禁止事项单独写清。

## 范围

| 文件 | 动作 |
|---|---|
| `tools/knowledge-new.sh` | 补齐 kind 到模板的映射和别名 |
| `tools/knowledge-regression.sh` | 扩展人工入口模板选择回归 |
| `README.md` | 增加常用专用模板命令 |
| `tools/README.md` | 增加场景化命令示例 |
| `templates/README.md` | 改为 kind -> template 映射表 |
| `governance/source-boundaries.md` | 更新为 13 个 source 的中文治理边界 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不生成 owner decision | enforced |
| 不关闭 owner gate | enforced |
| 不修改 PCR02 源项目 | enforced |
| 不复制 source 正文 | enforced |
| 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/` | enforced |
| 不启用自动化写操作 | enforced |
| 不写 `~/.codex/memories` | enforced |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `manual-entry-template review` | 0 | 发现 `debug-record`、`external-source-note`、`owner-decision-worksheet`、`patent-disclosure` 会 fallback 到 `templates/item.md`，并建议补回归和 README 示例 | subagent `019eea8e-ea37-7c43-9fdc-18ee07b95136` | Subagent evidence | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| subagent `source-boundary drift review` | 0 | 发现 `governance/source-boundaries.md` 仍停留在旧 6 类 source，缺少 13 个 source 和 PCR02 Level 2 边界 | subagent `019eea8f-40c6-7aa3-809c-2f3f76c53f39` | Subagent evidence | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| `rtk bash tools/knowledge-new.sh --kind debug-record --domain governance --id governance-template-debug-record --path artifacts/manifests/governance-template-debug-record.md` | 0 | 输出 `推荐模板: templates/debug-record.md` | `tools/knowledge-new.sh` | Smoke | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| `rtk bash tools/knowledge-new.sh --kind owner-decision-worksheet --domain governance --id governance-template-owner-decision-worksheet --path artifacts/manifests/governance-template-owner-decision-worksheet.md` | 0 | 输出 `推荐模板: templates/owner-decision-worksheet.md`，仍只是人工签核草稿入口 | `tools/knowledge-new.sh` | Smoke | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-21` | 0 | 73 个回归场景通过，包含 `manual-entry-template-selection` | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-21` | 0 | 全仓知识门禁 pass，0 errors / 0 warnings | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |
| `rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-21` | 1 | `final_status=needs-owner-review`，自动治理 `complete-except-owner-review`，只剩 7 个 owner gate blocker | `tools/knowledge-final-gate.sh` | Final gate | `knowledge-hub-manual-entry-source-boundary-sync-20260621` |

## 下一步

- owner gates 仍保持 open，等待真实 owner decision。
