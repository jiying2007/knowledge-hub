# Knowledge Hub 30 项边界候选 Owner 确认包

## 当前状态

本文件是只读确认包，不是 owner 决策，不代表任何候选已生效。30 个候选仍为 `reviewing`，`decision_owner` 仍为 `unassigned`，项目 evidence contract 仍为 `pending`。

## 精确绑定对象

- Packet ID：`knowledge-hub-terminal-owner-boundary-20260715`
- 明细 manifest：`artifacts/manifests/knowledge-hub-terminal-owner-boundary-packet-20260715.jsonl`
- Manifest SHA256：`39c1f84c084d4e37527732ff35216e26f83e1fc5b6527c09cb2c1974a0598975`
- 行数：30
- 唯一项目数：30
- 唯一候选 item 数：30
- 确认码：`KH-OWNER-39C1F84C084D`

每一行绑定 `project_id`、decision item、正文路径、当前状态、当前 owner、完整正文 SHA256 和提议效果。任一候选正文、manifest 内容或 manifest SHA256 变化，本确认包立即失效，必须重新生成。

## 提议决定

统一提议为 `accept-authority-boundary-remain-reviewing`：

- 接受各候选中的 source / Knowledge Hub / Obsidian 权威分工。
- 将 `decision_owner` 明确为 `leiwenjun`。
- 为对应项目 evidence contract 绑定可审计的 `owner_ref`。
- 保持候选 `status=reviewing`、`promotion=none`、`manual_validation_pending=true`。
- 在 validation、artifact/device、release、rollback 等真实证据齐备前，保持 evidence contract `pending`。

该提议不执行 active promotion，不证明项目 release-ready，不代替设备验证、回滚演练或真实采用反馈。

## Owner 必须明确回复的文本

只有 owner 亲自发送包含以下完整绑定信息的明确回复后，Codex 才能生成 attestation 并机械落地：

> 我是 leiwenjun。我已复核 Packet `knowledge-hub-terminal-owner-boundary-20260715`，Manifest SHA256 为 `39c1f84c084d4e37527732ff35216e26f83e1fc5b6527c09cb2c1974a0598975`，共 30 项；我接受全部行的 `accept-authority-boundary-remain-reviewing` 提议，确认码 `KH-OWNER-39C1F84C084D`。我授权 Codex 将本回复记录为 hash-bound owner attestation，并为这 30 个项目机械绑定 `decision_owner=leiwenjun` 与 `owner_ref`。本确认不授权 active promotion，不声明任何 evidence contract ready，不允许伪造 validation、artifact/device、release、rollback 或采用反馈。

泛化的“继续”“同意”“帮我落地”或只包含确认码的回复，不满足本包的精确确认条件。

## 落地后的验证

收到有效回复后必须：

1. 保存 exact response、owner identity、packet ID、manifest SHA256、确认码和时间。
2. 逐项校验 30 个候选正文 SHA256 未漂移。
3. 只落地 `decision_owner` 与 `owner_ref`，不改变 lifecycle/promotion/evidence ready 状态。
4. 重跑 `knowledge-check`、project readiness evaluator 和 product final gate。

## Review

- packet 生成者：Codex
- decision owner：`leiwenjun`
- 生成日期：2026-07-15
- 有效性：仅在所有绑定 hash 未漂移时有效
