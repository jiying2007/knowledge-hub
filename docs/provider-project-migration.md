# Provider 完整项目知识迁移

`migrate-project` 合并两个已登记项目，以目标项目作为唯一现行身份。它属于本地身份维护，不产生 owner decision、active promotion 或产品验收。

调用必须通过受管 Adapter。先执行 dry-run，使用回执的 `expected_hash` 绑定完整输入快照、迁移路径和输出内容；实际 apply 还要求 host 的 `assign` 写能力、标准授权账本中的精确执行 scope，以及当前线程真实用户请求的 attestation。

```bash
rtk bash ~/codex/scripts/knowledge-provider.sh migrate-project \
  --from-subject project:<source-project> --project <target-project> \
  --remote-url <verified-current-remote> --dry-run --summary-json
```

执行授权的 JSON scope 必须精确匹配 `actor`、`action=migrate-project`、`source_subject_sha256`、`subject_ref`、`remote_key`、`expected_hash` 和 `visibility_change=false`；`allowed_actions` 使用现有 `automation-apply-with-review`。授权只代表用户明确要求的身份迁移，不授予内容签收或发布权限。审批行不参与 proposal hash，以避免审批内嵌该 hash 的递归；事务仍绑定授权账本的完整实际字节并拒绝并发漂移。

```bash
rtk bash ~/codex/scripts/knowledge-provider.sh migrate-project \
  --from-subject project:<source-project> --project <target-project> \
  --remote-url <verified-current-remote> \
  --declaration-file /tmp/<actual-user-request>.md \
  --authorization-id <exact-execution-authorization> \
  --expected-content-sha256 <dry-run-expected-hash> --apply --summary-json
```

操作会预检源目录全部文件，拒绝 omitted/ignored 内容、符号链接、未知目标冲突及执行源改名。两个项目首页合并，仓库阶段与知识项目阶段的 evidence contract 各保留正文；仓库 contract 成为现行项目入口。其他冲突必须先显式解决，不覆盖目标内容。

原状态、owner、技术结论、commit 和测试边界保留。旧项目写授权撤销，不能转授目标。受影响的人审 hash 和 AI 受托凭据不自动签收新字节：历史证明进入迁移 manifest，当前内容回到待复核。Provider 当前字节证明通过追加记录续接，旧 hash 保留历史含义。

已有 owner packet 的原签收语句与原 hash 不改写。现行规范化 packet 只能由精确新 hash 加迁移 manifest 的 `before_writes → result_writes` 沿革核验；该证据只保全历史边界确认，不产生新的 owner 签收或产品资格。缺少沿革或 hash 不符时继续拒绝。

只有 `MIGRATED` 或 `ALREADY_MIGRATED` 且 `persisted=true` 可确认迁移持久化。回执包含事务与 manifest 引用，manifest 提供源文件 hash、目标路径、输出 hash 及历史复核证据；源身份只保留不可逆 hash，不建立 alias、跳转或兼容路由。

事务使用既有精确输入校验、逐文件备份和恢复 journal。网络或调用超时不证明未执行；先用相同预期 hash 回读核验，禁止盲目覆盖重试。`ALREADY_MIGRATED` 会核对全部输出字节，后续内容若已改变则保持 fail-closed。
