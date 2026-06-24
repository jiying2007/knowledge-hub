# pcr02-product-test

## 定位

- Source ID: `pcr02-product-test`
- Source path: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test`
- Role: `project-product-test-source`
- Authority: `legacy-project-product-test`
- Final disposition: `mixed-terminal-coverage`
- Migration strategy: `artifact-config-interface-validation-reference`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

PCR02 product test 作为产品测试资料源登记；二进制、PDF、压缩包和源码只做引用或 artifact-ref。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

构建产物和源码不得进入文本知识层。

## 维护入口

- 清单：`sources/pcr02-product-test/inventory.jsonl`
- 覆盖：`sources/pcr02-product-test/coverage.md`
- 计划：`sources/pcr02-product-test/migration-plan.md`
