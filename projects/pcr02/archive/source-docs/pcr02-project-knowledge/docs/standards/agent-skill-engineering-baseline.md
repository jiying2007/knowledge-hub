---
title: AGENT 与 SKILL 工程基线
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-12
tags: [agent, skill, engineering]
related: []
validation_refs: []
---

# AGENT 与 SKILL 工程基线

## 1. 目的

本基线用于统一团队在各子仓库维护 `AGENTS.md` 与 `SKILL.md` 的方式，避免规则重复、内容漂移和阶段性文案回流。

原则：AGENT/SKILL 只承载“摘要约束 + 执行入口”，详细规范归档在专用文档，机检规则归档在脚本。

## 2. 分层承载模型

### 2.1 AGENTS.md（硬约束层）

必须包含并保持固定章节顺序：

1. 基本信息
2. 职责范围
3. 依赖边界
4. 禁止事项
5. 规范要求
6. 最小验证
7. 推荐技能

职责：

- 明确子仓库边界、禁止项与最小验收命令。
- 提供可执行入口，不重复大段细则。

### 2.2 SKILL.md（执行流程层）

必须包含并保持固定章节顺序：

1. 触发条件
2. 处理范围
3. 强制检查
4. 最小验证
5. 输出要求

职责：

- 规定“何时触发、如何执行、如何验收、输出什么”。
- 面向执行过程，不替代设计文档或编码规范全文。

### 2.3 专项规范文档（细则层）

职责：

- 承载长期稳定、篇幅较长、需要演进记录的细则。

当前强制引用：

- 代码规范：`docs/standards/c-coding-standards.md`
- 本基线：`docs/standards/agent-skill-engineering-baseline.md`

### 2.4 机检脚本（门禁层）

职责：

- 将可自动校验的规范固化为脚本，减少人工审查负担。

当前建议：

- `docs/governance/check_agent_skill_consistency.py`：检查 AGENT/SKILL 模板一致性与关键字段完整性。
- `scripts/new-skill.sh`：按统一结构生成 `SKILL.md`、`README.md`、`LICENSE` 与 `agents/openai.yaml`。

### 2.5 内容归属判定规则（新增）

目的：避免把阶段性架构版本内容（如 V3/V4）写入长期规则文件，导致后续维护成本上升。

判定顺序（按优先级）：

1. 是否“长期稳定且跨版本复用”？
- 是：写入 `AGENTS.md`（边界、目录、命名、编译与验收门禁）。
- 否：进入下一条判断。

2. 是否“可重复执行的流程动作”？
- 是：写入 `SKILL.md`（触发条件、步骤、强制检查、验证与输出）。
- 否：进入下一条判断。

3. 是否“仅某一版本/阶段有效”？
- 是：留在业务项目仓库的设计、计划、报告目录，或进入 `docs/archive/*` 作为历史索引；不写入团队知识库 AGENT/SKILL 主体。

强制规则：

- `AGENT/SKILL` 禁止出现版本绑定叙事（如“V4终版策略”“V5迁移临时方案”）作为长期约束。
- 版本文档可引用 AGENT/SKILL，但 AGENT/SKILL 不回填阶段性实现细节。
- 若某版本实践被证明可长期复用，需先抽象为“版本无关规则”，再纳入 AGENT/SKILL。

## 3. 架构边界约束（通用）

- `cli`：仅命令发现与 canonical payload 组装，不执行业务。
- `cmd_server`：仅网关/注册/路由，不执行业务，不初始化业务资源。
- `daemon`：仅进程编排与守护，不承载诊断业务执行。
- `modules/hdi`：底层能力封装，不依赖 `modules/api`/`modules/app`。
- `modules/api`：中间封装层，不依赖 `modules/app`。
- `modules/app`：应用运行时收口层，负责上层诊断运行时闭环。

## 4. 目录结构约束（通用）

- 对外头文件与实现目录边界必须清晰：
  - `include/`：对外接口
  - `src/`：内部实现
- 对外发布双目录需同步：
  - `modules/app/include` 与 `include/app`
- 子仓库规则文件固定位置：
  - `<repo>/AGENTS.md`
  - `<repo>/.codex/skills/<skill-name>/SKILL.md`

## 5. 编译与验证约束（通用）

- 所有命令必须通过 `rtk` 前缀执行。
- AGENT 与 SKILL 的“最小验证”必须包含三段：
  - `构建`
  - `边界扫描`
  - `规范检查`
- 无验证证据时不得声明“已完成”。

## 6. 变更维护规则

- 任何 AGENT/SKILL 模板变更，必须同步更新本基线。
- 新增子仓库时，必须按本基线创建 AGENT/SKILL，不得自由发挥章节结构。
- 新增 skill 时，优先使用 `scripts/new-skill.sh`，不得只提交单个 `SKILL.md`。
- 提交前执行一致性机检，确保模板不漂移。
