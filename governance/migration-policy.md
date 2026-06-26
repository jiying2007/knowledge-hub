# 迁移策略（Migration Policy）

## 策略（Strategy）

- 先登记 source，再迁移正文。
- 每个旧路径必须写入 `registry/migrations.jsonl`、`registry/source-tombstones.jsonl` 或对应迁移 manifest，作为 provenance 和审计证据。
- 迁移前后必须做内容一致性校验。
- 新入口通过检查并完成人工确认后，旧路径不得继续作为 active entry、默认查询入口、fallback 或新增归档目的地；外部源若仍需保留，只能作为原始 provenance。

## 必填字段（Required Fields）

```json
{"from":"old/path.md","to":"new/path.md","mode":"copy-first","status":"planned","checked_at":"","notes_zh":""}
```

## 停止条件（Stop Conditions）

- 发现疑似 secret。
- 迁移后 diff 不一致。
- 新路径违反 authority boundary。
- 旧路径被构建、发布或脚本强依赖。
