# Knowledge Hub Registry Parse Gate 2026-06-19

## 目标

把 `registry/*.json` 和 `registry/*.jsonl` 的基础语法纳入 `knowledge-check`，防止人工或 AI 维护 registry 时留下半截 JSON、截断 JSONL 或不可解析控制文件。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| RPG-001 | `knowledge-check` 重点校验 `items.jsonl`、`source policies.jsonl`、`sources.json`，但没有统一遍历所有 registry 文件。 | `owners.json`、`projects.json`、`topics.json`、`retention.json` 等控制面文件可能损坏却不被默认门禁发现。 | 默认检查时解析所有 `registry/*.json`。 |
| RPG-002 | `decisions.jsonl`、`promotions.jsonl`、`maintenance-runs.jsonl` 当前可为空，但未来人工追加时可能产生坏行。 | 空文件可通过，坏行应失败。 | 默认检查时逐行解析所有 `registry/*.jsonl`，跳过空行。 |
| RPG-003 | `--sources-only` 应保持轻量 source 检查语义。 | 若改变语义，旧调用可能变慢或误认为全仓检查。 | registry parse gate 只在非 `--sources-only` 模式运行。 |

## 决策

- 不引入复杂 schema 校验。
- 不要求空 JSONL 文件必须有内容。
- 不改变 `--sources-only` 的轻量语义。
- 默认 `knowledge-check --dry-run --json` 必须能发现 registry JSON/JSONL 语法损坏。

## 非目标

- 不定义 `owners.json`、`projects.json`、`topics.json`、`retention.json` 的完整字段 schema。
- 不自动修复 JSON 或格式化 registry 文件。
- 不修改源项目 docs。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-registry-parse-gate-20260619.jsonl`
- `rtk jq -c . registry/*.json`
- `rtk bash -lc 'set -euo pipefail; for f in registry/*.jsonl; do rtk jq -c . "$f" >/dev/null; done'`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `rtk bash tools/knowledge-check.sh --sources-only --dry-run --json`
- `/tmp` 负向验证：复制仓库后写坏 `registry/topics.json`，`knowledge-check` 应报 `registry:registry/topics.json invalid json`。
- `/tmp` 负向验证：复制仓库后写坏 `registry/decisions.jsonl`，`knowledge-check` 应报 `registry:registry/decisions.jsonl:1 invalid jsonl`。
- `rtk bash tools/knowledge-search.sh "registry-parse-gate-applied" --json`

## 结果

已落地并验证通过。

- 当前所有 `registry/*.json` 可被 `jq` 解析。
- 当前所有 `registry/*.jsonl` 可被 `jq` 逐行解析；空文件保持允许。
- `knowledge-check --dry-run --json` 通过。
- `knowledge-check --sources-only --dry-run --json` 通过，保持 source-only 语义不变。
- `/tmp` 负向验证通过：写坏 `registry/topics.json` 后，默认检查失败并报告 `registry:registry/topics.json invalid json`。
- `/tmp` 负向验证通过：写坏 `registry/decisions.jsonl` 后，默认检查失败并报告 `registry:registry/decisions.jsonl:1 invalid jsonl`。
- `registry-parse-gate-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
