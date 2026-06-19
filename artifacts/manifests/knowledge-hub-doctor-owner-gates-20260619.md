# Knowledge Hub Doctor Owner Gates 2026-06-19

## 目标

把 owner gate 看板接入 `knowledge-doctor.sh`，让人工和 AI 维护者可以用一个只读诊断入口同时查看全仓 diagnostics、条目 explain/search，以及指定 source 的 owner-gated 未闭环状态。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| DOG-001 | owner gate 看板是独立命令，维护者可能只跑 doctor 而忘记 owner-gated 检查。 | 涉及 owner-gated 内容时，可能漏看 active exposure 或 owner 必填证据。 | `knowledge-doctor.sh` 新增 `--owner-gates <source-id>`。 |
| DOG-002 | doctor 如果吞掉 owner gate 看板失败状态，会掩盖 active exposure。 | active exposure 可能在统一诊断入口中被误放行。 | owner gate 看板失败时，doctor 最终退出码继承该失败状态。 |
| DOG-003 | doctor 不应升级成自动修复器。 | 自动改 registry/index 或生成 owner decision 会扩大风险。 | 仍只读运行现有检查，不创建、不修改、不提交、不提升。 |

## 决策

- 新增参数：`rtk bash tools/knowledge-doctor.sh --owner-gates <source-id>`。
- 可与 `--id <item-id>` 组合使用。
- doctor 运行顺序：
  1. 全仓 diagnostics。
  2. 可选 item explain/search。
  3. 可选 owner gate 看板。
- 任一步失败时，最终退出码为首个失败步骤状态码。

## 非目标

- 不生成 owner decision。
- 不迁移 owner-gated 正文。
- 不自动修复 registry、index、migration 或正文。
- 不执行 `validation_refs`。
- 不修改源项目 docs。
- 不启用自动化。
- 不写 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-doctor.sh --help` | 0 | help 已展示 `--owner-gates <source-id>`，并声明只读。 | `tools/knowledge-doctor.sh` | Tool smoke | doctor-owner-gates |
| `rtk bash tools/knowledge-doctor.sh --owner-gates pcr02-project-docs` | 0 | doctor 已运行 diagnostics 和 PCR02 owner gate 看板；看板显示 7 open、0 active exposure。 | `tools/knowledge-doctor.sh` | Tool smoke | doctor-owner-gates |
| `rtk bash tools/knowledge-doctor.sh --id knowledge-hub-root --owner-gates pcr02-project-docs` | 0 | 组合参数路径通过；doctor 同时输出 item explain/search 和 PCR02 owner gate 看板。 | `tools/knowledge-doctor.sh` | Tool smoke | doctor-owner-gates |
| `/tmp doctor owner-gates active exposure fixture` | 1 expected | 临时副本注入 owner-gated active item 后，doctor 返回 1，输出包含 `owner-gated-active`、`status: needs-fix` 和 `active exposure: 1`。 | 本 manifest 的“负向 fixture 复现契约” | Negative fixture | doctor-owner-gates |
| `/tmp doctor --id + owner-gates active exposure fixture` | 1 expected | 临时副本注入 owner-gated active item 后，组合参数 `--id bad-doctor-owner-gates-active-exposure --owner-gates pcr02-project-docs` 返回 1。 | 本 manifest 的“负向 fixture 复现契约” | Negative fixture | doctor-owner-gates |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 新增 doctor 参数和登记制品后全仓门禁通过，0 error、0 warning。 | `tools/knowledge-check.sh` | Knowledge Hub | doctor-owner-gates |
| `rtk bash tools/knowledge-search.sh doctor-owner-gates-applied --json` | 0 | 本制品可检索，命中 registry、status index 和 manifest。 | `registry/items.jsonl`、`indexes/by-status.md` | Knowledge Hub | doctor-owner-gates |

## 负向 fixture 复现契约

负向验证不把 `/tmp` 输出作为长期正文保存；长期审计只保存复现契约和预期结果。

1. 复制当前仓库到 `/tmp/kh-doctor-*-fixture.*/repo`。
2. 在临时副本 `registry/items.jsonl` 注入 `bad-doctor-owner-gates-active-exposure`，关键字段为 `status=active`，`source.source_id=pcr02-project-docs`，`source.source_path=runbooks/asan-debug-guide.md`。
3. 在临时副本 `indexes/by-owner.md`、`indexes/by-review-date.md`、`indexes/by-status.md` 和 `indexes/by-topic.md` 为该 fixture 补最小引用，避免无关索引缺失掩盖 owner gate 行为。
4. 运行 `rtk bash tools/knowledge-doctor.sh --owner-gates pcr02-project-docs`，预期退出码为 1。
5. 运行 `rtk bash tools/knowledge-doctor.sh --id bad-doctor-owner-gates-active-exposure --owner-gates pcr02-project-docs`，预期退出码为 1。
6. 预期输出同时包含 `owner-gated-active`、`status: needs-fix`、`active exposure: 1` 和 `bad-doctor-owner-gates-active-exposure`。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：如 owner gate 看板参数变化，同步 doctor 参数和 README 示例。
