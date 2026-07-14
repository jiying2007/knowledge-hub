---
id: llm-agent-adk-v3-1-rc2-release-closure-20260714
title: LLM Agent 与 ADK 3.1 RC2 发布候选闭环验证
kind: validation
domain: projects/llm-agent
scope: project-specific
visibility: team-internal
status: archived
owner: leiwenjun
review_after: '2026-10-14'
review_status: human-reviewed-retired
promotion: none
tags:
- llm-agent
- agent-dev-kit
- release-candidate
- validation
- no-active-promotion
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-14'
manual_validation_pending: false
summary_zh: 记录 ADK 3.1.0-rc.2 与根仓提交推送、可复现制品、回滚演练、根仓门禁及零复制零覆盖零删除的声明式 live apply；总体仍为 M3，真实 direct-target runtime、远端发布和现场 M5
  证据继续阻塞。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
promotion_decision: 用户于 2026-07-14 明确授权将本轮 ADK 3.1 RC2 闭环验证归档；保留正文与 provenance，不提升 active、不写 memory、不远端发布。
path: projects/llm-agent/validation/adk-v3-1-rc2-release-closure-20260714.md
aliases:
- llm-agent adk 3.1 rc2 release closure
- llm-agent-adk-v3-1-rc2-release-closure
related:
- projects/llm-agent/README.md
- projects/llm-agent/current/project-profile.md
- projects/llm-agent/validation/project-readiness.md
- projects/agent-dev-kit/README.md
---

# ADK 3.1.0-rc.2 实现交接

## 结论

`agent-dev-kit 3.1.0-rc.2` 已提交并推送，覆盖审计中最高优先级的 direct-target conformance，并补齐 JSON Schema 执行、clean-clone CI、静态/依赖/Scorecard 门禁、SBOM/provenance、端到端性能曲线和 OOD trace/outcome eval 控制面。

总体评级保持 **M3 release candidate**。三个 direct target 保持 `experimental`；本报告不声明真实 Claude Code、OpenCode、Hermes runtime 已认证。根仓 gitlink、`adk.lock`、Software M5 policy 和 current status 已同步到 rc.2，产品基线已提交推送，并完成声明式 live apply。

## 已实现

- Versioned `TargetContract`/shared adapter：Claude Code 与 OpenCode 使用 `agents/<name>.md`、`skills/<name>/SKILL.md`；Hermes 仅支持 Skill，Agent fail closed。
- Skill frontmatter 含 `name`、`description`；Agent 显式 permission profile；support tree 保持，symlink 拒绝。
- export/install 共用 renderer，plan v2、receipt v3、逐文件 source/rendered hash、atomic apply/rollback 与 legacy receipt 回滚。
- Draft 2020-12 manifest schema 由 `jsonschema` 实际执行；未知字段负例进入测试。
- root clean-clone workflow 只初始化 HTTPS `agent-dev-kit` 锁定 gitlink，不拉取全部参考仓。
- ADK CI 增加 ShellCheck、Ruff、pip-audit、target static；release 增加 SPDX SBOM 结构校验和 SHA-pinned provenance attestation；OpenSSF Scorecard 独立 report workflow。
- 性能覆盖 manifest/profile、target contract、CLI cold-start、10x plan、10x I/O 与 peak allocation。
- 24 例 OOD/adversarial 输入与标签分离，评分 route/safety/trace/outcome，并执行 `routing.intents` 消融。
- OpenAI 与 Anthropic 共用结构化 freshness gate：当前 69 条 source records，provider 域名归属、最低覆盖、必需 source ID 与 90 天窗口均受门禁约束。

## 当前锁与提交边界

- ADK commit `dd67b488c13e96933d80336f05160b9eea94e4fe` 已推送到 `origin/main`。
- 根仓 gitlink 与 `adk.lock` 已同步到 `3.1.0-rc.2 / dd67b488...`；产品基线 commit `4cae24857c4c378798b85a8cd096e1d513da7b10` 已推送到 `origin/main`。
- 已按授权完成 `~/codex -> ~/.codex` 声明式 apply：`copy=0`、`overwrite=0`、`delete=0`、`keep=481`、`mkdir=270`；仍不创建 tag、GitHub Release 或远端制品。

## 外部阻塞

1. 三个 direct target 的真实 runtime discovery/load/trigger/permission smoke。
2. GitHub-hosted CI、Scorecard 和 artifact attestation 的远端运行证据。
3. Codex/Claude 60-task × 2 condition × 3 trial campaign。
4. 独立仓库、第二操作者、30 天 field ledger 和完整事件链。
5. blocker 清零后的 final `3.1.0`。

## 验证状态

- ADK strict：PASS。
- ADK full regression：51/51 PASS。
- direct target static：3/3 PASS；真实 discovery smoke 均为 `not-run/not-certified`、exit 2。
- effect eval：24/24，route/safety/trace/outcome 均 100%，routing ablation delta 0.3333。
- performance：manifest/profile/export/target/cold-start/10x plan/10x I/O/peak-memory 全部预算 PASS。
- Ruff 0.15.21、ShellCheck、内建 security、兼容本机 Python 3.8 的 pip-audit 2.7.3、release check：PASS；CI 固定 Python 3.12 + pip-audit 2.10.1，等待远端运行。
- 可复现 rc.2 source artifact：两次独立构建及演练后的第三次重建 SHA256 均为 `8571134df515289d32905961ae78d5e5c2dd308d2771691690594a85c76142ac`，521 source files；checksum 独立核验 PASS。
- rc.1 → rc.2 演练：legacy 52 文件回滚、rc.2 39 文件安装与回滚均 PASS；随后从保留的 rc.1 artifact 重装并核对 52 个 managed hashes，最终清理 52 个文件；evidence 写入后 artifact SHA 不变。
- 根仓 quick：56/56 PASS；lock/current-status/software-M5/subrepo-state 的 rc.1 边界失败已在真实 ADK commit 后闭环。
- 根仓 full：62/62 PASS；harden readiness、性能、证据包、Token、WeChat 和 workspace entrypoints 全部通过。
- source-to-live：build 749 managed，doctor 0 error/0 warning，plan/dry-run/apply 均 PASS 且零复制/覆盖/删除；`~/codex` 66 tests、四 profile smoke、routing precedence 和 live compare 全部 PASS。
- 应用后 runtime health：PASS，live `team-collab` profile 0 error/0 warning。

完整本地证据见 `agent-dev-kit/docs/changes/adk-v3-1-rc2-target-conformance/verify-report.md`；机器可读演练见同目录 `release-rehearsal.json`。根仓机器可读 release evidence 见 `reports/adk-v3-1-rc2-release-evidence-2026-07-14.json`。

## Related

- [LLM Agent 项目入口](../README.md)
- [LLM Agent readiness validation](project-readiness.md)
- [Agent Dev Kit 项目入口](../../agent-dev-kit/README.md)
