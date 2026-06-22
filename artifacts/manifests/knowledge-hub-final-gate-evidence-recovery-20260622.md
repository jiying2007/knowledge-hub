# Knowledge Hub Final Gate Evidence Recovery 2026-06-22

## 摘要

本次收口面向终态失败后的证据追溯和中文恢复路径，压实三个可自动完成的治理切片：

- `knowledge-final-gate.sh --json` 增加命令级 `evidence_index[]`，记录 `knowledge-check`、`knowledge-regression`、`rtk git diff --check`、`knowledge-status --strict` 的 command、exit_code、status、中文摘要、runtime evidence path 和 related artifact。
- `knowledge-status.sh --strict --json` 增加 `owner_blocker_source`，并在 `owner-gates-open` blocker 内镜像该结构，说明 owner gate 数量、owner-ready 覆盖和 active exposure 来自 `owner_gates` 的哪些字段。
- README、tools README 和 indexes README 增加终态失败恢复决策树、owner-blocker provenance 和 source coverage latest closeout 恢复规则，降低中文维护者跨文档拼装路径的成本。

## 改动范围

| 文件 | 改动 |
|---|---|
| `tools/knowledge-final-gate.sh` | 增加 `evidence_index[]`、`owner-blocker-provenance` 证据行，并优先镜像 status 输出的 owner blocker provenance。 |
| `tools/knowledge-status.sh` | 增加顶层 `owner_blocker_source`，并在 `owner-gates-open` strict blocker 中携带同一 provenance。 |
| `tools/knowledge-regression.sh` | 锁定 final gate evidence index、owner blocker provenance 和 status provenance 输出契约。 |
| `README.md` | 增加终态失败恢复决策树，并说明 `evidence_index[]` 和 `owner-blocker-provenance`。 |
| `tools/README.md` | 补 final gate evidence index、失败分类和 owner handoff 恢复顺序。 |
| `indexes/README.md` | 补 source coverage latest closeout 选择恢复规则。 |
| `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md` | 同步 final gate owner-review 场景说明和 evidence index 覆盖描述。 |

## 边界

- 不生成 owner decision。
- 不关闭任何 owner gate。
- 不修改 PCR02 源项目文件。
- 不复制 owner-gated source 正文。
- 不提升 PCR02 project-specific 内容到 `domains/embedded/standards/`。
- 不启用自动化写操作。
- 不写 `~/.codex/memories`。

## 验证计划

```bash
rtk bash -n tools/knowledge-status.sh
rtk bash -n tools/knowledge-final-gate.sh
rtk bash -n tools/knowledge-regression.sh
rtk bash tools/knowledge-status.sh --strict --json --as-of 2026-06-22
rtk bash tools/knowledge-final-gate.sh --json --as-of 2026-06-22
rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-22
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-22
rtk git diff --check
```

## 当前阻塞

本轮只提高 final gate 证据可追溯性和失败恢复可读性。终态仍应停在 `needs-owner-review`，且唯一 blocker 应继续是 `owner-gates-open`；7 个 PCR02 owner gate 不能由 Codex 代签。
