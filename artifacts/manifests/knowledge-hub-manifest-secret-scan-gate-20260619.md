# Knowledge Hub Manifest Secret Scan Gate 2026-06-19

## 目标

把 `artifacts/manifests/` 纳入 `knowledge-check` 的 secret pattern 扫描范围，避免长期治理证据、owner review 包、迁移记录和 handoff manifest 中误写 token、cookie、private key 或 password。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| MSS-001 | `artifacts/manifests/` 是长期治理证据层，但旧 secret scan 未覆盖。 | manifest 可能成为 secret 残留入口，且会被索引和检索长期引用。 | 将 `artifacts/manifests` 加入 `scan_roots`。 |
| MSS-002 | `artifacts/` 也可能包含大文件、日志或二进制引用。 | 全量扫描 `artifacts/` 容易误扫非文本制品并增加维护成本。 | 本轮只扫描 `artifacts/manifests/`，不扫描整个 `artifacts/`。 |
| MSS-003 | 历史 manifest 需要先确认不会触发误报。 | 直接加门禁可能阻塞已有仓库。 | 先用同等正则扫描当前文本层，未发现命中。 |

## 决策

- `knowledge-check` 的 secret scan 覆盖 `domains/`、`registry/`、`governance/`、`templates/` 和 `artifacts/manifests/`。
- 不扫描整个 `artifacts/`，避免把制品存放层误变成重型内容扫描器。
- 若未来需要扫描更多 artifact 子目录，必须先登记数据类型、文件大小上限、文本扩展名和误报处理方式。

## 非目标

- 不修改源项目 docs。
- 不复制或扫描外部大文件正文。
- 不引入依赖或复杂 secret scanner。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## 验证计划

- `rtk rg -n -e "-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----" -e "(?i)(api[_-]?key|token|password|passwd|secret)\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]{12,}" -e "(?i)cookie\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]{12,}" artifacts/manifests registry governance templates domains`
- `rtk bash -n tools/knowledge-check.sh`
- `rtk jq -c . artifacts/manifests/knowledge-hub-manifest-secret-scan-gate-20260619.jsonl`
- `rtk jq -c . registry/items.jsonl`
- `rtk jq -c . registry/migrations.jsonl`
- `rtk bash tools/knowledge-check.sh --dry-run --json`
- `/tmp` 负向验证：复制仓库后在 `artifacts/manifests/secret-fixture.md` 写入一个 token 形态的长值，`knowledge-check` 应报 `secret-pattern:artifacts/manifests/secret-fixture.md`。
- `rtk bash tools/knowledge-search.sh "manifest-secret-scan-applied" --json`

## 结果

已落地并验证通过。

- 当前 `artifacts/manifests`、`registry`、`governance`、`templates` 和 `domains` 文本层未命中 secret pattern。
- `knowledge-check --dry-run --json` 通过。
- `knowledge-check --sources-only --dry-run --json` 通过，保持 source-only 语义不变。
- `manifest-secret-scan-applied` 可通过 `knowledge-search` 回查到 registry、status index 和本 manifest。
- `/tmp` 负向验证通过：在仓库副本的 `artifacts/manifests/secret-fixture.md` 写入 token 形态长值后，`knowledge-check` 返回失败并报告 `secret-pattern:artifacts/manifests/secret-fixture.md`。
