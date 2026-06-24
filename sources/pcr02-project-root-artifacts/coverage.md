# pcr02-project-root-artifacts 覆盖状态

## 结论

- Status: `registered-mixed-artifact-tool-boundary`
- Classification: `mixed artifact-ref + archive-only + tool-ref + classify-first candidate`
- Checked at: `2026-06-24`

## 决策

PCR02 root loose artifacts 使用边界化登记，排除子 source 和生成物。

## 风险

.bin/.log/.patch/.sh/.py 不复制正文；抽取事实需 owner review。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-project-root-artifacts/inventory.jsonl`
