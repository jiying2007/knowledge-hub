---
title: Docs 总入口
doc_type: index
knowledge_type: guideline
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-12
last_updated: 2026-05-21
tags: [docs, governance]
related: [governance/README.md, templates/standard-template.md, templates/agent-template.md, templates/skill-template.md, standards/repository-structure-guide.md, standards/agent-skill-engineering-baseline.md, standards/c-coding-standards.md, standards/thread-troubleshooting-optimization.md, standards/personal-development-enhancements.md, standards/shell-script-style-guide.md, runbooks/dev-tooling-setup-guide.md, runbooks/embedded-linux-performance-triage-guide.md, runbooks/spi-nand-busybox-io-stress-guide.md, runbooks/sigmastar-media-pipeline-triage-guide.md, runbooks/yolo-ai-vision-deployment-guide.md, architecture/sigmastar-media-ai-dataflow.md, runbooks/sigmastar-sdk-upgrade-playbook.md, runbooks/embedded-build-reproducibility-guide.md, runbooks/device-resource-leak-triage-guide.md, standards/embedded-artifact-provenance-standard.md]
validation_refs: []
---

# Docs 总入口

## 目录说明（强制）

1. `standards/`：长期稳定规范与约定。
2. `architecture/`：平台级架构、能力矩阵与知识模型。
3. `runbooks/`：操作手册、排障手册、归档流程。
4. `archive/`：冻结历史、外部资料索引与制品清单。
5. `templates/`：标准模板。
6. `governance/`：治理规则、校验脚本、门禁说明。

## 使用顺序

1. 新建文档时，先从 `docs/templates/` 选择对应模板。
2. 文档提交前，执行 `rtk bash scripts/check-all.sh`。
3. 合并前，执行全量门禁，确保命名/Schema/链接一致性。

## 团队入口

- `docs/runbooks/team-onboarding-guide.md`
- `docs/runbooks/codex-skills-install-guide.md`
- `docs/runbooks/dev-tooling-setup-guide.md`
- `docs/runbooks/ci-setup-guide.md`
- `docs/runbooks/server-hook-setup-guide.md`
- `docs/runbooks/spi-nand-busybox-io-stress-guide.md`
- `docs/standards/knowledge-contribution-guide.md`
- `docs/standards/release-versioning-guide.md`
- `docs/standards/repository-structure-guide.md`
- `docs/standards/personal-development-enhancements.md`
- `docs/standards/shell-script-style-guide.md`
- `docs/standards/embedded-artifact-provenance-standard.md`

## 模板入口

- `docs/templates/standard-template.md`
- `docs/templates/agent-template.md`
- `docs/templates/skill-template.md`
- `docs/templates/runbook-template.md`
- `docs/templates/spec-template.md`
- `docs/templates/plan-template.md`
- `docs/templates/report-template.md`
- `docs/templates/change-request-template.md`
- `docs/standards/knowledge-contribution-guide.md`
- `docs/standards/release-versioning-guide.md`

## 知识库主文档（当前生效）

- `docs/architecture/sigmastar-platform-internal-overview.md`
- `docs/architecture/sigmastar-platform-capability-matrix.md`
- `docs/architecture/sigmastar-media-ai-dataflow.md`
- `docs/runbooks/sigmastar-platform-development-workflow.md`
- `docs/runbooks/sigmastar-archive-artifact-guide.md`
- `domains/embedded/runbooks/asan-debug-guide.md`（团队级 active 方法论；active promotion 证据见 `artifacts/manifests/embedded-asan-active-promotion-20260629.md`）
- `docs/runbooks/asan-offline-symbolize-guide.md`
- `docs/runbooks/gdb-debug-guide.md`
- `docs/runbooks/core-dump-capture-guide.md`
- `docs/runbooks/core-binary-match-verification-guide.md`
- `docs/runbooks/crash-bundle-collection-guide.md`
- `docs/runbooks/offline-gdb-core-fastpass-guide.md`
- `docs/runbooks/crash-triage-checklist.md`
- `docs/runbooks/sigbus-alignment-check-guide.md`
- `docs/runbooks/thread-crash-correlation-guide.md`
- `docs/runbooks/embedded-linux-performance-triage-guide.md`
- `docs/runbooks/spi-nand-busybox-io-stress-guide.md`
- `docs/runbooks/sigmastar-media-pipeline-triage-guide.md`
- `docs/runbooks/yolo-ai-vision-deployment-guide.md`
- `docs/runbooks/sigmastar-sdk-upgrade-playbook.md`
- `docs/runbooks/embedded-build-reproducibility-guide.md`
- `docs/runbooks/device-resource-leak-triage-guide.md`
- `docs/runbooks/team-onboarding-guide.md`
- `docs/runbooks/codex-skills-install-guide.md`
- `docs/runbooks/dev-tooling-setup-guide.md`
- `docs/runbooks/ci-setup-guide.md`
- `docs/runbooks/server-hook-setup-guide.md`
- `docs/standards/sigmastar-platform-topic-catalog.md`
- `docs/standards/agent-skill-engineering-baseline.md`
- `docs/standards/c-coding-standards.md`
- `docs/standards/repository-structure-guide.md`
- `docs/standards/thread-troubleshooting-optimization.md`
- `docs/standards/personal-development-enhancements.md`
- `docs/standards/shell-script-style-guide.md`
- `docs/standards/embedded-artifact-provenance-standard.md`
- `docs/archive/sigmastar/manifest.md`
