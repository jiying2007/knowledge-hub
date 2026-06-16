# Knowledge Hub Agent Rules

## 1. 基本定位

- 根目录：`~/knowledge-hub`
- 角色：统一知识控制面
- 范围：团队知识、项目事实、工程归档、专利材料、Codex 工作流、个人草稿和外部制品引用。

## 2. 工作原则

- 先分类，再落盘；先 registry，再提升。
- 正文只维护一份；其他位置使用索引、引用或迁移记录。
- 自动化默认 `report-only`，不得自动删除、发布、提交、提升或写 memory。
- `~/.codex/memories` 只能作为辅助召回，不能作为规则或事实的唯一来源。

## 3. 权威边界

- 团队级规范和跨项目 runbook：`domains/embedded/`
- 当前项目事实：`domains/projects/<project>/current/`
- 项目历史证据：`domains/projects/<project>/archive/`
- 当前有效项目决策：`domains/projects/<project>/decisions/`
- 专利披露与检索：`domains/patents/`
- Codex 会话和工作流治理：`domains/codex/`
- 个人草稿：`domains/personal/`

## 4. 禁止事项

- 禁止把 project-specific 内容提升到 `domains/embedded/standards/`。
- 禁止把 `domains/personal/` 内容加入团队 active index。
- 禁止把 raw logs、core、SDK 压缩包、release binary 写入文本知识层。
- 禁止把 token、private key、password、cookie 或运行时 secret 写入任何正文或 registry。
- 禁止在未验证来源、owner、状态和 review 周期前声明知识条目 active。

## 5. 最小验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
```

修改 Codex 自动化或 manifest 后，还必须在 `~/codex` 执行：

```bash
rtk bash scripts/doctor.sh --scope governance
rtk bash scripts/check-routing-precedence.sh
rtk bash scripts/check.sh
rtk bash scripts/final-ready.sh
```
