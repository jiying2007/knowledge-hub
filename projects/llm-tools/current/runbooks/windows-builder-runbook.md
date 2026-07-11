# llm_tools Windows 构建机 Runbook

## 摘要

本文从旧 Codex archive 迁移而来，记录 `llm_tools` Windows x64 发布链路的构建机维护边界。当前状态为 `reviewing`：它是可复用 runbook 候选，但尚未基于当前 `llm_tools` 源仓重新执行完整发布验证，因此不声明 active 或已复核的当前事实。

## 适用边界

- Linux 控制端负责治理门禁、源码打包、产物下载和 SHA256 校验。
- Windows 构建机负责生成 Windows x64 EXE 和安装包。
- 默认发布目标以 x64 为主；x86 只能作为显式实验验证任务，并单独记录风险。
- 本文不保存 Windows 构建机真实 hostname、IP、用户名、SSH key、env 文件内容、证书、签名密钥或私有路径。

## 构建机要求

1. Windows 10/11 或 Windows Server。
2. OpenSSH Server 可用，Linux 控制端能按项目授权接入。
3. PowerShell 5.1+。
4. Python launcher `py.exe`。
5. Python 3.10 x64。
6. Inno Setup 6。

## 发布入口

```bash
./scripts/windows_builder_doctor.sh
./scripts/release_windows_remote.sh X.Y.Z
./scripts/release_all.sh X.Y.Z
```

## 远程发布约束

- `scripts/release_windows_remote.env` 是本机私有配置，必须保持 ignored。
- 非默认 SSH key 通过 `WIN_IDENTITY_FILE` 指定；本文不记录真实值。
- Windows 工作目录末级必须是 `llm-tool-build`，避免清理脚本误删高层目录。
- Linux 下载 Windows 生成的 `SHA256SUMS.txt` 后必须先处理 CRLF，再执行 `sha256sum -c`。
- 远程发布脚本不得依赖交互式密码、GUI 操作或未记录的构建机状态。

## 排障结论

- SSH 端口通但 `Permission denied`：优先检查 Windows 实际用户名、管理员组授权文件、授权文件是否为空和 ACL。
- `py -3.10-32` 缺失：只影响实验性 x86，不影响默认 x64 发布。
- PowerShell/SSH 调 `.bat` 时参数含空格容易被重解析：远程 runner 应使用环境变量或 PowerShell 直接调用构建器，避免手拼 `cmd.exe /c`。
- PySide6/PyInstaller 32-bit 发布链不稳定：x86 不进入默认发布目标。
- Inno Setup `.iss` 预处理语法必须与 Inno Setup 6 实测兼容，不使用未验证函数。

## 迁移边界

- Source：`domains/codex/archive/codex-archive/debug-notes/20260516-222503-windows-builder-runbook.md`
- Source SHA256：`9834e36cff48c76b3022f2957c612a140b0f11e19a84281d023139d455a26109`
- 迁移方式：脱敏摘要迁移，不复制机器身份、凭据、env 实值、raw log 或二进制制品。
- 当前限制：迁移时未重新打开 `llm_tools` 源仓验证脚本现状；提升为 active 前必须重新执行当前仓库发布链路或 owner review。
