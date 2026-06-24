# PCR02 product-test artifact/config/interface identity 2026-06-21

## 结论

本轮为 `pcr02-product-test` 补充只读身份清单，将 `app_product_test` 中非生成物文件的 `source_path`、`uri`、`size`、`sha256`、分类和引用模式固定到 Knowledge Hub。

该清单只证明“当前源文件身份可复核”，不迁移正文、不展开附件、不执行 build/test、不复制 C/C++ 源码、不关闭 owner gate、不把任何内容提升为 active 或团队标准。

## 范围

- Source ID: `pcr02-product-test`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test`
- Identity JSONL: `artifacts/manifests/pcr02-product-test-artifact-config-interface-identity-20260621.jsonl`
- 采集方式：只读遍历，显式排除 `.git/**`；对 `.o/.d` 生成物只做聚合排除，不逐个登记 hash。

## 统计

| 类别 | 数量 | 本轮处理 |
|---|---:|---|
| Markdown | 4 | 逐文件登记身份，保持 `classify-first-owner-gated` |
| PDF | 2 | 逐文件登记 `artifact-ref-no-body-copy` |
| zip/tgz | 2 | 逐文件登记 `artifact-ref-no-extract` |
| ini/toml/build config | 7 | 逐文件登记 config/build-config reference |
| C/C++ | 54 | 逐文件登记 interface/diagnostic/validation reference，不复制源码 |
| patch/backup/png/source-control metadata | 4 | 逐文件登记 artifact/excluded 边界 |
| `.o/.d` generated artifacts | 54 | 聚合排除，不进入 identity JSONL |
| `.git/**` | 319 | 显式排除，不进入 Knowledge Hub 资产层 |

## 控制规则

- Markdown 仍需 owner 决策后才能 copy-first、reference-first、no-migration 或 owner-gated 继续保留。
- `PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` 与 PDF 的 canonical body 仍需 owner 决策。
- 配置文件只记录 hash/size，不复制配置值；敏感性和环境绑定仍需 owner 判断。
- PDF、zip、tgz 只登记 artifact identity，不展开、不抽取正文。
- C/C++ 只作为 interface/diagnostic/validation reference，不复制源码正文。
- `.o/.d` 生成物默认排除，不进入文本知识层。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-status.sh --json` | 0 | 当前状态为 `needs-owner-review`，`source_check_health` 无缺口，`boundary_health=pass` | `tools/knowledge-status.sh` | Status | `pcr02-product-test-artifact-config-interface-identity-20260621` |
| `rtk bash -lc 'base=.../app_product_test; find "$base" -path "$base/.git" -prune -o -maxdepth 4 -type f -printf "%P\t%s\n" | sort'` | 0 | 排除 `.git/**` 后列出 127 个源文件身份候选 | `pcr02-product-test` source | Source Identity | `pcr02-product-test-artifact-config-interface-identity-20260621` |
| `rtk bash -lc '... awk ...'` | 0 | 统计 4 Markdown、2 PDF、2 archive、7 config、54 source、54 generated、4 other | `pcr02-product-test` source | Source Identity | `pcr02-product-test-artifact-config-interface-identity-20260621` |
| `rtk bash -lc '... sha256/size identity generator ...'` | 0 | 为 73 个非生成物文件生成 source identity JSONL 草案 | `artifacts/manifests/pcr02-product-test-artifact-config-interface-identity-20260621.jsonl` | Source Identity | `pcr02-product-test-artifact-config-interface-identity-20260621` |
| subagent `pcr02-product-test identity` | 0 | 建议落地 reference-only / owner-gated 身份清单，保持 owner gate 不变 | subagent read-only review | Subagent Review | `pcr02-product-test-artifact-config-interface-identity-20260621` |

## 未决项

- 4 个 Markdown 的最终迁移策略仍需 owner decision。
- 同名 Markdown/PDF 的 canonical body 仍需 owner decision。
- 配置文件是否可作为 config-ref 继续引用、是否需要更强 secret/env review，仍需 owner decision。
- patch、backup、png 是否保留为长期 artifact-ref，仍需 owner decision。
