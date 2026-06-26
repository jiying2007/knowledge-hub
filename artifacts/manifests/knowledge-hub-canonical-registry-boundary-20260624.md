# Knowledge Hub canonical registry 边界加固 2026-06-24

## 摘要

本次收敛硬切换后的 current registry 和 governance 文档边界：`registry/topics.json`、`registry/retention.json` 和当前治理说明不再把旧项目/个人目录作为长期入口。

## 变更范围

- `registry/topics.json`：项目 topic 指向 `projects`，个人 topic 指向 `notes/personal`。
- `registry/retention.json`：个人保留策略指向 `notes/personal`。
- `governance/ultimate-maintenance-plan.md`：权威等级改为 `projects/<project>/...` 与 `notes/personal/`。
- `governance/implementation-roadmap.md`：项目 docs 与工程归档迁移目标改为 `projects/`。
- `governance/glossary.md`：PCR02 项目术语边界改为 `projects/pcr02/`。
- `tools/knowledge-check.sh`：topic registry 和 retention rules 中的旧项目/个人入口变为硬错误。
- `tools/knowledge-regression.sh`：新增负向回归，证明旧入口回灌会失败。

## 边界

- 历史 manifest、历史 provenance record 和迁移前证据仍可保留旧路径文本。
- 本次未修改源项目。
- 本次未写 `~/.codex/memories`。
- 本次未生成 owner decision。
- 本次未提升 active。
- 本次未启用非 report-only 自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-06-24` | 0 | `status=pass`，errors=0，warnings=0；registry topic/retention canonical 边界通过。 | runtime:knowledge-check | Governance | `knowledge-hub-canonical-registry-boundary-20260624` |
| `rtk bash tools/knowledge-regression.sh --json --as-of 2026-06-24` | 0 | `status=pass`，新增 canonical registry 负向回归随全量场景通过。 | runtime:knowledge-regression | Governance | `knowledge-hub-canonical-registry-boundary-20260624` |
