# Knowledge Hub 实施路线图

## Phase 0: Bootstrap

- 创建目录骨架。
- 落盘 `README.md`、`AGENTS.md`、governance 文档、registry schema 和初始 sources。
- 实现只读工具 stub。

验收：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
```

## Phase 1: Source Registration

- 登记现有来源，不移动正文。
- 生成 `registry/sources.json`。
- 建立 `indexes/by-source.md`。

## Phase 2: Tooling Baseline

- 完成 `knowledge-check.sh`。
- 完成 `knowledge-search.sh`。
- 完成 capture/promote/retire 的 dry-run 安全入口。

## Phase 3: Project Docs Externalization

- 将项目仓 docs 正文迁入 `domains/projects/<project>/current/` 和 `archive/`。
- 项目仓仅保留 `docs/README.md`。
- 写入 `registry/migrations.jsonl`。

## Phase 4: Engineering Archive Migration

- 将 `~/embedded/engineering_archive` 按 project/domain 迁入 `domains/projects/*/archive/`。
- `decision-index.md` 迁入 `decisions/index.md`。
- 保留旧路径直到校验完成。

## Phase 5: Team Knowledge Migration

- 将 `~/embedded/knowledge/docs/standards` 等通用内容迁入 `domains/embedded/`。
- 工具和 skill 迁入或挂接到 `domains/embedded/tools`、`skills`。

## Phase 6: Codex Automation Integration

- 在 `~/codex/manifests` 登记 workflow、recipe、automation 和 slash contract。
- 所有 automation 默认为 disabled/report-only。
- 前三次运行必须人工复审。
