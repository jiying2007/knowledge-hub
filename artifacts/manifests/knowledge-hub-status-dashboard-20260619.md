# Knowledge Hub Status Dashboard 2026-06-19

## 目标

新增只读状态总览入口，让人工和 AI 维护者用一条命令判断 Knowledge Hub 当前控制面是否健康、是否仍有 owner-gated 语义阻塞、是否存在 stale review 或 active exposure。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| KSD-001 | `knowledge-check`、registry 统计、source policy 状态、source coverage 和 owner gate 状态分散在多个命令里。 | 长期维护者容易只看单一绿灯，误以为终态已完成。 | 新增 `tools/knowledge-status.sh` 聚合只读状态。 |
| KSD-002 | PCR02 owner gate open 是真实未闭环，但不应被当作工具失败。 | 维护者可能把 open gate 当成 check 失败，或反过来忽略语义阻塞。 | 状态总览返回 `needs-owner-review` 且退出码 0；active exposure 才返回 1。 |
| KSD-003 | 终态推进需要能看到 stale review、registry item 数量、source coverage 和 source policies。 | 后续人工新增内容时可能遗漏 review cycle 或 migration 记录。 | dashboard 输出 registry/status、stale review、sources、source policies 和 owner gate 摘要。 |

## 决策

- 新增命令：`rtk bash tools/knowledge-status.sh`。
- 支持 JSON：`rtk bash tools/knowledge-status.sh --json`。
- 支持严格终态门禁：`rtk bash tools/knowledge-status.sh --strict`，任何非 `ok` 状态都返回 1。
- 命令只读，不创建、不修改、不提交、不提升任何文件。
- 状态语义：
  - `ok`：控制面通过，且无 owner gate open。
  - `needs-owner-review`：控制面通过，但仍有 owner decision worksheet open；退出码为 0。
  - `needs-fix`：`knowledge-check` 失败或 owner gate active exposure 存在；退出码为 1。
  - `blocked`：状态工具自身无法读取或解析关键输入；退出码为 1。

## 非目标

- 不关闭 PCR02 owner gates。
- 不生成 owner decision。
- 不迁移 owner-gated 正文。
- 不自动修复 registry、index、source policy 或正文。
- 不执行提升、删除、发布、提交或写 memory。
- 不修改源项目 docs。
- 不启用自动化。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-status.sh` | 0 | 输出中文状态总览；当前控制面为 `needs-owner-review`，`knowledge-check=pass`，owner gates 为 7 open、0 active exposure。 | `tools/knowledge-status.sh` | Knowledge Hub | status-dashboard |
| `rtk bash tools/knowledge-status.sh --json` | 0 | 输出可机器读取 JSON；包含 registry/source/migration/current owner gate 快照，且 `stale_review_after_count=0`。 | `tools/knowledge-status.sh` | Knowledge Hub | status-dashboard |
| `rtk bash tools/knowledge-status.sh --strict --json` | 1 expected | 严格终态门禁在当前 7 个 owner gate open 时返回 1，防止误声明终态完成。 | `tools/knowledge-status.sh` | Knowledge Hub | status-dashboard |
| `/tmp status active exposure fixture` | 1 expected | 临时副本注入 owner-gated active item 后，dashboard 返回 `needs-fix`，`active_exposure_count=1`，`knowledge_check.status=fail`。 | 本 manifest 的“负向 fixture 复现契约” | Negative fixture | status-dashboard |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增状态总览工具和登记制品后全仓门禁应通过。 | `tools/knowledge-check.sh` | Knowledge Hub | status-dashboard |
| `rtk bash tools/knowledge-search.sh status-dashboard-applied --json` | 0 | 本制品应可检索，命中 registry、status index 和本 manifest。 | `registry/items.jsonl`、`indexes/by-status.md`、本 manifest | Knowledge Hub | status-dashboard |

## 负向 fixture 复现契约

负向验证不把 `/tmp` 输出作为长期正文保存；长期审计只保存复现契约和预期结果。

1. 复制当前仓库到 `/tmp/kh-status-fixture.*/repo`。
2. 在临时副本 `registry/items.jsonl` 注入 `bad-status-active-exposure`，关键字段为 `status=active`，`source.source_id=pcr02-project-docs`，`source.source_path=runbooks/asan-debug-guide.md`。
3. 在临时副本 `indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md` 和 `indexes/by-topic.md` 为该 fixture 补最小引用，避免无关索引缺失掩盖 owner gate 行为。
4. 运行 `rtk bash tools/knowledge-status.sh --json`，预期退出码为 1。
5. 预期 JSON 包含 `status=needs-fix`、`knowledge_check.status=fail`、`owner_gates.active_exposure_count=1`。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- review_status：`status-dashboard-applied`
- 下一次复核内容：若 registry 状态、source coverage manifest 或 owner gate 工具字段变化，同步 status dashboard 字段和 README 示例。
