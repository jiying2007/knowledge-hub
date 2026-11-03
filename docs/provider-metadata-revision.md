# Provider reviewing 候选元数据修订

`archive --item-id <现有条目>` 用于原候选的描述性元数据修订，沿用 v4 回执和 metadata 操作账本。保持原 ID、路径、主体、owner、正文、source provenance、reviewing 与 promotion=none；不能借此修改正文、标题或提升资格。

来源文件包含原样正文及允许的描述性 YAML 元数据。服务端重新执行类型、主体、内容证明、脱敏和大小检查；调用方必须提供批准的修订前完整文件 SHA256。知识修订始终通过 Codex Provider Adapter，不能直接修改知识文件和 registry。

先规划：

```bash
rtk bash ~/codex/scripts/knowledge-provider.sh archive --cwd "$PWD" \
  --subject project:example --kind runbook --item-id <existing-id> \
  --expected-before-sha256 <approved-before-sha256> \
  --source /tmp/revision.md --sanitized --dry-run --json
```

核对计划中的 operation_id 和 content_sha256，再使用相同参数增加 `--expected-content-sha256 <planned-after-sha256> --apply`。修订同一事务更新正文的元数据镜像、registry、派生视图和追加操作账本。旧内容和事务备份保留；旧内容哈希不再代表修订后内容，后续对账必须使用新的批准哈希。原创建 operation 与原 item ID 均保留。

相同 before hash、相同元数据结果的重放返回 ALREADY_ARCHIVED；错误 before/after hash、正文或标题变化、主体不符、非 reviewing、source provenance 漂移均拒绝写入。写结果 UNKNOWN 时先通过 operation_id 和批准的 after hash 对账，禁止盲目重复 apply。

该入口不改变 active/provisional、owner review、权限和设备事实的边界，也不将 archive 存储位置视为生命周期已归档。检索只对 Provider 创建的 reviewing/draft 且 promotion=none 候选解除路径历史降级，真实历史生命周期及旧手工归档仍保持历史队列。
