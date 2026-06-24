# pcr02-product-test 覆盖状态

## 结论

- Status: `hard-migrated-to-hub`
- Classification: `retired-origin copy-docs-and-artifacts`
- Checked at: `2026-06-24`

## 决策

pcr02-product-test 文档与明确文档附件已硬迁移到 Hub；旧 app_product_test 路径不再作为知识 source path。

## 风险

源码、构建产物和产测运行结果不得混入文本知识层。

## 证据

- `registry/sources.json`
- `artifacts/manifests/knowledge-hub-source-coverage-closeout-20260624.jsonl`
- `sources/pcr02-product-test/inventory.jsonl`
