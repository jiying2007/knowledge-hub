---
id: txt-reader-product-and-technical-plan-20260801
title: TXT 阅读器产品与技术落地方案候选
kind: personal-note
domain: notes
path: notes/personal/2026-08-01-txt-reader-product-and-technical-plan.md
scope: team-general
visibility: personal-local
status: personal
owner: leiwenjun
source:
  type: current-session-research
  from: '2026-08-01 current Codex session: DeepSeek share review, public-source research, and local reference APK static analysis'
  source_sha256: 95071109fc6ec058a1a9698310ec41af74ac32d101004bd626e387f64fa08796
  temporary_source_retained: false
review_after: '2026-11-01'
review_status: personal-local
content_review_status: not-required
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- txt-reader
- android
- harmonyos
- product-research
- local-first
validation_refs:
- notes/personal/2026-08-01-txt-reader-product-and-technical-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- notes/personal/2026-08-01-txt-reader-product-and-technical-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-01'
updated_at: '2026-08-01'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-01'
manual_validation_pending: true
summary_zh: 沉淀 TXT 阅读器竞品、参考 APK、产品定位、Android/HarmonyOS 技术候选、MVP、W0 门禁、合规与商业验证假设；仅为个人研究候选，不代表技术或市场已验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# TXT 阅读器产品与技术落地方案候选

## 摘要

本记录沉淀 2026-08-01 对 TXT 阅读器市场、参考 APK、Android/HarmonyOS 平台能力及合规边界的研究结论。建议产品定位为“面向大文件、乱码和排版混乱文本的本地阅读与可逆清洗工具”，工作名“净读 TXT”。本文是 research/archive candidate，不代表产品需求、技术选型、性能目标或商业模型已经由用户、真机或市场验证。

## 背景与目标

- 类型：新产品。
- 优先级候选：P1 重要。
- 目标用户：持有合法本地 TXT 的长篇读者、写作者和资料阅读者，尤其面对错误编码、脏排版、大文件及 Android/HarmonyOS NEXT 双端需求的人群。
- 核心价值：大文件稳定性、中文脏文本可逆清洗、权限克制、Android 与纯鸿蒙一致的工作流。
- 建议口号：TXT 再乱，也能快速开读；原文不动，阅读更干净。

## 研究输入与证据边界

- DeepSeek 分享对话：<https://chat.deepseek.com/share/54r2cshnypu36jfmrp>，retrieved_at: 2026-08-01。
- 本地 `txt_ref_apps` 中 6 个 APK：仅做 AndroidManifest、组件、权限和 DEX 字符串静态分析；没有安装、真机交互或网络行为测试，也不归档 APK 二进制。
- ReadEra Google Play：<https://play.google.com/store/apps/details?id=org.readera>，retrieved_at: 2026-08-01。
- Moon+ Reader Pro Google Play：<https://play.google.com/store/apps/details?id=com.flyersoft.moonreaderp>，retrieved_at: 2026-08-01。
- Android Storage Access Framework：<https://developer.android.com/training/data-storage/shared/documents-files>，retrieved_at: 2026-08-01。
- Google Play Target API 要求：<https://developer.android.com/google/play/requirements/target-sdk>，retrieved_at: 2026-08-01。
- KuiklyUI：<https://github.com/Tencent-TDS/KuiklyUI>，retrieved_at: 2026-08-01。
- Flutter OpenHarmony：<https://gitee.com/openharmony-sig/flutter_flutter/blob/master/README.en.md>，retrieved_at: 2026-08-01。
- HarmonyOS Reader Kit：<https://developer.huawei.com/consumer/cn/doc/harmonyos-guides/reader-introduction>，retrieved_at: 2026-08-01。
- Google Play 知识产权政策：<https://support.google.com/googleplay/android-developer/answer/9888072?hl=en>，retrieved_at: 2026-08-01。
- 华为应用隐私保护：<https://developer.huawei.com/consumer/cn/doc/doccenter-architecture/bpta-app-privacy-protection>，retrieved_at: 2026-08-01。

外部网页仅保存事实摘要、链接和检索日期，不复制受版权保护的长篇正文。DeepSeek 分享内容只作为方案来源之一，不提升为权威事实。

## 关键判断

1. 不应做“支持 TXT 的通用阅读器”。ReadEra 已覆盖离线、多格式、书架、目录、书签、标注和进度等通用基线，正面比拼格式数量缺乏优势。
2. 自动滚动和名字替换不能作为独占卖点。Moon+ Reader 已有多种自动滚动和 Name Replacement；它们应是辅助功能。
3. “不要书架”不适合长篇留存。MVP 至少需要最近阅读、进度、目录和书签。
4. 不应承诺自动还原被屏蔽词。正确方式是用户显式规则、批量预览、按书或全局作用、撤销和导出；原文件永不覆盖。
5. “100MB 秒开依赖 mmap”不成立为通用方案。系统文件选择器可能返回云端或虚拟 URI，应使用分块读取、渐进呈现、私有副本和后台索引。
6. 产品不能包含在线书源、爬虫、下载器或侵权样书；目标内容限定为用户合法持有或公共领域文本。

## 产品范围

### P0 / MVP

- 系统文件选择器导入及“打开方式”接入；原子复制到应用私有空间。
- UTF-8/BOM、GBK、GB18030、GB2312、UTF-16 LE/BE 检测和手动覆盖；Big5 先做技术验证。
- 最近阅读书架、进度、目录、书签和删除。
- 章节识别，并允许合并、拆分和改名。
- 连续滚动与翻页、日夜/护眼主题、字号、行距和边距。
- 书内全文搜索和上下文片段。
- 净读层：断行、空行、重复章节、网址/广告尾巴扫描；字面替换规则；修改预览、撤销和导出清洗副本。
- 自动滚动、速度调节和暂停。
- 低存储、导入中断和异常退出恢复。

### P1 候选

- 全局/单书规则包导入导出。
- 本地“人物回忆”：基于名字定位首次、最近和关键上下文，不依赖云端 AI。
- 本地 TTS、手动备份包、可选 WebDAV、平板和折叠屏布局。

### 非目标

- 书城、在线书源、爬虫、下载器、UGC、云账号、广告。
- PDF/Office、完整编辑器、MVP EPUB、自动猜词和默认上传正文的 AI。

## 技术候选

优先验证 Kuikly/Kotlin Multiplatform 共享书架、设置、规则和领域逻辑，两端保留原生 ReaderSurface：

- Android：Storage Access Framework、平台字符集和原生排版/滚动组件，直接面向 targetSdk 36。
- HarmonyOS NEXT：DocumentViewPicker、ArkUI/Reader Kit 及平台存储适配器。
- 共享契约：加载文本窗口、排版参数、阅读模式、锚点定位、当前位置、选择文本和事件回调。
- 数据库存储通过接口隔离：Android SQLite/Room 与 Harmony relationalStore，不强求未经验证的共享 SQL 插件。
- 内部文本转为 UTF-8 分段文件，章节、搜索和问题索引后台构建；不把整本书读入单一内存字符串。
- 中文搜索优先验证 Unicode n-gram 倒排索引，避免跨平台 FTS 中文分词差异。
- 阅读锚点由段落哈希、字节/字符偏移和上下文哈希组成，降低换字体、主题和净读规则后的进度漂移。

如果 W0 发现原生组件桥接或 Harmony KMP 工具链不稳定，回退为 Android Compose + Harmony ArkUI/Reader Kit 双原生 UI，共享产品规范、算法和测试语料。Flutter OpenHarmony 与 ArkUI-X 作为备选，不在未验证插件和平台版本前做主选型承诺。

## W0 技术门禁

正式开发前用 5 个工作日验证：

1. Kuikly 页面能否稳定嵌入 Android/Harmony 原生 ReaderSurface。
2. 10MB、100MB、300MB TXT 的首屏、后台索引、内存和中断恢复。
3. Harmony Reader Kit 对标准化 TXT 的排版、目录和锚点映射。
4. GB18030、UTF-16、Big5 和损坏字节语料。
5. 字号、主题和净读规则变化后的稳定定位。

Go 条件应至少覆盖：100MB 文件选择后首屏目标小于 1.5 秒、峰值 RSS 目标小于 180MB、300MB 压测无 OOM、位置漂移不超过一个段落、原文件逐字节不变、两端对相同语料产生一致编码/章节/净读结果。以上均为待实测目标，不是已通过证据。

## 实施节奏

- W0：技术验证和 Go/No-Go。
- W1：工程骨架、数据模型、测试语料。
- W2：导入、编码、分段存储和索引。
- W3：Android ReaderSurface。
- W4：Harmony ReaderSurface 与 Reader Kit 适配。
- W5：书架、目录、进度、书签和搜索。
- W6：净读规则、预览、撤销、导出和自动滚动。
- W7：双端回归、性能、无障碍和大字体。
- W8：30–50 人封闭测试、隐私政策和商店材料。
- W9–W10：反馈修复和发布准备。

个人全职开发估算为 8–10 周；兼职估算 12–16 周。每个共享功能应在同一迭代通过 Android 和 Harmony 验证，避免最后集中移植。

## 商业与验证假设

- 内测免费；正式版优先测试“免费核心 + 一次性 Pro”，不使用广告。
- 可测试首发价 28 元、常规价 38 元；在出现持续云成本前不做订阅。
- 30–50 名封测用户中至少收集 20 份合法持有且存在编码/排版问题的 TXT 案例。
- 早期目标：激活率不低于 65%、D7 不低于 25%、D30 不低于 12%、净读层活跃使用率不低于 30%、导入失败率低于 1%。
- 至少 10 名用户明确把净读、大文件或 Harmony 支持作为换用理由，且付费意向达到 5% 后再接入支付。
- 分析数据默认关闭或显式 opt-in，禁止收集书籍正文；诊断材料由用户主动导出。

上述价格、留存和转化率均为验证假设，不是市场事实。

## 风险与缓解

| 风险 | 缓解 |
| --- | --- |
| Kuikly/Reader Kit 桥接失败 | W0 技术门禁；保留双原生回退 |
| 编码误判 | 置信度、手动覆盖、固定测试语料 |
| 净读误伤正文 | 显示层虚拟变换、预览、撤销、原文不改 |
| 大文件 OOM 或卡顿 | 分块管线、后台索引、禁止整书大字符串 |
| 产品差异化不足 | 先验证 10 名用户的明确换用理由 |
| 版权与商店合规 | 不提供内容源/下载能力，仅使用原创或公共领域样书 |
| 个人开发范围膨胀 | MVP 冻结为 TXT、本地和双端核心链路 |

## 当前状态与后续

- 当前只有研究方案和静态证据，没有代码、真机性能数据、动态 APK 测试、产品命名审查或用户访谈。
- Gate Result：作为脱敏 research/archive candidate 可归档；作为技术选型、产品可行性或发布结论为 `manual-validation-pending`。
- 下一步最多三项：执行 W0；建立合法测试语料；招募 30–50 名封测用户。
- Memory Candidate：no。本文不自动写入 memory、AGENTS 或 active facts。
- Supersedes：none。
- last_verified：2026-08-01。
