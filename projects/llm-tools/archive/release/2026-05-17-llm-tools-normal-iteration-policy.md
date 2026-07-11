# llm_tools 正常迭代策略历史记录 2026-05-17

## 摘要

本文从旧 Codex archive `memory-curation` 选择性迁移而来，保留 2026-05-17 `llm_tools`、`sigmastar-flasher`、`ota-packager` 从“一次性初始化/单提交整理”转入正常迭代的历史策略。本文是 archive-only 记录，不代表当前仓库状态、当前发布基线或当前远端策略已经重新验证。

## 历史策略

- 三仓进入正常迭代后，默认不再 amend、rebase、squash 或强推来维持单提交历史。
- 后续修改使用普通增量提交，保留可审计历史。
- 只有用户明确要求“覆盖/重写历史/强推”时，才允许考虑改写历史；执行前仍需范围、回滚和远端状态确认。
- 母仓 `llm_tools` 负责治理、跨仓脚本、release 编排和工具注册；子仓 `sigmastar-flasher`、`ota-packager` 保持独立 Git 历史和独立发布边界。
- `tooling/tool.json` 的标准动作应覆盖 `test`、`preflight`、`validate`、`inspect`、`smoke`、`release_check`、`codex_check`、`clean` 等可组合入口。
- wheelhouse 依赖应外置到 release requirements，不把发布依赖硬编码到脚本。
- 生成物清理通过显式 `clean-generated` / `clean_workspace.sh --dry-run` 入口进行，不用会误伤子仓工作区的仓库级隐式清理。
- Windows 发布保持 x64 优先；x86 不作为默认发布目标。
- Authenticode 证书、私有 PyPI 凭据、PFX 密码和 release secret 不进入仓库、Hub 正文或 memory。

## 迁移边界

本记录只迁移历史策略，不提升 active rule，不写 memory，不修改源项目。

| Source | SHA256 | 行数 | 字节 | 处置 |
| --- | --- | ---: | ---: | --- |
| `domains/codex/archive/codex-archive/memory-curation/20260517-154419-llm-tools-targeted-memory-curation.md` | `b8081a23afac1bb76f09df6249f198678651aeef51995248b7c1d50aa95e5420` | 69 | 4383 | extract-first migrated |
| `domains/codex/archive/codex-archive/memory-curation/20260517-155031-llm-tools-memory-curation-normal-iteration.md` | `dded8e2cc0141056bc6fb24ef4b5c5f65da08bbd9a48fa44542e0fb9e5ace370` | 73 | 3053 | extract-first migrated |

## 覆盖关系

- 相关历史治理：`projects/llm-tools/archive/release/2026-05-17-llm-tools-three-repo-governance-session.md`
- 后续 release governance 历史：`projects/llm-tools/archive/release/2026-05-16-llm-tools-release-governance.md`
- 终态删除 coverage：`artifacts/manifests/codex-archive-memory-curation-coverage-20260711.md`

## 风险

- 本记录不证明三仓当前仍保持这些动作、脚本或远端状态。
- 单提交阶段属于历史状态；不得用它覆盖正常迭代策略。
- 若要形成 current runbook，必须基于当前仓库重新运行测试、release check、Windows 构建和签名门禁。
