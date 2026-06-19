# Knowledge Hub Registry Boundary Gate - 2026-06-19

## 摘要

本次修复把 registry item 的 `scope`、`visibility`、`domain` 与 `path` 边界纳入 `knowledge-check`，防止条目落错 domain、项目内容越界、Codex memory governance 混入非 Codex domain，或未来出现未审查的新 scope/visibility。

本 manifest 是治理门禁记录，不是内容迁移；不修改源项目 docs，不写 memory，不启用自动化，不提升任何 owner-gated 条目。

## 问题地图

| ID | 发现 | 级别 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| KHD-20260619-012 | `scope` 和 `visibility` 是边界字段，但未被 allowed values 校验。 | P1 | 当前实际值为 `team-general`、`project-specific`、`codex-memory-curation-governance` 和 `team-internal`。 | 已加入 scope/visibility 白名单。 |
| KHD-20260619-013 | `domain` 决定知识权威边界，但未校验 domain root。 | P1 | 当前实际 domain root 为 `root`、`governance`、`projects`、`codex`。 | 已加入 Knowledge Hub 声明边界的 domain root 白名单。 |
| KHD-20260619-014 | `domain` 与 `path` 可以漂移，例如 project-specific 条目落到治理路径或 embedded standard。 | P1 | 现有 project control-plane manifest 使用 `artifacts/manifests/`，正文使用 `domains/projects/pcr02/`。 | 已加入 domain/path 对应关系检查。 |
| KHD-20260619-015 | `codex-memory-curation-governance` scope 必须绑定 `codex` domain。 | P1 | `memory-auto-curation-report-only-governance-20260618` 当前 domain 为 `codex`。 | 已加入 scope/domain 关系检查。 |

## 已改内容

- `tools/knowledge-check.sh`
  - 校验 item `scope`、`visibility`。
  - 校验 domain root。
  - 校验 domain/path 对应关系。
  - 校验 `project-specific` scope 必须使用 `projects/<project>` domain。
  - 校验 `codex-memory-curation-governance` scope 必须使用 `codex` domain。
- `registry/schema.md`
  - 补充 allowed `scope`、`visibility`、domain roots 和 domain/path invariants。
- `tools/README.md`
  - 说明 `knowledge-check.sh` 已覆盖 domain-boundary checks。

## 验证

已执行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json
rtk bash tools/knowledge-search.sh "registry-boundary-gate-applied" --json
rtk git diff --check
```

负向样例：

```bash
rtk bash -lc 'tmp=/tmp/knowledge-hub-registry-boundary-test; rm -rf "$tmp"; cp -a . "$tmp"; cd "$tmp"; rtk python3 -c "from pathlib import Path; p=Path(\"registry/items.jsonl\"); text=p.read_text(); p.write_text(text.replace(\"\\\"domain\\\":\\\"projects/pcr02\\\"\", \"\\\"domain\\\":\\\"governance\\\"\", 1))"; bash tools/knowledge-check.sh --dry-run --json'
```

预期结果：

- 当前仓库 `knowledge-check` 返回 `pass`，无 errors/warnings。
- 临时副本负向样例返回 `fail`，错误包含 project-specific scope outside projects domain。

## 剩余风险

- `team-general` scope 当前允许 `root`、`governance` 等控制面条目；未来若新增 `embedded` 或 `patents` 正文条目，需要进一步细化 scope/domain 矩阵。
- `visibility` 目前只使用 `team-internal`，但保留 `personal-local` 作为已声明边界；真正引入 personal item 时仍需补 active index 禁止项验证。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`registry-boundary-gate-applied`
- promotion：`none`
- review_after：`2026-09-19`
