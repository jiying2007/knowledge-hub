---
id: gd32l235-charge-chain-pdf-text-index-20260720
title: GD32L235 充电链三份 PDF 派生全文索引
kind: project-archive
domain: projects/gd32l235
path: projects/gd32l235/archive/reference/2026-07-20-charge-chain-pdf-text-index.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: user-provided-local-pdf-derived-text
  from: workspace://mcu
review_after: '2026-10-20'
review_status: manual-entry-pending-review
promotion: none
promotion_decision: archive-only
tags:
- gd32l235
- charging
- sc8922
- cw2217
- battery-pack
- datasheet
- pdf-text
related:
- projects/gd32l235/archive/debug/2026-07-20-dock-discharge-cw2217-zero-data-initial-analysis.md
validation_refs:
- projects/gd32l235/archive/reference/2026-07-20-charge-chain-pdf-text-index.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
summary_zh: 保存 SC8922、CW2217BAAD 与 CXY18650-2S 电池承认书的 PDF 派生 UTF-8 全文，供后续直接检索；正文不替代原 PDF 的表格、曲线、原理图和版式证据。
primary_language: zh-CN
source_language: mixed
translation_status: source-language-preserved
terminology_status: pending-review
evidence_strength: direct-local-document-extraction
evidence_validation_status: pending
generated_by_ai: true
ai_role: extracted
ai_model_or_tool: Codex and pdftotext
ai_generated_at: '2026-07-20'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
---

# GD32L235 充电链三份 PDF 派生全文索引

## 用途

本目录保存三份充电链资料的 PDF 文本层提取结果，后续可直接用编辑器、`rg` 或 Knowledge Hub 搜索，不必再次执行 PDF 转文本。

派生文本保持 PDF 原始语言：SC8922、CW2217 以英文技术原文为主，电池承认书以中文和英文混排为主。没有对英文全文做机器翻译，避免寄存器名、位定义、公式、阈值和时序在翻译中失真。相关中文理解和初步结论见配套排障记录。

## 可直接查阅的全文

| 资料 | 派生全文 | 页数 | 文本大小 | 文本 SHA-256 |
| --- | --- | ---: | ---: | --- |
| SC8922 2/3 节升压充电与 power-path datasheet | [sc8922-datasheet-text.txt](sc8922-datasheet-text.txt) | 18 | 57,708 bytes | `3d6da67058c005b02dc271a552ac65360ab4ad7ffff8e139a682ba7d26dc4568` |
| CW2217BAAD 电量计 datasheet | [cw2217baad-datasheet-text.txt](cw2217baad-datasheet-text.txt) | 24 | 60,343 bytes | `b2d268b23dab21a3944f42f5ca7df78f080040ad604df652bc894ca60f5fd583` |
| CXY18650-2S 7.4V 2500mAh 电池承认书 | [cxy18650-2s-7v4-2500mah-approval-20260622-text.txt](cxy18650-2s-7v4-2500mah-approval-20260622-text.txt) | 13 | 35,685 bytes | `43f339f72ad23e766eb04a087c4c9472998834b75aa4fbef7ba4896f95fc6c90` |

## 原 PDF 身份

| 原文件 | Source URI | 大小 | SHA-256 |
| --- | --- | ---: | --- |
| `SC8922.pdf` | `workspace://mcu/SC8922.pdf` | 1,914,951 bytes | `7a209bcff3307e1d89d964250f683d0a12b52bc311fd36dd8caba3efde8c4f65` |
| `CW2217BAAD.pdf` | `workspace://mcu/CW2217BAAD.pdf` | 1,083,102 bytes | `efd2bc4b8702330c94a51e93ed017d5287a203f828a8473a651256ef068aa6a9` |
| `视壮科技 CXY18650-2S 7.4V-2500mAh 侧面加板2MOS(8)+10K 1% B=3435 2.0-4P外露60mm 电池承认书20260622.pdf` | `workspace://mcu/视壮科技 CXY18650-2S 7.4V-2500mAh 电池承认书20260622.pdf` | 602,040 bytes | `74d56c31efd7ca0613920d4c98aa00a2b34c896ef86afe128b9e12a123af0868` |

## 转换方式

```text
pdftotext -layout <source.pdf> <derived-text.txt>
```

电池承认书的 PDF 字体层包含少量不可见控制字符。转换后仅删除了 `0x00-0x08`、`0x0B-0x0C`、`0x0E-0x1F` 和 `0x7F` 控制字符；没有改写任何可见文字、数值或表格内容。三份结果均已确认为 UTF-8 文本。

## 检索提示

- SC8922：`Safety Timer`、`Automatic Recharge`、`Power Path Management`、`NTC`、`PG`、`VINREG`。
- CW2217：`REG_CONFIG`、`REG_SOC_ALERT`、`UPDATE_FLAG`、`REG_TEMP`、`IC_STATE`、`FW_VERSION`、`shutdown mode`。
- 电池包：`过充保护`、`过放保护`、`静态工作电流`、`充电温度`、`B=3435`、`2MOS`。

例如：

```bash
rtk rg -n "Safety Timer|Automatic Recharge|NTC" projects/gd32l235/archive/reference/sc8922-datasheet-text.txt
rtk rg -n "REG_CONFIG|UPDATE_FLAG|REG_TEMP|IC_STATE" projects/gd32l235/archive/reference/cw2217baad-datasheet-text.txt
rtk rg -n "过放|静态工作电流|充电温度|B=3435" projects/gd32l235/archive/reference/cxy18650-2s-7v4-2500mah-approval-20260622-text.txt
```

## 使用边界

- 这些文件是 PDF 文本层的派生副本，不是重新排版后的正式 datasheet。
- 表格列对齐、图形、曲线、波形、引脚图和原理图必须回看原 PDF；文本不能替代视觉证据。
- OCR/字体映射可能产生个别字符错误，作设计决策前应以原 PDF 对应页为准。
- SC8922 文件标有 preliminary/confidential 属性，来源许可证未确认；仅限团队内部排障参考，不对外分发。
- 本索引和派生全文均为 `archive-only/reviewing`，不代表 owner 已确认，也不自动提升为当前设计规范。

## Review

- owner：leiwenjun
- review_after：2026-10-20
- 下一次复核：抽查关键阈值、寄存器表、公式和表格文本是否与 PDF 页面一致。
