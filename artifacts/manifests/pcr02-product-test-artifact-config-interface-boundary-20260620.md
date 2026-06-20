# PCR02 product-test artifact/config/interface boundary 2026-06-20

## 结论

`pcr02-product-test` 已完成只读边界复核。该目录是产测应用、配置、校准示例、附件和构建残留混合源。当前不得迁移源码正文，不得展开 PDF/zip/tgz，不得把 `.o/.d` 生成物放入 active 知识层。后续只能按 owner 决策对 Markdown 做 `classify-first` 后处理，对 PDF/压缩包做 `artifact-ref`，对配置做 `config-ref` 或降级 artifact/excluded，对 C/C++ 做 interface/diagnostic/validation reference。

## 范围

- Source ID: `pcr02-product-test`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test`
- 扫描方式：只读路径分类；未执行 build/test，未展开附件，未复制源码正文。

## 统计

| 类别 | 数量 | 决策 |
|---|---:|---|
| Markdown | 4 | `classify-first`，owner 决策前不迁移正文 |
| PDF | 2 | `artifact-ref` |
| zip/tgz | 2 | `artifact-ref` |
| ini/config | 3 | `config-ref`，敏感或环境绑定时降级 |
| C/C++ | 54 | interface/diagnostic/validation reference，不复制正文 |
| object/dep/build artifacts | 54 | 默认 excluded；仅证据需要时 artifact-ref |
| other | 8 | 单独边界登记 |

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险与后续 |
|---|---|---|---|
| `DEVELOPMENT_PLAN.md` | `product-test-plan-candidate` | `classify-first` | owner 决定 copy-first/reference-first/owner-gated/no-migration。 |
| `PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` | `product-test-guide-candidate` | `classify-first` | 与同名 PDF 需确定 canonical body，避免正文重复。 |
| `TECHNICAL_DESIGN.md` | `product-test-design-candidate` | `classify-first` | owner 决策前不声明 active。 |
| `examples/imu/imu_turntable_calibration.md` | `calibration-guide-candidate` | `classify-first` | 偏 validation/calibration reference，需 owner 决策。 |
| `PRODUCT_TEST_INI_PRODUCTION_GUIDE.pdf` | `product-test-guide-pdf-artifact` | `artifact-ref` | 不展开、不复制正文；需 canonical body 决策。 |
| `examples/VOSEN产品SN编码规范-V0.2-20260327.pdf` | `sn-spec-pdf-artifact` | `artifact-ref` | 需确认来源、有效性和是否可引用。 |
| `examples/ai_get_extrinsic.zip`、`examples/imu_calibration_prog.tgz` | `calibration-attachment-artifact` | `artifact-ref` | 不展开压缩包，不进入文本知识层。 |
| `product_test.ini`、`version.ini`、`examples/tof/sensor_calibration.toml` | `product-test-config-ref` | `config-ref-or-artifact-boundary` | 需 secret/env-specific check；可能包含产线或设备参数。 |
| `pt_main.c`、`pt_common.*` | `product-test-app-interface-ref` | `interface-reference` | 不复制源码正文，只登记接口/职责边界。 |
| `pt_diag_bridge.*` | `diagnostic-interface-ref` | `diagnostic-reference` | 作为诊断桥接接口引用，不提升为标准。 |
| `pt_sn_validator.*` | `sn-validation-ref` | `validation-reference` | 作为 SN 校验逻辑引用，不复制源码。 |
| `pt_calibration*`、`examples/camera/*`、`examples/imu/*`、`examples/tof/*` | `calibration-validation-ref` | `validation-reference` | 校准和处理逻辑只作为验证引用。 |
| `pt_hw_*.c` | `hardware-diagnostic-ref` | `diagnostic-reference` | 硬件产测逻辑只作为诊断引用。 |
| `pt_font_*.h`、`pt_ss_font_info.h` | `font-data-artifact` | `excluded-or-artifact-ref` | 更像数据表，不作为 interface reference 正文。 |
| `*.user.arm.o`、`*.user.arm.d` | `build-artifact-generated` | `excluded` | 生成物或依赖文件，不进 active 知识层。 |
| `.clang-format`、`app_product_test.mk`、`dep.mk`、`examples/camera/CMakeLists.txt` | `build-config-ref` | `config-ref` | 可登记构建配置边界，不自动迁移。 |
| `.gitignore` | `source-control-metadata` | `excluded` | 源控元数据不进入知识层。 |
| `examples/camera/chessboard_fixed_region_5.png`、`pt_bt.patch`、`pt_hw_bt.backup` | `misc-artifact-boundary` | `artifact-ref-or-owner-gated-excluded` | patch/backup 需 owner 判定是否保留。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不复制 C/C++ 源码正文 | enforced-by-boundary |
| 不展开 PDF/zip/tgz | enforced-by-boundary |
| `.o/.d` 默认排除 | enforced-by-boundary |
| Markdown 需 owner 决策后再迁移 | owner-gated |
| 配置文件需 secret/env-specific check | owner-gated |
| 同名 Markdown/PDF 需 canonical body 决策 | owner-gated |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc 'base=.../app_product_test; for pat in ...; find "$base" ...'` | 0 | 按 Markdown、PDF、zip/tgz、配置、C/C++、生成物列出路径，未读取附件正文 | `pcr02-product-test` | Source scan | `pcr02-product-test-artifact-config-interface-boundary-20260620` |
| subagent `PCR02-PRODUCT-TEST-BOUNDARY` | 0 | 只读扫描完成；确认 4 个 Markdown、2 个 PDF、2 个压缩包、3 个配置、54 个 C/C++、54 个生成物、8 个 other | `pcr02-product-test` | Subagent evidence | `pcr02-product-test-artifact-config-interface-boundary-20260620` |

## 未决项

- owner 需要决定 4 个 Markdown 的最终状态。
- owner 需要确认 `PRODUCT_TEST_INI_PRODUCTION_GUIDE.md` 与 PDF 的 canonical body。
- owner 需要确认 3 个配置文件是否可做 config-ref，或必须排除正文。
- patch、backup、png 是否保留为 artifact-ref 需要 owner 判定。
