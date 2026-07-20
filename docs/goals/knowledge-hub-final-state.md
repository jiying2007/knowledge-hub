# Knowledge Hub 终态目标历史记录

> 归档身份：registry item `knowledge-hub-final-state-goal-20260620` 的状态为 `archived`。本文件只保存当时的目标与验收口径，不是当前执行入口；当前产品边界见 `README.md`，当前证据状态见 `governance/product/validation/project-readiness.md`。

## 历史目标摘要

Knowledge Hub 的当前定位：

```text
Knowledge Hub = Obsidian-friendly Markdown Vault + 最小 registry 账本 + 高风险治理门禁
```

当前 canonical 目录：

- `projects/<project>/`：项目知识唯一主入口。
- `domains/`：跨项目领域知识。
- `notes/`：普通笔记和个人笔记。
- `sources/`：source 控制面，每个 registered source 至少包含 `README.md`、`inventory.jsonl`、`coverage.md` 和 `source-policy.md`。
- `registry/`：最小机器账本。
- `indexes/`：可重建导航。
- `artifacts/manifests/`：高风险治理证据包。
- `templates/`、`governance/`、`tools/`：人工维护、治理规则和门禁工具。

不再维护迁移账本、旧 source tombstone 或旧 hard-migration 入口。旧外部路径只允许作为
`registry/sources.json` 的 `origin_path` provenance、历史 Git 记录或历史 manifest 证据出现；
不得作为新增内容入口、默认查询入口、fallback 或新增归档目的地。

## 完成标准

- `knowledge-check` 能证明 registry、source control、owner target、raw dump safety 和边界健康。
- `knowledge-regression` 覆盖当前工具、schema、source control、review queue、owner gate 和 final gate 契约。
- `knowledge-final-gate --json --final-profile product` 是唯一终态入口，分别输出 `platform_status`、`content_readiness`、`retrieval_quality`、`operational_readiness`、`delivery_readiness`、`overall_status`、`local_delivery_complete`、`remote_published`、`offsite_restore_verified`、`adoption_ready` 和 `terminal`。
- 平台技术候选完成要求 `gate_status=pass`、全部 technical hard checks 通过；本地交付完成还要求 clean committed HEAD、tracked dependency manifests、full regression 和 HEAD `git archive` restore。远端发布和异地恢复分别由远端 push 与独立运行环境的签名证据判定，三者不能混为同一声明。
- 真实 owner/evidence 未闭环时必须保持 `overall_status=needs-owner-review`，不能用候选文档、30/30 source mapping 或治理通过冒充成熟。
- 全面产品终态声明要求 `--regression-suite full --require-terminal` 退出 0，且 `local_delivery_complete`、`remote_published`、`offsite_restore_verified`、`adoption_ready`、`terminal` 全部为 `true`、`overall_status=mature`；未达到时结论必须保守降级。
- 旧入口精确扫描不命中当前文档、registry、index、template、tool 或 source control。

## 验证命令

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-regression.sh
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
rtk git diff --check
```

## 边界

- 不修改源项目，除非当前用户或项目 owner 明确授权并给出 scope。
- 不写 `~/.codex/memories`。
- 不代签 owner decision，不自动关闭 owner gate。
- 不提升 active，不发布、不 push、不 merge、不 tag，除非有明确授权、证据和回滚路径。
- 不把项目特定内容提升到 `domains/embedded/standards/`。
- 不把 raw session、history、source code、binary、log 或 secret-like config 作为正文复制进知识层。
