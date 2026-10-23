# 旧 Codex Archive 封存索引

本目录是旧 `~/codex/docs/archive` 迁移后的封存索引区。旧正文、同名 `.meta.json` 和旧 `_registry/` 已不再作为 Knowledge Hub 的正文层或新增入口；保留的 topic `index.md` 只用于 tombstone / provenance 导航，帮助追溯旧文件被删除、迁移、覆盖或保留的原因。

## 当前权威入口

新增或复核 Codex 治理、会话总结、工作流、归档审计和长期经验时，不再写入本目录。按内容类型进入当前 canonical 位置：

- Codex 治理和工作流：`domains/codex/`
- 高风险迁移、删除、覆盖和审计证据：`artifacts/manifests/`
- 项目事实和项目历史：`projects/<project>/current/`、`projects/<project>/archive/`、`projects/<project>/decisions/`
- 团队级嵌入式 runbook / 方法论：`domains/embedded/`
- 普通个人或临时笔记：`notes/`

## 保留内容

- topic `index.md`：记录旧文件名、tombstone、迁移目标或删除执行 manifest。
- `codex-archive.ref.md`：记录旧 archive 的 source / provenance 边界。
- 删除和迁移证据：以 `artifacts/manifests/codex-archive-*` 为准。

本目录不再保存旧正文，不再要求 `.meta.json`，也不再使用旧 `schema_version=2` archive meta 作为当前 registry。旧来源路径只作 provenance，不作为 active source、默认查询入口或新增归档目标。

## 查询和门禁

以下命令只适用于当前 Knowledge Hub 工作区；封存目录不是可执行运行环境。历史归档中的旧命令、参数和日期不作为现行运行权限，实际操作以当前 CLI 解析器与受保护主线为准。完整回归仅说明仓库机器检查结果，不替代 owner、源仓或产品验收。

```bash
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "Codex archive"
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product --regression-suite full
```

旧正文删除、迁移目标调整或 tombstone 更新必须保留授权、hash、rollback 和验证命令；不得因为本目录存在 topic index 就把旧 archive 视为仍可写入的知识库正文层。
