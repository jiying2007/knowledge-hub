# Knowledge Hub Index Path Gate - 2026-06-19

## 摘要

本次修复把 `indexes/*.md` 中的本地路径引用纳入 `knowledge-check`，防止导航索引保留失效 manifest、domain、registry、tool、template 或 governance 路径。

本 manifest 是治理门禁记录，不是内容迁移；不修改源项目 docs，不写 memory，不启用自动化，不提升任何 owner-gated 条目。

## 问题地图

| ID | 发现 | 级别 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| KHD-20260619-006 | `indexes/*.md` 中的本地路径引用没有门禁，文件重命名或删除后可能留下残留导航。 | P1 | 只读扫描发现 97 个本地路径型引用；旧 `knowledge-check` 未校验这些路径。 | 已加入本地路径和 glob 引用检查。 |
| KHD-20260619-007 | `indexes/by-source.md` 有一个 code span 同时包含多个路径，无法被机器可靠校验。 | P2 | `registry/items.jsonl; registry/migrations.jsonl; indexes/by-*.md` 被识别为一个复合引用。 | 已拆成独立 code span，并保留中文顿号连接。 |
| KHD-20260619-008 | `indexes/by-topic.md` 使用 `domains/projects/*/current` 与 `domains/projects/*/archive` 这类 glob 导航。 | P2 | glob 当前能匹配 `domains/projects/pcr02/current` 和 `domains/projects/pcr02/archive`。 | 门禁支持 glob，要求至少匹配一个本地路径。 |

## 已改内容

- `tools/knowledge-check.sh`
  - 扫描所有 `indexes/*.md`。
  - 对 `artifacts/`、`domains/`、`registry/`、`indexes/`、`governance/`、`tools/`、`templates/`、`README.md`、`AGENTS.md` 的 code span 执行本地路径校验。
  - 普通路径必须存在；含 `*` 的 glob 必须至少匹配一个路径。
- `indexes/by-source.md`
  - 将复合 code span 拆成三个独立可校验引用。
- `tools/README.md`
  - 说明 `knowledge-check.sh` 覆盖 index local path/glob reference checks。

## 验证

已执行：

```bash
rtk bash tools/knowledge-check.sh --dry-run --json
rtk bash tools/knowledge-search.sh "index-path-gate-applied" --json
rtk git diff --check
```

负向样例：

```bash
rtk bash -lc 'tmp=/tmp/knowledge-hub-index-path-test; rm -rf "$tmp"; cp -a . "$tmp"; printf "\n- Bad path: \`artifacts/manifests/not-exist.md\`\n" >> "$tmp/indexes/by-topic.md"; cd "$tmp"; bash tools/knowledge-check.sh --dry-run --json'
```

预期结果：

- 当前仓库 `knowledge-check` 返回 `pass`，无 errors/warnings。
- 临时副本负向样例返回 `fail`，错误包含 `missing local path reference artifacts/manifests/not-exist.md`。

## 剩余风险

- 外部绝对路径由 `registry/sources.json` 管理，本次门禁不校验普通索引中的外部绝对路径。
- `pcr02-project-docs/...` 这类 source-relative 伪路径仍作为源标识，不按本地路径校验。

## Review

- owner：`leiwenjun`
- status：`reviewing`
- review_status：`index-path-gate-applied`
- promotion：`none`
- review_after：`2026-09-19`
