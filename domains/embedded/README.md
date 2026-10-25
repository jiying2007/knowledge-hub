# Embedded Domain

本目录是 Knowledge Hub 的嵌入式候选与 provenance 域，保存跨项目知识的提炼稿、复核证据和历史 Hub canonical 内容。团队已发布规范、runbook、公共工具与 Codex skill 的消费权威位于 `workspace://embedded-knowledge`。

## 首次使用

团队成员使用团队发布仓入口：

```text
workspace://embedded-knowledge
```

团队仓验证（必须在 `workspace://embedded-knowledge` 对应的实际团队仓 checkout 根目录执行；不得直接在 Knowledge Hub 镜像中执行或把命令存在当成测试成功）：

```bash
rtk bash scripts/check-all.sh
```

本目录 `skills/` 中引用的 `scripts/check-all.sh`、`docs/templates/` 或 `docs/AGENTS.md` 也遵循相同的团队仓 cwd/版本边界；没有真实团队仓 commit、执行退出码和产物，不得在 Hub 标记团队技能已发布或测试通过。

Hub 侧常用入口：

- 团队化候选：`standards/`、`runbooks/`
- 平台和架构知识：`platform/`、`architecture/`
- 技能和工具说明：`skills/`、`tools/`
- 模板和治理规则：`templates/`、`governance/`

## 目录

- `standards/`：团队级规范和跨项目规则。
- `runbooks/`：排障、验证、发布和工具使用流程。
- `architecture/`、`platform/`：平台能力、系统架构和设计知识。
- `skills/`、`tools/`：可复用技能和工具说明。
- `templates/`、`governance/`：模板、命名、证据和治理规则。

这些目录中的 `reviewing`、draft、旧 active body 或历史 mirror 不自动等于团队已发布事实。提升时必须记录 source SHA256、目标路径、成熟度、Owner、验证状态和回滚，并通过目标仓 `docs/governance/promotion-contract.md`。

## 旧归档规范的适用性警示（2026-10-25）

本仓 `standards/`、`architecture/` 与 `governance/` 下部分文件是退役团队知识仓的原文镜像。即使旧 Frontmatter 写 `maturity: verified`，只要状态仍为 `status: archived`、`searchable: false`，就只能用于历史回溯；正文中“当前生效”“强制规范”及 `docs/`、`scripts/` 等执行路径均**不得**据此获得当前 Hub 或团队发布权限。

- [历史C代码规范](standards/c-coding-standards.md) 中的 `__API_LIST_H__`、`_List_t`、`_LIST_IsEmpty` 是 C/C++ 实现保留标识符示例，不能直接复制到新代码、头文件或生成模板；当前C规范需在实际团队发布仓与目标工具链上重新确认。
- [历史发布版本说明](standards/release-versioning-guide.md) 的 `scripts/release.sh` / `--push` 与 [旧Docs索引](governance/docs-index.md) 的“当前生效”仅属于旧团队仓语境；绝不在 Hub 镜像执行或据此发布。
- [历史平台能力矩阵](architecture/sigmastar-platform-capability-matrix.md) 的“完整／强／中”仅为当时资料组织/定性判断，不是最新SDK、板卡功能、性能或量产选型证明。
- [历史线程排障文档](standards/thread-troubleshooting-optimization.md) 里的 `<PID>` 等标记仅是需由授权操作人员替换的参数占位；排障命令、VSHDIOS设计与2026年阶段记录不视为当前平台已验收。

本节只补充检索导航和执行作用域：不修改旧正文、历史日期或原哈希，不自动迁移到团队仓、不更新 Owner/Active/`review_after`，也不授权设备、发布、源仓写入或外部证据操作。逐篇审查意见记录在 Issue #176，仍需实际团队仓提交、许可、负向测试和必要的Owner验证。


## Hub 候选门禁

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
```

如果需要恢复历史来源、迁移证据或 owner 边界，优先查看 `registry/retired-sources.jsonl`、`registry/source-tombstones.jsonl`、`indexes/by-source.md` 和团队仓迁移映射。

## 发布边界

- Hub 不直接写团队仓 remote，不自动 commit/push/merge/tag。
- 团队仓不接收 Hub registry、authorization、raw evidence、个人笔记或项目 lifecycle 正文。
- 发布正文在团队仓通过 `scripts/check-all.sh` 后，Hub 回写 validation/provenance；没有目标 commit 时只能声明本地待提交状态。
- X5 实机、外部下载入口等未验证项继续保留明确 draft/pending 边界，不因文件进入团队仓自动升级成熟度。
