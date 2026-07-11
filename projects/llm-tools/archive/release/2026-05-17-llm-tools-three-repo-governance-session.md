# llm_tools 三仓治理与单提交发布历史 2026-05-17

## 摘要

本文从旧 Codex archive `session-wrap` 选择性迁移而来，保留 `llm_tools`、`sigmastar-flasher`、`ota-packager` 三仓在 2026-05-17 的治理和初始化发布历史。本文是 archive-only 记录，不代表当前发布基线已经重新验证。

## 历史完成事项

- 三仓治理资产完成整理：`AGENTS.md`、skill、tool manifest、脚本、发布文档和运行手册。
- 母仓新增 `scripts/clean_generated.sh`，并在 `scripts/toolctl.py` 暴露 `clean-generated`。
- wheelhouse 发布依赖从脚本内联改为 `requirements/release.txt`，支持 `LLM_TOOLS_RELEASE_REQUIREMENTS` 覆盖。
- 母仓新增 `docs/initial-release-baseline.md` 和 `docs/script-maintenance.md`。
- `sigmastar-flasher` 与 `ota-packager` 补齐 `docs/runbook.md`、`docs/release.md`、`docs/troubleshooting.md`。
- 两个子仓 `tooling/tool.json` 统一标准动作：`test`、`preflight`、`validate`、`inspect`、`smoke`、`release_check`、`codex_check`、`clean`。
- 两个子仓 `scripts/clean_workspace.sh` 支持 `--dry-run` 并拒绝未知参数。
- 三仓当时合并为单一初始化提交，并以 `--force-with-lease` 覆盖推送。

## 历史仓库状态

- `llm_tools`: `0d17885040d33f5c765e3cfc45df123a31611951`
- `sigmastar-flasher`: `2efe549dfa772a882b02da2808e4409488b0a7bd`
- `ota-packager`: `6ac23a8814ad2183e0f94a74ce917d0267cb3322`
- 当时三仓均为 `master...origin/master` 同步状态。
- 当时三仓 `git rev-list --count HEAD` 均为 `1`。

## 历史决策

- 三仓当时保持单一初始化提交，不保留中间优化提交历史。
- 覆盖推送使用 `git push --force-with-lease`，避免无保护地覆盖远端新增提交。
- 母仓负责治理、注册、发布编排和跨仓脚本；两个子仓保持独立 Git 历史。
- 母仓不使用 `git clean -X` 清理 ignored 子仓目录，避免误删子仓工作区。
- Windows 发布继续走 Windows 构建机和 Authenticode 可选/强制门禁；证书、密码、私有 pip 凭据不进入仓库或 Hub 正文。
- 发布基线文档不固定初始化提交短哈希，以实时 `HEAD` 和 commit manifest 为准。

## 历史验证摘要

旧源记录当时通过：

- `rtk ./scripts/toolctl.py doctor`
- `rtk pytest -q`，母仓 `105 passed`
- `rtk ./scripts/toolctl.py run-all test`，子仓分别 `42 passed` 和 `46 passed`
- `rtk ./scripts/toolctl.py run-all preflight`
- `rtk ./scripts/toolctl.py run-all smoke`
- `rtk ./scripts/toolctl.py clean-generated --dry-run`
- `rtk ./scripts/build_wheelhouse.sh --help`
- 三仓 `git diff --check`
- 两个子仓 `release_check`
- 三仓远端哈希与本地一致性复核

这些验证只证明旧会话当时状态。本次迁移未重新执行源仓测试、发布脚本、Windows 构建或远端检查。

## 风险

- `sigmastar-flasher` preflight 当时有 `max_workers > 当前串口数量` 警告，但旧源标记为非阻塞。
- Authenticode 机制已接入，但无证书时只能生成 `NotSigned` 状态；正式发布前仍需 required-mode 验证。
- wheelhouse 已外置依赖清单，但旧源没有完整供应链审计报告。
- 当前源仓可能已经漂移；如需 current runbook，必须重新核验当前仓库。

## 迁移边界

- Source: `domains/codex/archive/codex-archive/session-wrap/20260517-154126-llm-tools-session-wrap.md`
- Source SHA256: `7aec9611beb17018dd2ebfaa2798d78a3d139008acec60782d9c91350f820cd0`
- Source size: `4671` bytes
- Preflight row: `CAEF-20260710-024`
- Tombstone: `CARE-20260710-032`
- 决策：旧正文可在本记录、registry、index、tombstone 和授权账本落地后删除；不提升 active、不写 memory、不改源项目。
