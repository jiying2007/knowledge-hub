---
title: 知识库发布与版本规范
doc_type: standard
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-17
last_updated: 2026-05-17
tags: [release, versioning, governance]
related: [knowledge-contribution-guide.md]
validation_refs: [CHANGELOG.md]
---

# 知识库发布与版本规范

## 1. 目标

让团队可以明确识别某个项目引用的是哪一版知识库内容。

## 2. Tag 格式

正式发布 tag 使用：

```text
knowledge-vYYYY.MM.DD
```

同一天多次发布时追加序号：

```text
knowledge-vYYYY.MM.DD.N
```

## 3. 发布前检查

```bash
rtk bash scripts/check-all.sh
git status --short
```

要求：

1. `scripts/check-all.sh` 通过。
2. 工作区干净。
3. `CHANGELOG.md` 已记录面向团队的变化。

## 4. 项目引用建议

业务项目只记录知识库远程与 tag，不复制通用内容到项目仓。

## 5. 自动化脚本

```bash
rtk bash scripts/release.sh --date 2026-05-17
```

同一天多次发布：

```bash
rtk bash scripts/release.sh --date 2026-05-17 --suffix 2
```

需要同时推送 tag 时追加 `--push`。
