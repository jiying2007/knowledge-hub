# Knowledge Hub Validation Reference Gate 2026-06-19

## 目标

让 `registry/items.jsonl` 中的 `validation_refs` 成为稳定、轻量、可人工维护的证据入口，避免条目登记后没有验证线索、引用空值或留下失效的本地证据路径。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| VRG-001 | active/reviewing 条目需要可复核证据，但此前未强制 `validation_refs` 非空。 | 人工新增条目后可能只登记描述，没有验证入口。 | `knowledge-check` 要求 active/reviewing item 有非空 `validation_refs`。 |
| VRG-002 | `validation_refs` 可能被写成字符串、空列表或空元素。 | 后续人工和 AI 无法稳定解析验证入口。 | `knowledge-check` 要求 `validation_refs` 是非空字符串列表。 |
| VRG-003 | `validation_refs` 中的本地文件路径可能失效或写成不规范路径。 | manifest、registry 或证据文件移动后，复核链路断开；`./`、绝对路径或拼写错误的路径可能被静默放过。 | 对没有空格、且形似 Knowledge Hub 本地路径的 ref，要求使用仓库内规范相对路径并检查本地文件存在；不支持的路径形态直接报错。 |

## 决策

- `active` 和 `reviewing` item 必须有非空 `validation_refs`。
- `validation_refs` 存在时必须是 list。
- list 每个元素必须是非空 string。
- 没有空格、且以 `artifacts/`、`docs/`、`domains/`、`registry/`、`indexes/`、`governance/`、`tools/`、`templates/` 开头，或等于 `README.md` / `AGENTS.md` 的 ref，视为本地路径并检查存在。
- 没有空格的绝对路径、`./`、`../` 和其他路径样式 ref 不静默跳过，必须改成仓库内规范相对路径，或写成明确的命令型 ref。
- 命令型 ref 只记录，不执行；本门禁不访问外部源、不运行验证命令。

## 非目标

- 不执行 `validation_refs` 中记录的命令。
- 不访问外部路径或源项目 docs。
- 不自动生成验证报告。
- 不改变 item status、owner、review_after 或 promotion。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . artifacts/manifests/knowledge-hub-validation-ref-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后删除一个 active item 的 `validation_refs`，`knowledge-check` 应报 active/reviewing missing validation_refs。
- `/tmp` 负向验证：复制仓库后把一个 item 的 `validation_refs` 改成字符串，`knowledge-check` 应报 validation_refs must be list。
- `/tmp` 负向验证：复制仓库后把一个 item 的本地 path ref 改成缺失路径，`knowledge-check` 应报 validation_ref missing local path。
- `/tmp` 负向验证：复制仓库后把一个 item 的本地 path ref 改成 `./registry/items.jsonl`，`knowledge-check` 应报 validation_ref must be repo-relative or command。
- `/tmp` 负向验证：复制仓库后把一个 item 的本地 path ref 改成绝对路径，`knowledge-check` 应报 validation_ref must be repo-relative or command。
- `/tmp` 负向验证：复制仓库后把一个 item 的本地 path ref 改成不支持的相对路径，`knowledge-check` 应报 unsupported validation_ref format。
- `rtk bash tools/knowledge-search.sh "validation-ref-gate-applied" --json`

## 结果

- `rtk bash -n tools/knowledge-check.sh`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk jq -c . artifacts/manifests/knowledge-hub-validation-ref-gate-20260619.jsonl`: pass。
- `rtk jq -c . registry/items.jsonl`: pass。
- `rtk bash tools/knowledge-check.sh --dry-run --json`: pass，`errors=[]`，`warnings=[]`。
- `/tmp` missing-validation-refs 负向验证：删除一个 active item 的 `validation_refs` 后，`knowledge-check` 报 `items:knowledge-hub-root active/reviewing missing validation_refs`。
- `/tmp` validation-refs-type 负向验证：把一个 active item 的 `validation_refs` 改成字符串后，`knowledge-check` 报 `items:knowledge-hub-root validation_refs must be list`。
- `/tmp` missing-local-validation-ref 负向验证：把一个本地 path ref 改成 `artifacts/manifests/missing-validation-ref.jsonl` 后，`knowledge-check` 报 `items:knowledge-hub-validation-ref-gate-20260619 validation_ref missing local path: artifacts/manifests/missing-validation-ref.jsonl`。
- `/tmp` dot-slash-validation-ref 负向验证：把一个本地 path ref 改成 `./registry/items.jsonl` 后，`knowledge-check` 报 `items:knowledge-hub-validation-ref-gate-20260619 validation_ref must be repo-relative or command: ./registry/items.jsonl`。
- `/tmp` abs-validation-ref 负向验证：把一个本地 path ref 改成 `/tmp/abs-validation-ref.jsonl` 后，`knowledge-check` 报 `items:knowledge-hub-validation-ref-gate-20260619 validation_ref must be repo-relative or command: /tmp/abs-validation-ref.jsonl`。
- `/tmp` unsupported-validation-ref 负向验证：把一个本地 path ref 改成 `unknown/path.jsonl` 后，`knowledge-check` 报 `items:knowledge-hub-validation-ref-gate-20260619 unsupported validation_ref format: unknown/path.jsonl`。
- `rtk bash tools/knowledge-search.sh "validation-ref-gate-applied" --json`: count=3，可从 `registry/items.jsonl`、`indexes/by-status.md` 和本 manifest 找到。
