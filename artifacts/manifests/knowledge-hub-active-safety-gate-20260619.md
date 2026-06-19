# Knowledge Hub Active Safety Gate 2026-06-19

## 目标

把 `registry/schema.md` 中已经声明的 active 安全不变量压实到 `tools/knowledge-check.sh`，避免长期知识库出现 personal-local、AI 生成内容或 active 索引漂移。

## 源事实

- `personal-local` 内容属于个人本地可见，不应成为团队 active 知识。
- `domains/personal/` 内容不得进入团队 active index。
- AI 生成或 AI 转换内容只有在具备人工复核证据后才允许进入 `active`。
- 自动化仍保持 report-only；本次不启用自动写入、自动提升或 memory 写入。

## 问题地图

| ID | 发现 | 风险 | 本次动作 |
|---|---|---|---|
| ASG-001 | `personal-local + active` 之前只产生 warning | 个人草稿可能被误当团队事实 | 改为 `knowledge-check` hard error |
| ASG-002 | `indexes/by-status.md` 的 active bucket 未显式拦截 personal/local item | active 索引可发现性与 registry 边界可能漂移 | 增加 active bucket personal-local/domain=personal 检查 |
| ASG-003 | `generated_by_ai=true + active` 未要求人工复核字段 | AI 生成内容可能绕过人工确认进入长期事实 | 要求 `human_reviewed_by`、`human_reviewed_at`、`review_basis` |

## 已落盘

- 更新 `tools/knowledge-check.sh`：新增 personal-local active、active index personal/local、AI active 人工复核字段门禁。
- 更新 `registry/schema.md`：把 active 安全不变量写成可执行字段要求。
- 更新 `tools/README.md`：说明 `knowledge-check.sh` 覆盖 active 安全门禁。
- 更新 registry、migration 和索引，登记本治理制品。

## 非目标

- 不处理 PCR02 7 个 owner-gated 源文档的 owner 决策。
- 不修改 PCR02 源项目 docs。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards/`。
- 不启用自动化，不写 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-active-safety-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-search.sh "active-safety-gate-applied" --json`
- `rtk git diff --check`
- 负向样例：临时副本中将 active item 改为 `visibility=personal-local`，应失败。
- 负向样例：临时副本中将 active item 改为 `generated_by_ai=true` 且无人工复核字段，应失败。

## 状态

- `review_status`: active-safety-gate-applied
- `status`: reviewing
- `owner`: leiwenjun
- `review_after`: 2026-09-19
