---
title: SSC305 飞书知识库目录与维护规范
doc_type: standard
knowledge_type: guideline
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, feishu, knowledge-map, tools, methods]
related: [../architecture/sigmastar-platform-internal-overview.md, ../architecture/sigmastar-platform-capability-matrix.md, sigmastar-platform-topic-catalog.md, ../runbooks/ssc305-sigdoc-lookup-method.md, ../runbooks/ssc305-build-burn-upgrade-method.md, ../runbooks/ssc305-debug-toolchain-method.md, ../runbooks/ssc305-media-sensor-ai-triage-method.md, ../runbooks/ssc305-dualos-cm4-low-power-method.md, ../runbooks/ssc305-diag-regression-method.md]
validation_refs: [../archive/sigmastar/manifest.csv, sigmastar-platform-topic-catalog.md]
---

# SSC305 飞书知识库目录与维护规范

## 1. 目标

本文定义 SSC305 平台知识库上传到飞书后的目录结构、文档边界和维护规则。

适用对象：

1. 平台开发人员：快速定位 `SSC305_sigdoc` 中的主题和工具链资料。
2. 应用开发人员：按构建、调试、媒体链路、诊断回归等方法闭环问题。
3. 测试与现场支持：用统一术语描述问题、收集证据、回传复现材料。

## 2. 资料来源

当前知识化资料基于以下来源整理：

| 来源 | 用途 | 边界 |
| --- | --- | --- |
| `sigmastar-ssc305-20260516-v2` | SSC305 官方 sigdoc 归档实体 | 只作为可追溯证据，不直接复制原文 |
| `docs/standards/sigmastar-platform-topic-catalog.md` | 115 个 SSC305 主题索引 | 用于查找主题 ID、技术域和原始路径 |
| `docs/architecture/sigmastar-platform-internal-overview.md` | 平台分层模型 | 用于统一解释 BSP、MI、算法、DualOS/CM4 和产品工程层 |
| 项目仓 `docs/` 与 `tools/` | 已验证的项目方法和工具入口 | 只提炼跨项目方法，不把单项目路径写成平台规范 |

## 3. 飞书目录建议

建议在飞书中建立知识库：

```text
SSC305 平台工具与方法
```

一级目录建议：

| 飞书目录 | 对应文档 | 目标 |
| --- | --- | --- |
| 00 导览与索引 | 本文 | 让新人知道先看什么、怎么搜索、怎么维护 |
| 01 资料定位方法 | `ssc305-sigdoc-lookup-method.md` | 把问题映射到 sigdoc 主题 ID 和能力域 |
| 02 构建烧录升级 | `ssc305-build-burn-upgrade-method.md` | 建立从源码到设备运行的交付闭环 |
| 03 调试工具链 | `ssc305-debug-toolchain-method.md` | 统一 runtime baseline、core、ASAN、依赖审计等工具 |
| 04 媒体与 AI 链路 | `ssc305-media-sensor-ai-triage-method.md` | 处理 Sensor、VIF/ISP、编码、IPU/算法问题 |
| 05 DualOS/CM4/低功耗 | `ssc305-dualos-cm4-low-power-method.md` | 处理快启、STR、CM4 与电源协同问题 |
| 06 诊断与回归 | `ssc305-diag-regression-method.md` | 用 diag/prog_tool 建立可重复测试闭环 |

## 4. 导入顺序

上传飞书时按以下顺序导入，避免读者先看到局部命令而缺少上下文：

1. `ssc305-feishu-knowledge-map.md`
2. `sigmastar-platform-internal-overview.md`
3. `sigmastar-platform-capability-matrix.md`
4. `sigmastar-platform-topic-catalog.md`
5. `ssc305-sigdoc-lookup-method.md`
6. `ssc305-build-burn-upgrade-method.md`
7. `ssc305-debug-toolchain-method.md`
8. `ssc305-media-sensor-ai-triage-method.md`
9. `ssc305-dualos-cm4-low-power-method.md`
10. `ssc305-diag-regression-method.md`

## 5. 标签规范

飞书标签建议使用四段式：

```text
平台 / 阶段 / 能力域 / 工具或方法
```

示例：

| 场景 | 标签 |
| --- | --- |
| Sensor 移植 | `SSC305`、`开发`、`BSP`、`Sensor` |
| 媒体链路黑屏 | `SSC305`、`调试`、`MI`、`VIF/ISP` |
| AI 推理异常 | `SSC305`、`调试`、`IPU`、`算法接入` |
| STR 耗时过长 | `SSC305`、`优化`、`DualOS`、`低功耗` |
| 诊断回归 | `SSC305`、`测试`、`diag`、`prog_tool` |

## 6. 搜索词规范

在飞书中搜索时优先组合以下字段：

```text
SSC305 + 技术域 + 问题类型 + 工具名
```

推荐搜索词：

| 问题 | 搜索词 |
| --- | --- |
| 找不到官方资料 | `SSC305 sigdoc 主题索引` |
| 构建失败 | `SSC305 构建 方法 make install` |
| 运行期资源异常 | `SSC305 runtime baseline 调试工具` |
| core 分析 | `SSC305 core fastpass 二进制匹配` |
| Sensor 无图 | `SSC305 Sensor VIF ISP 排障` |
| AI 无检测结果 | `SSC305 IPU 算法 输入格式` |
| 快启慢 | `SSC305 DualOS STR TTFF TTUFF` |
| 自动化回归 | `SSC305 diag prog_tool suite` |

## 7. 维护规则

1. 新增知识必须先判断归属：平台通用内容放入 `knowledge/docs`，项目强绑定内容留在项目仓 `docs`。
2. 每篇文档必须说明适用范围、输入材料、步骤、失败路径和验证方式。
3. 引用 sigdoc 时只写 `archive_id`、主题 ID、技术域和路径，不复制大段原文。
4. 现场日志、core、SDK 压缩包、客户信息不得上传到 Git 或飞书正文；应进入受控问题单、NAS 或制品库。
5. 修改知识库文档后至少运行文档 schema、命名、链接检查。

## 8. 版本追溯

当前 SSC305 资料归档实体：

| 字段 | 值 |
| --- | --- |
| `archive_id` | `sigmastar-ssc305-20260516-v2` |
| `platform` | `SSC305` |
| `snapshot_date` | `2026-05-16` |
| `sitemap_lastmod` | `2025-05-26` |
| `zh_page_count` | `115` |

若后续 sigdoc 升级，必须新增归档实体并更新 `docs/archive/sigmastar/manifest.csv`，不要覆盖旧记录。
