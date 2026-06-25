# Embedded Knowledge Base

本仓库是嵌入式研发团队知识库，沉淀可复用技术文档、排障 runbook、平台知识、调试工具与 Codex skill。

## 首次使用

团队成员本机统一放置在：

```text
~/embedded/knowledge
```

初始化：

```bash
mkdir -p ~/embedded
git clone ssh://git@192.168.1.4:10022/embedded/knowledge.git ~/embedded/knowledge
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

验证：

```bash
cd "$EMBEDDED_KNOWLEDGE_HOME"
rtk bash scripts/check-all.sh
```

项目 profile 示例：

```bash
source profiles/template.env
# PCR02 项目可使用：
source profiles/pcr02.env
```

## 目录

- `docs/`：技术知识文档、治理规则与模板。
- `tools/`：可复用调试、诊断、归档工具。
- `docs/governance/`：文档命名、Frontmatter、链接与 AGENT/SKILL 一致性门禁。
- `tools/.codex/skills/`：团队调试与资产处理技能。
- `scripts/`：团队初始化、检查与安装入口。
- `profiles/`：项目环境变量示例。

结构边界见 `docs/standards/repository-structure-guide.md`。

## 本地门禁

```bash
rtk bash scripts/check-all.sh
rtk bash scripts/check-artifacts.sh
rtk bash scripts/check-repository-shape.sh
rtk bash scripts/check-secrets.sh
rtk bash scripts/check-shell-style.sh
rtk bash scripts/check-tools.sh
rtk bash scripts/generate-release-manifest.sh --root <release-dir> --out <release-dir>/release-manifest.csv
rtk bash scripts/check-release-manifest.sh --manifest <release-dir>/release-manifest.csv --root <release-dir>
```

如果 Git 服务支持 CI 或服务端 hook，参考 `docs/runbooks/ci-setup-guide.md` 与 `docs/runbooks/server-hook-setup-guide.md`。

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
ssh://git@192.168.1.4:10022/embedded/knowledge.git
```
