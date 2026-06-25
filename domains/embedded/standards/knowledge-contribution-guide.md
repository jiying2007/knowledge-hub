---
title: 知识库贡献规范
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-16
last_updated: 2026-05-16
tags: [knowledge, contribution, governance]
related: [../runbooks/team-onboarding-guide.md, ../runbooks/codex-skills-install-guide.md, ../runbooks/ci-setup-guide.md, ../runbooks/dev-tooling-setup-guide.md, repository-structure-guide.md, release-versioning-guide.md, shell-script-style-guide.md]
validation_refs: []
---

# 知识库贡献规范

## 1. 内容边界

1. 跨项目复用的规范、排障手册、公共脚本、平台知识进入本仓。
2. 只服务单个业务项目的架构、计划、报告和构建细节留在项目仓。
3. 大体积 SDK、core、日志包、制品归档不进入 Git，只在 manifest 中记录 URI 与 SHA256。
4. 仓库目录边界遵循 `docs/standards/repository-structure-guide.md`。

## 2. 提交流程

1. 新增文档优先复用 `docs/templates/`。
2. 新增工具必须有 README 或 runbook 入口。
3. 修改前后运行：

```bash
rtk bash scripts/check-all.sh
```

4. 修改归档 manifest 时，额外确认：

```bash
rtk bash scripts/check-artifacts.sh
```

5. 新增脚本或 profile 时，额外关注：

```bash
rtk bash scripts/check-shell-style.sh
rtk bash scripts/check-secrets.sh
```

新增文档建议使用：

```bash
rtk bash scripts/new-doc.sh --type runbook --title "标题" --out docs/runbooks/example-runbook.md
```

新增技能建议使用：

```bash
rtk bash scripts/new-skill.sh --name example-triage --description "示例分诊技能" --scope tools
```

## 3. 引用规则

1. 团队本机路径统一写作 `$EMBEDDED_KNOWLEDGE_HOME`。
2. 制品路径优先使用 `nas://` 或内部制品服务 URI。
3. 示例可保留项目名，但必须标明“示例”，不能作为通用默认值。

## 4. 版本记录

每次结构性调整更新 `CHANGELOG.md`；平台资料升级同步更新 `docs/archive/sigmastar/manifest.csv` 与 `manifest.md`。

发布 tag 规则见 `docs/standards/release-versioning-guide.md`。

合并请求模板可使用 `docs/templates/change-request-template.md`、`.github/PULL_REQUEST_TEMPLATE.md` 或 `.gitlab/merge_request_templates/knowledge.md`。
