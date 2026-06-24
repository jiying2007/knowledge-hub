---
title: 项目 Docs 总入口
doc_type: index
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-18
tags: [docs, project, knowledge]
related: []
validation_refs: []
---

# 项目 Docs 总入口

本目录只保留当前项目强绑定文档。团队通用知识库统一放在：

```text
~/embedded/knowledge
```

远程仓库：

```text
ssh://git@192.168.1.4:10022/embedded/knowledge.git
```

建议本机环境变量：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

## 本项目保留内容

1. `architecture/`：当前项目架构、模块边界、诊断命令架构。
2. `runbooks/`：当前项目构建部署、标定、专项工具使用。
3. `specs/`：当前项目设计规格。
4. `plans/`：当前项目实施计划归档；默认不作为当前执行来源。
5. `reports/`：当前项目分析、验证、复盘报告归档；默认不作为当前门禁来源。
6. `standards/`：当前项目特有依赖基线。
7. `../tools/`：当前项目对团队公共工具的轻量适配层。

## 团队知识库内容

以下内容不再放在当前项目仓，统一查阅 `~/embedded/knowledge`：

1. 通用 C/C++ 编码规范、Agent/Skill 工程基线。
2. ASAN、GDB、core dump、SIGBUS、crash bundle 等通用排障手册。
3. `tools/debug/`、`tools/sigmastar/` 等公共脚本。
4. `tools/.codex/skills/` 团队调试技能。
5. SigmaStar 平台通用知识、能力矩阵、主题索引与归档 manifest。
6. 文档模板与文档治理脚本。

## 文档状态规则

1. `status: active`：当前仍可作为设计、构建、排障或工具使用的有效入口。
2. `status: archived`：历史计划、历史报告或已完成会话记录，只能作为背景参考。
3. 归档计划中的未勾选步骤不是当前待办；重新启用前必须核对源码、构建脚本和实际产物。
4. 历史报告中的旧验证命令只代表当时执行记录；当前验证优先使用本项目现有脚本和 `~/embedded/knowledge` 的公共门禁。

## 当前生效项目文档

- `docs/architecture/project-overview-design.md`
- `docs/architecture/project-detailed-design.md`
- `docs/architecture/project-core-module-design.md`
- `docs/architecture/module-catalog.md`
- `docs/architecture/hdi-api-app-functional-overview.md`
- `docs/architecture/diag-command-architecture-final.md`
- `docs/specs/2026-05-10-diag-v4-hybrid-refcount-discovery-spec.md`
- `docs/runbooks/project-build-and-deploy-guide.md`
- `docs/runbooks/project-debug-tools-guide.md`
- `docs/runbooks/irlight-sw-threshold-calibration.md`
- `docs/runbooks/prog-tool-usage-guide.md`
- `docs/standards/third-party-libraries-reference.md`

## 项目工具入口

- `tools/README.md`
- `tools/debug/README.md`
- `tools/debug/project-knowledge-debug.sh`

## 历史资料入口

- `docs/plans/`：历史计划与阶段性实施方案。
- `docs/reports/`：历史分析、发布说明、会话归档和验证记录。
