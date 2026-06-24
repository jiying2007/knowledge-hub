---
title: 记忆自动化整理流程
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-21
last_updated: 2026-05-21
tags: [memory, automation, codex, curation]
related: [project-debug-tools-guide.md]
validation_refs: [../../tools/memory/memory-curator-auto.sh, ~/codex/scripts/curate-memory.sh]
---

# 记忆自动化整理流程

## 1. 目标

把记忆整理流程固定为：

1. 自动生成候选（`memory-curator`）
2. 自动审核打标（`keep/rewrite/drop`）
3. 自动产出优化草稿（`final`）

默认不直接写正式 memory，避免误写和跨项目污染。

## 2. 入口命令

一键执行全流程：

```bash
rtk bash tools/memory/memory-curator-auto.sh run --project llm_tools --exclude-keywords "crash-debug,core 排障,BusyBox"
```

仅做自动审核（不重新跑 curate）：

```bash
rtk bash tools/memory/memory-curator-auto.sh review \
  --report ~/codex/docs/archive/memory-curation/<report>.md \
  --candidate ~/.codex/memories/.codex/curation-inbox/<candidate>.md \
  --project llm_tools \
  --exclude-keywords "crash-debug,core 排障,BusyBox"
```

## 3. 输出位置

- 自动审核结果：`~/.codex/memories/.codex/curation-inbox/*-memory-candidate.auto-review.md`
- 自动优化草稿：`~/.codex/memories/.codex/curation-inbox/*-memory-candidate.auto-final.md`

## 4. 自动审核规则

1. `drop`
- AGENTS 重复项
- 标题/结构项（如 `#`、`##`）
- 描述性非规则语句
- 命中跨项目关键词（`--exclude-keywords`）

2. `keep`
- 已满足稳定、短小、可复用的规则句

3. `rewrite`
- 有复用价值但表述偏叙述，自动改写为规则句

## 5. 推荐节奏

1. 每次会话收尾后运行一次 `run`
2. 每周集中复核一次 `auto-final`
3. 通过复核后再手动写入正式 memory

## 6. 风险控制

1. 草稿阶段不自动落库（默认）
2. 跨项目关键词必须维护，防止污染当前项目记忆
3. 规则写入前要求保留 `Evidence` 路径，保证可追溯
