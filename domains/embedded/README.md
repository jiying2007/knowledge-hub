# Embedded Domain

本目录是 Knowledge Hub 的嵌入式候选与 provenance 域，保存跨项目知识的提炼稿、复核证据和历史 Hub canonical 内容。团队已发布规范、runbook、公共工具与 Codex skill 的消费权威位于 `workspace://embedded-knowledge`。

## 首次使用

团队成员使用团队发布仓入口：

```text
workspace://embedded-knowledge
```

验证：

```bash
rtk bash scripts/check-all.sh
```

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
