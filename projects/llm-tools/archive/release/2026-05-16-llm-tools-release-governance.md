# llm_tools 发布治理归档 2026-05-16

## 摘要

本文从旧 Codex archive 迁移而来，保留 2026-05-16 `llm_tools` 发布治理历史结论。它是 archive-only 记录，不代表当前发布基线已经重新验证，也不提升为 active runbook。

## 历史决策

- Windows 默认发布目标只包含 x64：`sigmastar-flasher` EXE、`sigmastar-flasher` 安装包、`ota-packager` GUI EXE。
- x86 构建不进入默认发布基线；如需验证，必须显式开启并单独记录风险。
- Windows 发布默认执行最终 EXE smoke test，不能只信任 PyInstaller 构建完成。
- Linux 与 Windows 发布目录均生成 `release-manifest.json` 与 `SHA256SUMS.txt`。
- 发布说明由 manifest 与产物清单生成。
- 工具清单结构由 tool manifest / registry schema 固定。
- Windows 构建依赖使用持久 pip cache；源码打包排除虚拟环境目录，避免依赖环境混入源码包。

## 历史入口

```bash
./scripts/release_local.sh <version>
./scripts/release_windows_remote.sh <version>
./scripts/release_all.sh <version>
./scripts/windows_builder_doctor.sh
./scripts/generate_release_notes.py <version> --out release-notes/v<version>.md
```

## 历史验证摘要

旧记录声称当时完成了 Codex 标准检查、Git remote 检查、工具注册校验、两个工具测试、Windows 构建机诊断、Windows 远程发布、Linux 跳过 Windows 发布路径和 manifest JSON 解析。

这些证据只作为 2026-05-16 历史发布治理记录。由于本次迁移未重新执行 `llm_tools` 源仓测试和发布脚本，不能把这些结果当作当前通过证据。

## 当前风险

- 当前 `llm_tools` 仓库的脚本、schema、发布说明生成器和 Windows 构建机状态可能已经漂移。
- 历史记录混合了决策、流程、验证证据和环境提示，后续若要写入 `current/runbooks/release-governance.md`，必须重新核验当前源仓。
- 任何 Windows 构建机真实地址、用户名、SSH key、env 文件内容、证书、签名密钥、release binary 或完整 manifest 都不得写入 Hub 正文。

## 迁移边界

- Source：`domains/codex/archive/codex-archive/release-governance/20260516-225144-llm-tools-release-governance-20260516.md`
- Source SHA256：`d67055f56fccc7b2210bd97b9a173f25291bbab872edfb06358a7d6349966a03`
- 迁移方式：archive-only 历史摘要，不复制 raw release logs、binary、manifest 全文、凭据或环境私有值。
- 后续动作：如需当前发布 runbook，基于源仓当前 `docs/release-mechanism.md`、`docs/tool-governance.md` 和 release scripts 重新复核后另建 reviewing 条目。
