# Knowledge Hub source coverage closeout 2026-06-24

## 摘要

本 closeout 是 `knowledge-hub-simplified-final-version.md` 硬切换后的 source 覆盖矩阵。它把 Knowledge Hub 从旧的 PCR02 专项治理面扩展为 Hub 主库：

- 已登记 source 数量：18。
- 新增 Hub 主库来源：`codex-history`、`codex-raw-sessions`、`codex-session-index`、`codex-archive-registry`、`knowledge-hub-automation-runs`。
- 迁移口径：治理全覆盖，不复制全部正文。
- raw history、raw sessions、binary、源码、日志和制品只做引用、摘要、hash、artifact-ref 或 archive-only。
- AI / Codex 高风险动作必须引用 `registry/authorizations.jsonl`。

## 边界

- 本文件不生成 owner decision。
- 本文件不提升 active。
- 本文件不写 `~/.codex/memories`。
- 本文件不修改源项目。
- 本文件不执行非 `report-only` 自动化。
- 本文件不把 raw session 或 memory candidate 写成 current fact。

## 证据

- 结构化矩阵：`artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- Source registry：`registry/sources.json`
- Source index：`indexes/by-source.md`
- 授权账本：`registry/authorizations.jsonl`
- 自动化运行账本：`registry/automation-runs.jsonl`

## 验证

```bash
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-index-plan.sh --section source --json
rtk bash tools/knowledge-final-gate.sh --json
```
