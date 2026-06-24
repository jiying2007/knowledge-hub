# pcr02-project-root-artifacts 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin project-root-shallow`
- Checked at: `2026-06-24`

## 决策

pcr02-project-root-artifacts 的根部可读文本已按 shallow policy 迁入 Hub；项目根目录不再作为知识 source path。

## 风险

root loose artifact、日志、patch、脚本和生成物不得被复制为 Hub 正文。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-root-artifacts/inventory.jsonl`
