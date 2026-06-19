# Knowledge Hub Registry Enum Gate - 2026-06-19

## 摘要

本次修复把 registry schema 中的受控枚举纳入 `knowledge-check`，防止 `registry/items.jsonl` 和 `registry/sources.json` 出现拼写漂移、未审查新状态词或兼容性不明的新分类。

本 manifest 是治理门禁记录，不是内容迁移；不修改源项目 docs，不写 memory，不启用自动化，不提升任何 owner-gated 条目。

## 问题地图

| ID | 发现 | 级别 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| KHD-20260619-009 | `registry/schema.md` 已声明 item `kind/status` allowed values，但 `knowledge-check` 未校验。 | P1 | 只读扫描显示当前值合法，但未来拼错不会被拦截。 | 已加入 `kind/status` enum 检查。 |
| KHD-20260619-010 | `registry/sources.json` 的 `role/authority/status/write_policy` 是实际受控词，但 schema 未列出 allowed values。 | P1 | 当前只有 6 个 source，值集合稳定且承担边界语义。 | 已在 schema 写明 allowed values，并加入 `knowledge-check` 校验。 |
| KHD-20260619-011 | 未审查的新 source write policy 可能放宽写入边界。 | P1 | Knowledge Hub 原则要求 source 不被直接写穿，自动化默认 report-only。 | `write_policy` 必须在白名单内。 |

## 已改内容

- `tools/knowledge-check.sh`
  - 校验 item `kind` 与 `status`。
  - 校验 source `role`、`authority`、`status`、`write_policy`。
- `registry/schema.md`
  - 补充 source `role`、`authority`、`status`、`write_policy` allowed values。
- `tools/README.md`
  - 说明 `knowledge-check.sh` 已覆盖 registry/source enum checks。

## 验证

已执行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json
rtk bash tools/knowledge-search.sh "registry-enum-gate-applied" --json
rtk git diff --check
```

负向样例：

```bash
rtk bash -lc 'tmp=/tmp/knowledge-hub-registry-enum-test; rm -rf "$tmp"; cp -a . "$tmp"; cd "$tmp"; rtk python3 -c "from pathlib import Path; p=Path(\"registry/items.jsonl\"); text=p.read_text(); p.write_text(text.replace(\"\\\"status\\\":\\\"reviewing\\\"\", \"\\\"status\\\":\\\"reviewing-typo\\\"\", 1))"; bash tools/knowledge-check.sh --dry-run --json'
```

预期结果：

- 当前仓库 `knowledge-check` 返回 `pass`，无 errors/warnings。
- 临时副本负向样例返回 `fail`，错误包含 `invalid status: reviewing-typo`。

## 剩余风险

- `scope`、`visibility`、`domain` 目前仍是半开放字段；后续需要单独定义 domain/scope/visibility 契约后再加入门禁。
- 新增 source role、authority 或 write_policy 时，需要先更新 `registry/schema.md` 和 `tools/knowledge-check.sh`，再登记 migration。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`registry-enum-gate-applied`
- promotion：`none`
- review_after：`2026-09-19`
