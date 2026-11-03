# Provider 内容质量维护

`maintain-content` 用于已登记项目知识的元数据整理、主责迁移和目录收敛。调用经受管 Adapter，先 dry-run，再以真实用户请求 attestation、精确授权 scope 和预期计划 hash 执行 apply。

计划为 JSON：`schema_version=1`，`items` 中每项提供 `item_id`、当前 `expected_sha256`，以及可选 `target_path`、`metadata`。允许字段由 Provider 的明确 allowlist 控制，不能修改 owner、生命周期状态、review_after、source 或正文。正文只允许机械更新迁移路径和相对链接；不补造缺失结论。active 内容及仍绑定受托复核凭据的变更必须先完成独立治理，操作会拒绝隐式降级。

```bash
rtk bash ~/codex/scripts/knowledge-provider.sh maintain-content \
  --source /tmp/<reviewed-plan>.json --dry-run --summary-json
rtk bash ~/codex/scripts/knowledge-provider.sh maintain-content \
  --source /tmp/<reviewed-plan>.json --declaration-file /tmp/<actual-request>.md \
  --authorization-id <exact-authorization> \
  --expected-content-sha256 <planned-hash> --apply --summary-json
```

授权 action 为 `maintain-content`，scope 严格绑定 actor、完整 item_ids、expected_hash 和 visibility_change=false，并要求 host 的 assign 能力。计划包含所读取的 registry、正文和索引的输入 hash；执行采用逐文件备份、并发冲突拒绝与事务 journal。成功只接受 `MAINTAINED` 且 `persisted=true`，manifest 包含实际输出 hash、迁移路径及保留的历史复核信息。超时不能证明未执行，须核对 manifest 和事务状态后处理，不能盲目重试。

质量处理规则：

- 未填写模板正文保留为明确的内容缺失记录，`searchable=false`，不得充当工程验证或排障结论；Provider 拒绝再次归档未填写模板。
- 已被后继候选完整替代的旧入口退出默认检索，使用 `successor_refs` 连接后继；历史保留不授予现行权威。
- 部分范围替代必须标明范围，不能将整个架构判定失效。默认实施入口可收敛到后继，其他架构内容通过明确历史链接读取。
- archived/superseded/rejected 不放在 current 目录。
- 超期记录保留原 review_after，检索给出 `review-overdue` 提示并进入 historical lane；这不意味着技术结论已被否定，也不能当作新的 owner 签收。
- GROS 应用与集成结论、PCR02 SSC305 SDK/平台结论按主责分开；跨仓正文只维护一份，其他位置用引用。

运行知识检查会阻止可默认检索的纯模板条目及 current 中的终态记录。Provider 当前字节证明在事务内追加续接，原 hash 和历史 manifest 不改写；人审 hash 不自动签收新字节。
