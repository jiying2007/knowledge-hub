# Knowledge Hub 实施路线图

## Phase 0: Bootstrap

- 创建目录骨架。
- 落盘 `README.md`、`AGENTS.md`、governance 文档、registry schema 和初始 sources。
- 实现只读工具 stub。

验收：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

## Phase 1: Source Registration

- 登记现有来源，不移动正文。
- 生成 `registry/sources.json`。
- 建立 `indexes/by-source.md`。

## Phase 2: Tooling Baseline

- 完成 `knowledge-check.sh`。
- 完成 `knowledge-search.sh`。
- 完成 capture/promote/retire 的 dry-run 安全入口。

## Phase 3: Project Docs Canonicalization

- 项目知识正文只落到 `projects/<project>/current/`、`projects/<project>/decisions/`、`projects/<project>/validation/` 和 `projects/<project>/archive/`。
- 源项目仅保留本项目运行所需的本地说明和 Git 管理文件。
- 更新 `registry/items.jsonl`、`registry/sources.json`、`sources/<source_id>/source-policy.md` 和核心索引。

## Phase 4: Engineering Archive Canonicalization

- 将 `engineering-archive` source 按 project/domain 归入 `projects/*/archive/`，source control 入口统一为 `sources/engineering-archive`。
- `decision-index.md` 归入 `decisions/index.md` 或对应项目决策索引。
- 旧路径只允许作为 `origin_path` provenance，不作为 active source、默认查询入口、fallback 或新增归档目的地。

## Phase 5: Team Knowledge Canonicalization

- 将 `embedded-knowledge` source 中的通用内容归入 `domains/embedded/`，source control 入口统一为 `sources/embedded-knowledge`。
- 工具和 skill 只登记 canonical 说明、artifact-ref 或 source policy；不复制不安全 raw 正文。

## Phase 6: Codex Automation Integration

- 在 `~/codex/manifests` 登记 workflow、recipe、automation 和 slash contract。
- 所有 automation 默认为 disabled/report-only。
- 前三次运行必须人工复审。
