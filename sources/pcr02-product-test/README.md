# pcr02-product-test

## 定位

- Source ID: `pcr02-product-test`
- Hub source path: `sources/pcr02-product-test`
- Role: `hub-canonical-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hub-canonical`
- Source strategy: `hub-canonical-copy-docs-and-artifacts`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-product-test 旧正文副本已按终态剪枝；旧 app_product_test 路径不再作为知识 source path，明确附件仍由 artifact vault/provenance 表达。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

源码、构建产物和产测运行结果不得混入文本知识层。

## 维护入口

- 清单：`sources/pcr02-product-test/inventory.jsonl`
- 覆盖：`sources/pcr02-product-test/coverage.md`
- 策略：`sources/pcr02-product-test/source-policy.md`
