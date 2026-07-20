# embedded-knowledge 覆盖状态

## 结论

- Status: `superseded-by-terminal-domain-canonicalization`
- Classification: `retired-origin copy-docs`
- Checked at: `2026-06-25`

## 决策

embedded-knowledge 的 2026-06-24 source canonicalization 记录已被 2026-06-25 终态归位取代；当前正文权威为 domains/embedded/*，sources/embedded-knowledge 只保留 source 控制面。

## 风险

历史 team knowledge 不自动成为 active standard；后续提升仍需按 Hub owner/review 规则拆分。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/embedded-knowledge/inventory.jsonl`

## 2026-07-18 远端身份复核

- Remote：使用本地受控映射 `source://embedded-knowledge`；长期正文不保存内部网络端点。
- Verified ref：`refs/heads/main` = `cadbf4d6777319c8d43b15f842cbea002cd94cef`。
- Scope：项目 dev 副本中的 178 个非缓存文件由该 commit 精确保留；7 篇 SSC305 方法已提炼为 PCR02/SSC305 reviewing 候选，工具和仓库治理文件保持 source reference。
- Boundary：不复制第二套可执行工具，不提升 active，不修改远端；13 个 `.pyc` 和嵌套 `.git` 不进入长期正文。
- Evidence：`projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md`、`artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`。
