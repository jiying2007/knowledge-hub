# Embedded Domain

本目录是 Knowledge Hub 的嵌入式团队级知识域，沉淀跨项目可复用技术文档、排障 runbook、平台知识、调试工具与 Codex skill。

## 首次使用

团队成员统一使用 Knowledge Hub 终态入口：

```text
~/knowledge-hub/domains/embedded
```

验证：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "embedded" --json --limit 10
```

常用入口：

- 团队规范：`standards/`
- 排障 runbook：`runbooks/`
- 平台和架构知识：`platform/`、`architecture/`
- 技能和工具说明：`skills/`、`tools/`
- 模板和治理规则：`templates/`、`governance/`

## 目录

- `standards/`：团队级规范和跨项目规则。
- `runbooks/`：排障、验证、发布和工具使用流程。
- `architecture/`、`platform/`：平台能力、系统架构和设计知识。
- `skills/`、`tools/`：可复用技能和工具说明。
- `templates/`、`governance/`：模板、命名、证据和治理规则。

结构边界见 `standards/repository-structure-guide.md`。

## 本地门禁

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
```

如果需要恢复历史来源、迁移证据或 owner 边界，优先查看 `sources/embedded-knowledge/`、`registry/source-tombstones.jsonl` 和 `indexes/by-source.md`。

## Codex Skills

```bash
rtk bash scripts/install-codex-skills.sh --dry-run
rtk bash scripts/install-codex-skills.sh
```

## 个人开发工具

```bash
rtk bash scripts/check-tools.sh
rtk bash scripts/bootstrap-dev-tools.sh
```

安装缺失工具：

```bash
rtk bash scripts/bootstrap-dev-tools.sh --install
```

新增文档：

```bash
rtk bash scripts/new-doc.sh --type runbook --title "示例 Runbook" --out docs/runbooks/example-runbook.md
```

新增技能：

```bash
rtk bash scripts/new-skill.sh --name example-triage --description "示例分诊技能" --scope tools
```

## 发布

```bash
rtk bash scripts/generate-release-manifest.sh --root out/arm/app --out out/arm/app/release-manifest.csv
rtk bash scripts/check-release-manifest.sh --manifest out/arm/app/release-manifest.csv --root out/arm/app
rtk bash scripts/release.sh --date 2026-05-17
```

## 迁移记录

- 首版来源项目 commit：`899da6b5`
- 迁移映射：`docs/governance/knowledge-repo-migration-map.csv`
- 项目强绑定文档保留在来源项目仓，仅通用知识、平台知识与公共工具进入本仓。

## 远程

目标远程仓库：

```text
source://embedded-knowledge
```
