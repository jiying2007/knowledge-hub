# Migration Policy

## Strategy

- 先登记 source，再迁移正文。
- 每个旧路径必须写入 `registry/migrations.jsonl`。
- 迁移前后必须做内容一致性校验。
- 旧路径保留到新入口通过检查并完成人工确认。

## Required Fields

```json
{"from":"old/path.md","to":"new/path.md","mode":"copy-first","status":"planned","checked_at":"","notes_zh":""}
```

## Stop Conditions

- 发现疑似 secret。
- 迁移后 diff 不一致。
- 新路径违反 authority boundary。
- 旧路径被构建、发布或脚本强依赖。
