---
title: Owner Review 规范
summary_zh: 定义 owner review、owner gate、owner decision、delegated review 和 archive-only 处理边界，防止把 AI 处理或治理证据误当 owner 签收。该 active
  规范只约束复核流程，不代填 reviewed_by、不自动关闭 gate。
tags:
- governance
- owner-review
- decision-gate
- zh-cn
id: knowledge-hub-owner-review-rules
kind: standard
domain: governance
path: governance/owner-review-rules.md
scope: team-general
visibility: team-internal
status: active
owner: leiwenjun
review_after: '2026-09-18'
review_status: human-reviewed-accepted
promotion: none
aliases:
- Owner Review 规范
related:
- indexes/obsidian-home.md
---

# Owner Review 规范

## 目标

Owner review 用于确认知识条目的权威状态、适用范围和生效条件，避免草稿、会话记录、推断或项目临时材料误变成 active 事实。

## 适用场景

- 将 `draft` 或 `reviewing` 提升为 `active`。
- 将源项目 docs 迁移为 Knowledge Hub 正文。
- 将外部资料吸收为团队规范或 runbook。
- 将会话记录、排障记录、owner worksheet 中的结论提升为当前事实。
- 决定条目是 active、archived、superseded、rejected 还是 archive-only。

## Owner 必答问题

- 这个条目的 owner 是谁。
- 这个条目的适用项目、模块、版本和环境是什么。
- 这个条目是否是当前有效事实。
- 证据是否足够，证据路径是什么。
- 是否存在更权威的 source。
- 何时 review_after。
- 如果出错，如何回退或 supersede。

## 三类责任必须分开

| 责任 | 证明什么 | 不能替代什么 |
| --- | --- | --- |
| 执行授权 | 授权某个 executor 在限定 scope、时间窗和回滚条件下执行写操作 | 不证明 owner 已复核正文，也不等于生命周期决定 |
| 内容复核确认 | 绑定精确条目、原状态、目标状态和正文 SHA256，记录真人作出的内容或生命周期决定 | 不授权工具执行写操作 |
| 执行记录 | 记录实际 executor、transaction、验证和 authorization 消费结果 | 不得反向生成或冒充前两项 |

`registry/authorizations.jsonl` 只承载执行授权。`content-review-attestation` 表单只承载内容复核确认，禁止嵌入 `authorization_id`。`knowledge-promote.sh` 和 `knowledge-retire.sh` 必须分别校验两类证据，任一缺失都保持 blocked。

## Codex 机械生成表单

真人决定不等于真人必须手写 JSON。生命周期变更应先运行只读确认包：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh packet --id <item-id> --target <active|archived|superseded|rejected> --json
```

确认包必须显示 item id、原状态、目标状态、完整正文 SHA256、影响、确认码和两类确认模板。收到真人包含这些绑定信息的明确回复后，Codex 可以把该回复机械映射为本地表单：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-review-attest.sh generate \
  --id <item-id> --target <target> --expected-sha256 <sha256> \
  --attestation-mode <human-reviewed|human-directed-delegation> \
  --attested-by <human> --attestation-source-ref <source-ref> \
  --attestation-text '<exact-human-response>' --confirm-attestation \
  --output artifacts/manifests/<name>.local.jsonl --apply --json
```

该命令只允许写入已忽略提交的 `artifacts/manifests/*.local.jsonl`，不创建授权、不改变 registry、不执行 promotion/retire。重复输入必须幂等，正文 hash、原状态、目标状态或确认码漂移时必须拒绝。

确认模式：

- `human-reviewed`：真人确认已复核精确正文；`reviewed_by` 记录真人身份。`active` 只允许此模式。
- `human-directed-delegation`：真人看过确认包并明确作出非 active 生命周期决定，但委托 Codex 机械落表；`reviewed_by` 必须记录为 `<human>-via-codex-delegation`，不得伪装成直接内容复核。
- “授权执行”“帮我处理”“按建议优化”等泛化指令不自动构成内容复核确认；缺少精确 item、状态、完整 hash 和确认码时不得生成表单。

## 签核结果

建议使用以下状态：

| 状态 | 含义 |
| --- | --- |
| `approved-active` | 可登记为 active |
| `approved-reviewing` | 可保留 reviewing，等待进一步证据 |
| `archive-only` | 只作历史材料，不进入当前事实 |
| `superseded` | 已被新条目替代 |
| `rejected` | 不纳入长期知识 |
| `blocked` | 缺 owner、证据或状态判断 |

## 禁止事项

- 不把 owner 未确认的项目特定材料提升到团队标准。
- 不把 memory candidates 当作项目事实。
- 不把 `.session`、handoff、raw log 或 release binary 写成 active 正文。
- 不在缺少 source、review_after 或证据时声明 active。
- 不把执行授权写成内容复核确认，也不把内容复核表单当作执行授权。
- Codex 不得自行编造 attestation 文本、真人身份或确认码对应的决定。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
