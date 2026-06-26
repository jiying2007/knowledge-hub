# Knowledge Hub source 主控目录统一收口 2026-06-24

## 结论

本轮把 `registry/sources.json` 中 18 个 registered source 全部落到 Hub 内 `sources/<source_id>/` 主控目录，并补齐 PCR02 owner 决策中允许落地的 4 个目标正文。

统一管理面的含义是：每个 source 在 Hub 内都有 `README.md`、`inventory.jsonl`、`coverage.md` 和 `source-policy.md`，用于说明来源、覆盖状态、迁移边界和后续复核路线；不等于把 Codex history、raw session、source code、binary、log 或外部目录全文复制进长期正文层。

## 本轮落地

- 建立 18 个 `sources/<source_id>/` 主控目录，每个目录 4 个控制文件，共 72 个文件。
- materialize PCR02 owner-approved target：
  - `projects/pcr02/current/runbooks/asan-debug-guide.md`
  - `projects/pcr02/archive/plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md`
  - `projects/pcr02/archive/reports/2026-05-29-motor-mcu-debug-record.md`
  - `projects/pcr02/archive/reports/2026-06-16-dvr-record-replay-session-archive.md`
- 为 `sources/pcr02-project-docs/inventory.jsonl` 增加 4 条目标覆盖行。
- 为 `knowledge-check` 增加 source 主控目录、source inventory、raw dump 安全和 owner target 存在性检查。
- 为 `knowledge-regression` 增加删除 source 控制文件、raw copy-body 和 owner target 缺失的负向 fixture。

## 边界

- 不修改 PCR02 源项目 docs。
- 不写 `~/.codex/memories`。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不自动生成 owner decision，不代填 `reviewed_by`。
- 不提升 active，不自动关闭 owner gate。
- 不复制 Codex raw session/history/source-code/binary/log 全文到正文层。
- 自动化仍默认 report-only；非 report-only 操作需要授权账本记录。

## 验证入口

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-24
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json --as-of 2026-06-24
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --as-of 2026-06-24
```

## 后续人工维护

新增或调整 source 时，先更新 `registry/sources.json`，再运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-source-control.sh --apply --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

如果 source 中存在 raw session、history、source code、binary 或 log，只能在 inventory 中登记为 `summary-only`、`artifact-ref`、`reference-only`、`archive-only` 或 `exclude`，不得使用 `copy-body`。
