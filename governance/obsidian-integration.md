---
retrieved_at: 2026-07-13
source_license: not-declared; link-and-summary-only
external_refs:
- https://obsidian.md/help/data-storage
- https://obsidian.md/help/properties
- https://obsidian.md/help/bases/syntax
- https://obsidian.md/help/cli
- https://help.obsidian.md/Obsidian%20Sync/Security%20and%20privacy
human_reviewed_by: leiwenjun-via-codex-delegation
human_reviewed_at: 2026-07-13
human_review_decision: accept-as-review-record
review_authorization: auth-20260713-knowledge-hub-obsidian-audit-review
aliases:
- Knowledge Hub Obsidian 集成边界
related:
- indexes/obsidian-home.md
id: knowledge-hub-obsidian-integration-20260713
title: Knowledge Hub Obsidian 集成边界
kind: standard
domain: governance
path: governance/obsidian-integration.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual-plus-official-docs
  from: Codex implementation of user-requested Obsidian integration boundary
  source_urls:
  - https://obsidian.md/help/data-storage
  - https://obsidian.md/help/properties
  - https://obsidian.md/help/bases/syntax
  - https://obsidian.md/help/cli
  - https://help.obsidian.md/Obsidian%20Sync/Security%20and%20privacy
review_after: '2026-10-13'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: verified
promotion: none
promotion_decision: none; local presentation integration only, no active promotion, no owner decision and no external publish
tags:
- knowledge-hub
- obsidian
- markdown
- properties
- backlinks
- local-first
- bases
- cli
- official-docs
- no-active-promotion
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
- rtk bash ~/knowledge-hub/tools/knowledge-search.sh Obsidian --json
- indexes/obsidian-home.md
- indexes/project-readiness.md
- indexes/obsidian/project-readiness.base
- tools/knowledge-link-audit.sh
- tools/knowledge-obsidian-view-build.sh
- templates/obsidian-runtime-acceptance.md
- registry/items.jsonl
- registry/body-coverage.json
evidence_strength: implemented-governance-contract-plus-navigation-entry-and-official-docs-review
evidence_refs:
- governance/obsidian-integration.md
- indexes/obsidian-home.md
- registry/body-coverage.json
- https://obsidian.md/help/data-storage
- https://obsidian.md/help/properties
- https://obsidian.md/help/bases/syntax
- https://obsidian.md/help/cli
- https://help.obsidian.md/Obsidian%20Sync/Security%20and%20privacy
- https://github.com/obsidianmd/obsidian-help
created_at: '2026-07-13'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-13'
summary_zh: 规定 Obsidian 只作为 Knowledge Hub 的本地阅读、手工编辑和链接导航客户端；Markdown 是唯一正文，registry 是 status、owner、review_after 和授权权威，所有高风险动作继续由
  Hub gate 控制。
primary_language: zh-CN
source_language: en
translation_status: summarized-zh
terminology_status: reviewed
---

# Knowledge Hub Obsidian 集成边界

## 结论

Obsidian 可以直接把 `~/knowledge-hub` 作为 vault 打开，但它不是 registry、owner decision、promotion、authorization 或 final gate 的替代品。

```text
Obsidian UI -> canonical Markdown
registry/items.jsonl -> status / owner / review_after 权威
registry + Markdown -> knowledge-check / final gate
indexes/obsidian-home.md -> 人工首屏导航
```

## 推荐配置

- vault root：`~/knowledge-hub`。
- `.obsidian/` 全部保持本机私有，不进入 Git；工作区布局、插件和主题不构成团队事实。
- Excluded files 建议包含：`.git/`、`.tmp/`、`registry/`、`artifacts/manifests/`、`sources/`、`tools/` 和历史归档噪音。
- 新附件默认进入 `inbox/attachments/`，完成分类、hash、敏感性和 owner 复核后再决定是否进入 `artifacts/vault/`。
- 首屏打开 `indexes/obsidian-home.md`，项目和主题继续以 canonical Markdown 链接为准。

## Properties 所有权

| 字段 | 权威位置 | Obsidian 编辑边界 |
|---|---|---|
| `title`、`tags`、`aliases`、`doc_type`、`related` | Markdown frontmatter | 可人工维护，修改后运行 check |
| `status`、`owner`、`review_after` | `registry/items.jsonl` | 只允许镜像 registry；不得在 Obsidian 单独改判 |
| `source`、`evidence_refs`、`validation_refs` | registry 与正文证据段 | 不用 Obsidian 批量改写 |
| owner decision、promotion、authorization | registry/manifest | 只能走 Hub 授权和验证流程 |

`knowledge-check` 会阻断已登记正文的 `status`、`owner`、`review_after` frontmatter 漂移。集合覆盖的历史 corpus 不因 Obsidian 属性而自动成为 active。

## Links、Backlinks 和 Graph

- 长期导航优先使用标准 Markdown links；反引号路径只用于命令或精确路径展示。
- Backlinks 和 Graph 只用于发现关系，不决定权威性。
- `indexes/by-status.md`、`by-owner.md`、`by-review-date.md` 是 registry 派生视图；`by-topic.md` 和 `obsidian-home.md` 是人工 MOC。

## Bases 与 CLI

- 官方 Properties 使用 YAML，并明确不提供内建 bulk editing；这与 Hub 由 registry/脚本做批量治理、Obsidian 只做单文档编辑的边界一致。
- Bases 是 core plugin，视图保存为 `.base`，数据仍来自本地 Markdown 和 properties。本仓提交三个可选只读视图：项目成熟度、reviewing 队列和 active 长期知识；它们不包含自动写入动作，也不依赖 community plugin。
- 30 个规范项目各保留 1 份 readiness evidence contract，并声明一致的 lifecycle properties；统一 dashboard 与项目 Base 提供聚合导航，`pcr02` group 元数据不重复计数。30 份保留 contract 已由 hash-bound owner attestation 绑定 `decision_owner=leiwenjun`，同时继续保持 `reviewing`、`manual_validation_pending=true` 和 `promotion=none`；这些状态仍由 registry/gate 解释，Base 不改变状态，也不推导 evidence-ready。旧 profile/runbook/decision 投影已删除，不保留第二正文或兼容入口。
- `.base` 只消费经过 check 的 properties，不编辑 `status`、`owner`、`review_after`，不创建第二份正文。普通 Markdown 阅读器仍可通过 `indexes/project-readiness.md` 获得等价 MOC 导航。
- 官方 CLI 已提供命令行能力，但要求较新的 installer 并由 Obsidian 注册 PATH。本机 2026-07-13 未发现 `obsidian` 命令，因此当前不接入；未来只允许 `open/search/read` allowlist，不得成为 Hub 验证、写入或发布的必需依赖。

## 安全边界

- 本仓含 team-internal、项目材料和专利附件，不启用 Obsidian Publish。
- 如使用 Sync，必须由 owner 确认数据范围、端到端加密、附件同步和恢复责任。
- 不安装来源不明的 community plugin；需要插件时先做供应链审查并记录回滚方式。
- `.obsidian/` 继续本机私有；仓库只提交不含凭证、布局或设备状态的 `.base` 查询定义。

## 链接与视图验证

`knowledge-link-audit.sh` 检查标准 Markdown links、30 份 readiness contract 的入链和 `.base` YAML 基本结构。active/reviewing 正文、README 和 MOC 的断链属于阻断；archive/冻结历史断链只作告警，避免修改历史证据来制造整洁 Graph。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --json --strict
rtk bash ~/knowledge-hub/tools/knowledge-obsidian-view-build.sh --check --json
```

自动检查只证明 Markdown、Properties、MOC、Base 定义和链接契约正确，不证明 Obsidian 桌面端已经真实渲染。
GUI 验收使用 [本机运行态验收模板](../templates/obsidian-runtime-acceptance.md)，人工完成后把结构化记录写入被
Git 忽略的 `local/obsidian-runtime-acceptance.json`。`knowledge-obsidian-view-build.sh --check --json`
会单独输出 `obsidian_runtime_status=pass|not-validated`；没有版本、验收人、日期、四项 GUI 检查和截图引用时
必须保持 `not-validated`。该状态不改变 registry、owner decision、promotion 或 product gate 的文件层结果。

## 官方能力核对

本边界于 2026-07-13 按 Obsidian 官方文档复核：vault 是本地文件夹，Properties 存储为 YAML，Bases 是基于 Markdown/properties 的 core view，CLI 为可选桌面能力；Sync 的远端 vault 可使用端到端加密，但本地 vault 本身不由 Obsidian 加密。因此 Hub 的 Git、registry、secret scan 和本机磁盘权限仍是主安全边界。

官方 `obsidian-help` 仓库未提供可识别的根 LICENSE 文件；本条目只保存链接和中文概括，不复制官方帮助正文，许可边界记录为 `not-declared; link-and-summary-only`。

- [How Obsidian stores data](https://obsidian.md/help/data-storage)
- [Properties](https://obsidian.md/help/properties)
- [Bases syntax](https://obsidian.md/help/bases/syntax)
- [Obsidian CLI](https://obsidian.md/help/cli)
- [Sync security and privacy](https://help.obsidian.md/Obsidian%20Sync/Security%20and%20privacy)

## 验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Obsidian Knowledge Hub" --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json
rtk bash ~/knowledge-hub/tools/knowledge-obsidian-view-build.sh --check --json
```

## 复核记录

2026-07-13 用户明确授权复核。Codex 作为受托执行人核对官方文档、官方 `obsidian-help` 仓库、本地正文、registry/index 和验证证据后，结论为 `accept-as-review-record`。本结论只关闭 AI/external-source 内容复核队列，保持 `status=reviewing`、`promotion=none`，不生成 owner decision、不提升 active、不授权 Publish/Sync/CLI 写入。

## 未决项

- 本记录是 reviewing 集成规范，不代表 Obsidian CLI、Sync、Bases 或任何 community plugin 已启用。
- 三个 `.base` 已作为可选视图定义落地，但本轮没有启动 Obsidian GUI 做渲染验收；当前运行态明确为 `not-validated`，可移植 Markdown MOC、view build 和 Hub link audit 是自动验证基线。
- 不因本规范生成 owner decision、active promotion、memory write 或远端发布授权。
