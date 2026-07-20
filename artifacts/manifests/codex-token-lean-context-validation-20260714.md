---
id: codex-token-lean-context-validation-20260714
title: Codex token-lean 固定上下文优化验证候选
kind: validation
domain: codex
path: artifacts/manifests/codex-token-lean-context-validation-20260714.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: generated
  from: current Codex token-context optimization session against ~/codex and Knowledge Hub validation outputs
  source_sha256: 0cb281e9ff1b11b289d4931f0ca7cadedc7b29b4fe286cf2a2d36906d1666a3f
review_after: '2026-10-14'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- codex
- token-lean
- token-governance
- knowledge-hub
- validation-candidate
- no-active-promotion
validation_refs:
- artifacts/manifests/codex-token-lean-context-validation-20260714.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- artifacts/manifests/codex-token-lean-context-validation-20260714.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-14'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-14'
manual_validation_pending: true
summary_zh: 记录 Codex 默认固定上下文与 Knowledge Hub 预检的 Token 治理优化：Codex 固定文本字节估算下降 62.3%，默认保留 20 个核心 skill 并通过受治理检索加载长尾能力；该条目仅为 reviewing
  验证候选。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# Codex token-lean 固定上下文优化验证候选

## 结论

本次优化把 Codex 默认固定上下文从“完整技能目录常驻”改为“20 个核心技能常驻 + 全量可信目录按需检索”，并把 Knowledge Hub 预检切到 `small + summary-json`。按 UTF-8 字节数代理估算，Codex 固定上下文由 35,434 B 降至 13,349 B，下降 62.3%。该数值用于相对比较，不等同于供应商账单 token。

## 范围与来源

- captured_at: 2026-07-14
- validated_at: 2026-07-15
- source: `~/codex` 当前 source、build、live 资产及本次验证输出
- Knowledge Hub source: `~/knowledge-hub/tools/knowledge-context.sh` 当前只读预检输出
- scope: 默认 profile、全局 AGENTS、skill catalog、按需 skill 检索、source-to-live 门禁
- non-goals: 不删除长尾 skill，不改变外部权限，不由优化流程自行 commit/push，不写入长期 memory；后续 commit/push 只接受用户单独明确授权

## 前后指标

| 指标 | 优化前 | 优化后 | 变化 |
| --- | ---: | ---: | ---: |
| 全局 AGENTS | 16,604 B | 8,501 B | -48.8% |
| 默认 skill catalog | 18,830 B / 60 项 | 4,848 B / 20 项 | -74.3% |
| Codex 固定上下文估算合计 | 35,434 B | 13,349 B | -62.3% |
| Knowledge Hub 常规预检样本 | 27,368 B | 2,923 B | -89.3% |
| Knowledge Hub quick regression 代表查询 | 不适用 | 3,938–3,940 B | 本轮观测区间含 stdout 换行，小于 4,096 B 预算 |

## 落地设计

1. 默认 profile 改为 `token-lean`，只常驻 20 个核心技能；`team-collab` 保留完整兼容能力，作为显式切换项。
2. 新增 `scripts/skill-search.sh`，从受治理的完整 manifest 检索并只加载命中的 `SKILL.md`；默认排除 Superpowers fallback，只有显式 `--include-fallback` 才返回。
3. 在 `manifests/profiles.json` 固化 AGENTS、默认 active skill 数、catalog 字节和检索输出预算，并在治理校验中阻断超限漂移。
4. Knowledge Hub 默认预检示例使用 `--context-budget small --limit 3 --summary-json`，保留原文回退入口。
5. 保留 `team-collab` 和完整 manifest，不以删除能力换取省 Token。

## Evidence Index

| 命令/证据 | 结果 | 说明 |
| --- | --- | --- |
| Codex commit `a27c0229fad59abd6f54d8a5bff278fee2887c1c` 的隔离 `scripts/check.sh` | exit 0 | 73 个 Python tests 通过；minimal、solo-dev、token-lean、team-collab、superpowers-compat profile smoke 全通过 |
| 隔离 profile doctor / diff / drift | exit 0 | 最终 profile 检查 0 errors、0 warnings，diff/drift 均为 0 |
| 隔离 `scripts/check-skills.sh` | exit 0 | skills=60，errors=0，warnings=0 |
| `rtk bash ~/codex/scripts/check-routing-precedence.sh` | exit 0 | 默认 profile 为 token-lean；默认 active Superpowers=0 |
| 选择性暂存快照的隔离 HOME build/plan/apply/check | exit 0 | 不读取真实 `~/.codex`，应用后完成五个 profile 的 source-to-live smoke 与一致性检查 |
| `skill-search` 定向测试 | exit 0 | 资产治理命中 `skill-asset-manager`；无 fallback 时 `writing plans` 为 zero-hit；显式 fallback 后可命中 |
| Knowledge Hub 定向 pytest | exit 0 | `test_context.py`、`test_metrics.py`、`test_search.py` 全部通过 |
| Knowledge Hub `knowledge-check` | exit 0 | 选择性快照 0 errors、0 warnings |
| Knowledge Hub quick regression | exit 0 | 26/26 通过；代表性 small summary 本轮为 3,938–3,940 B（含换行），小于 4,096 B 预算 |
| `rtk git diff --check` | exit 0 | 无空白错误 |

## 负向路径与修复

1. Knowledge Hub 复杂摘要初版为 4,325 B，超过 4 KiB 目标；压缩重复字段后降至 3,922 B，当前 clean clone 代表查询因动态 `latency_ms` 在 3,938–3,940 B（含换行）间变化。
2. 新增资产治理 route 时，governance 检查发现 fallback skill 未列入 workflow closure；补齐 `adk-skill-composition-governance` 后检查通过。
3. 两次大范围补丁与并发工作区变化冲突；改为小粒度补丁并重新跑完整门禁，没有覆盖或回退其他未提交改动。
4. 首次在 linked worktree 运行 Knowledge Hub quick regression 时，3 个自路由用例因 worktree 私有 gitdir 不含 remote config 而失败；主仓对照与带独立 `.git`、受控 `local/workspaces.json` 的 clean clone 均能识别同一 remote/workspace，clean clone 最终 26/26 通过，证伪了 token 改动破坏路由的假设。

## 兼容性、回滚与剩余风险

- 行为变化：默认不再把 60 项完整技能描述注入固定上下文；长尾能力通过按需搜索加载。
- 兼容路径：需要完整目录时显式使用 `team-collab`；需要 Superpowers 时显式使用 `superpowers-compat` 或 `--include-fallback`。
- 回滚路径：将默认 profile 切回 `team-collab`，再执行 `build -> doctor -> plan -> dry-run -> apply -> check` 的 source-to-live 链路。
- 权限边界：未扩大 transport、凭证、外部写入或发布权限。
- 剩余风险：字节数只是 token 的稳定代理；真实计费受 tokenizer 和运行时额外提示影响。长尾 skill 的召回质量需要结合后续 zero-hit/误召回样本继续监控。
- 工作区边界：`~/codex` 与 Knowledge Hub 均存在其他会话的并存未提交改动；本候选只覆盖选择性暂存快照，不把这些改动归因于本次优化。可提交/推送结论另由完成门禁和用户明确授权决定。

## 候选状态

本记录仅作为 `reviewing` 验证候选，`promotion=none`。不代表 owner 签收、active 提升、发布完成或长期 memory 写入。
