# 外部资料吸收规范

## 目标

外部文章、项目、官方文档、研究笔记和参考仓库只能经过来源登记、证据判断和 owner review 后进入长期资产。吸收的目标是形成可复用结论，不是搬运原文。

## 来源元数据

外部资料候选至少记录：

- `source_id`
- `title`
- `publisher_or_author`
- `published_at`
- `retrieved_at`
- `url_or_path`
- `source_language`
- `source_license`
- `read_status`
- `review_status`
- `evidence_strength`
- `promotion_decision`

`promotion_decision` 建议值：

- `adopt`：可直接采用结论。
- `adapt`：需要结合本仓边界改写。
- `reject`：不采用。
- `archive-only`：只作历史或参考归档。

## 吸收流程

1. 先搜索现有 AGENTS、registry、domains 和 governance，确认没有同等规则。
2. 登记来源、读取日期、适用范围和许可证状态。
3. 写中文摘要、关键证据和不采用内容。
4. 标注 adopt、adapt、reject 或 archive-only。
5. 需要提升为团队规范时，走 owner review 和 secret scan。
6. 保留 source URL 或路径，但不复制整篇外部正文。

## 禁止事项

- 不整段搬运外部文章或项目文档到 skill、AGENTS 或 governance。
- 不把单篇文章观点直接提升为全局规则。
- 不把未确认来源、owner、状态和 review 周期的条目标为 active。
- 不写入凭证、私有 URL、cookie、内部端点或个人隐私。
- 不为同一概念创建平行规则，优先更新现有规范或登记 archive-only。
- 不把外部 binary、SDK、日志、core、release 包放入文本知识层。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-18`
- validation_refs：`tools/knowledge-check.sh --dry-run`
