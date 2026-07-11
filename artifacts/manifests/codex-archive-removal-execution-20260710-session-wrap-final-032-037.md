# Codex archive session-wrap final 删除执行批次 2026-07-10

## Scope

本批完成剩余 6 个 `session-wrap` 旧正文的 extract-first 后删除。

授权 ID：`auth-20260710-codex-archive-delete-session-wrap-final-032-037`

恢复锚点：`db07bd4839016d76f37218cd2b72857ed8575d48`

## Canonical 目标

- `projects/llm-tools/archive/release/2026-05-17-llm-tools-three-repo-governance-session.md`
- `projects/mcu/archive/2026-05-17-gd32-hc32-codex-maintenance-session.md`
- `artifacts/manifests/codex-archive-knowledge-legacy-coverage-20260710.md`
- `artifacts/manifests/codex-wechat-absorption-final-handoff-coverage-20260710.md`
- `projects/mcu/archive/2026-05-24-gd32l235-app-boot-refactor-session.md`

## 删除清单

| CARE | Old source | SHA256 | 覆盖目标 |
| --- | --- | --- | --- |
| `CARE-20260710-032` | `session-wrap/20260517-154126-llm-tools-session-wrap.md` | `7aec9611beb17018dd2ebfaa2798d78a3d139008acec60782d9c91350f820cd0` | `projects/llm-tools/archive/release/2026-05-17-llm-tools-three-repo-governance-session.md` |
| `CARE-20260710-033` | `session-wrap/20260517-154134-gd32-firmware-session-wrap.md` | `c8c3e8361a0cc3bdf0fbfa72eb6a11b73e441cb773e58872ed20cb683095566b` | `projects/mcu/archive/2026-05-17-gd32-hc32-codex-maintenance-session.md` |
| `CARE-20260710-034` | `session-wrap/20260517-180051-knowledge-session-wrap.md` | `963923625ccdbece2548b4315ab4f9a907e6f6ed908d1afffc504a996626b266` | `artifacts/manifests/codex-archive-knowledge-legacy-coverage-20260710.md` |
| `CARE-20260710-035` | `session-wrap/20260523-135801-wechat-all-cleared-handoff.md` | `01e93739e354812d4d3a9938b6eb1340ed367a94679b97c146e991bb78985888` | `artifacts/manifests/codex-wechat-absorption-final-handoff-coverage-20260710.md` |
| `CARE-20260710-036` | `session-wrap/20260524-141359-gd32l235-app-boot-v1-session-wrap-20260524.md` | `8c78fc6ddd9ed56dc5995565bdc7497e835661c8d116fc64a908feb2417cb5d5` | `projects/mcu/archive/2026-05-24-gd32l235-app-boot-refactor-session.md` |
| `CARE-20260710-037` | `session-wrap/20260524-231336-gd32l235-app-boot-v1-session-wrap.md` | `6b1202c675572b6f5c2da4a0ecb785b7ad34bb11cc6aed5d0e1d1ed2873b2117` | `projects/mcu/archive/2026-05-24-gd32l235-app-boot-refactor-session.md` |

## Boundaries

- 删除范围只限上述 6 个旧正文。
- 不删除 `session-wrap` topic index。
- 不删除旧 archive corpus；memory-curation topic 仍阻塞整库删除。
- 不写 memory，不提升 active，不生成 owner decision。
- 不改源项目，不 commit，不 push。

## Validation Plan

```bash
rtk jq -c . artifacts/manifests/codex-archive-removal-execution-20260710-session-wrap-final-032-037.jsonl
rtk bash -lc "test ! -e domains/codex/archive/codex-archive/session-wrap/20260517-154126-llm-tools-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260517-154134-gd32-firmware-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260517-180051-knowledge-session-wrap.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260523-135801-wechat-all-cleared-handoff.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260524-141359-gd32l235-app-boot-v1-session-wrap-20260524.md && test ! -e domains/codex/archive/codex-archive/session-wrap/20260524-231336-gd32l235-app-boot-v1-session-wrap.md"
rtk bash tools/knowledge-search.sh "llm_tools 三仓治理"
rtk bash tools/knowledge-search.sh "GD32 HC32 Codex 维护"
rtk bash tools/knowledge-search.sh "WeChat 313 zero pending"
rtk bash tools/knowledge-search.sh "GD32L235 app_boot_v1 重构历史"
rtk bash tools/knowledge-check.sh --dry-run
rtk git diff --check
```
