# Project: Knowledge Hub

- 根目录：`/home/leiwenjun/knowledge-hub`
- 控制面：manifest、registry、index、read-only tooling。
- 当前 owner gate 状态：PCR02 7 条 owner decision worksheet 仍需人工签收。

## 关键边界

- 所有 shell 命令必须使用 `rtk`。
- 手工修改必须使用 `apply_patch`。
- 子 agent 默认只读，主 agent 串行整合。
- 自动化默认 `report-only`。
- `.session`、handoff、memory candidates 不能进入 active facts。

## 本轮写入范围

- `.codex/20260620-owner-forms-jsonl/`
- `issues/20260620-owner-forms-jsonl.csv`
- `tools/knowledge-owner-gates.sh`
- `tools/knowledge-regression.sh`
- `tools/README.md`
- `artifacts/manifests/knowledge-hub-governance-regression-helper-20260619.md`
- `artifacts/manifests/knowledge-hub-owner-forms-jsonl-only-20260620.md`
- `artifacts/manifests/knowledge-hub-owner-forms-jsonl-only-20260620.jsonl`
- `registry/items.jsonl`
- `registry/migrations.jsonl`
- `indexes/by-owner.md`
- `indexes/by-review-date.md`
- `indexes/by-status.md`
- `indexes/by-topic.md`

## 禁止写入

- 源项目 docs。
- `domains/embedded/standards/`。
- `~/.codex/memories`。
- `/home/leiwenjun/codex` 中既有未相关变更。
