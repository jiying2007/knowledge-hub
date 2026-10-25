# Embedded Domain

本目录是 Knowledge Hub 的嵌入式候选与 provenance 域，保存跨项目知识的提炼稿、复核证据和历史 Hub canonical 内容。团队已发布规范、runbook、公共工具与 Codex skill 的消费权威位于 `workspace://embedded-knowledge`。

## 首次使用

团队成员使用团队发布仓入口：

```text
workspace://embedded-knowledge
```

团队仓验证（必须在 `workspace://embedded-knowledge` 对应的实际团队仓 checkout 根目录执行；不得直接在 Knowledge Hub 镜像中执行或把命令存在当成测试成功）：

```bash
rtk bash scripts/check-all.sh
```

本目录 `skills/` 中引用的 `scripts/check-all.sh`、`docs/templates/` 或 `docs/AGENTS.md` 也遵循相同的团队仓 cwd/版本边界；没有真实团队仓 commit、执行退出码和产物，不得在 Hub 标记团队技能已发布或测试通过。

Hub 侧常用入口：

- 团队化候选：`standards/`、`runbooks/`
- 平台和架构知识：`platform/`、`architecture/`
- 技能和工具说明：`skills/`、`tools/`
- 模板和治理规则：`templates/`、`governance/`

## 目录

- `standards/`：团队级规范和跨项目规则。
- `runbooks/`：排障、验证、发布和工具使用流程。
- `architecture/`、`platform/`：平台能力、系统架构和设计知识。
- `skills/`、`tools/`：可复用技能和工具说明。
- `templates/`、`governance/`：模板、命名、证据和治理规则。

这些目录中的 `reviewing`、draft、旧 active body 或历史 mirror 不自动等于团队已发布事实。提升时必须记录 source SHA256、目标路径、成熟度、Owner、验证状态和回滚，并通过目标仓 `docs/governance/promotion-contract.md`。

## 旧归档规范的适用性警示（2026-10-25）

本仓 `standards/`、`architecture/` 与 `governance/` 下部分文件是退役团队知识仓的原文镜像。即使旧 Frontmatter 写 `maturity: verified`，只要状态仍为 `status: archived`、`searchable: false`，就只能用于历史回溯；正文中“当前生效”“强制规范”及 `docs/`、`scripts/` 等执行路径均**不得**据此获得当前 Hub 或团队发布权限。

- [历史C代码规范](standards/c-coding-standards.md) 中的 `__API_LIST_H__`、`_List_t`、`_LIST_IsEmpty` 是 C/C++ 实现保留标识符示例，不能直接复制到新代码、头文件或生成模板；当前C规范需在实际团队发布仓与目标工具链上重新确认。
- [历史发布版本说明](standards/release-versioning-guide.md) 的 `scripts/release.sh` / `--push` 与 [旧Docs索引](governance/docs-index.md) 的“当前生效”仅属于旧团队仓语境；绝不在 Hub 镜像执行或据此发布。
- [历史平台能力矩阵](architecture/sigmastar-platform-capability-matrix.md) 的“完整／强／中”仅为当时资料组织/定性判断，不是最新SDK、板卡功能、性能或量产选型证明。
- [历史线程排障文档](standards/thread-troubleshooting-optimization.md) 里的 `<PID>` 等标记仅是需由授权操作人员替换的参数占位；排障命令、VSHDIOS设计与2026年阶段记录不视为当前平台已验收。

本节只补充检索导航和执行作用域：不修改旧正文、历史日期或原哈希，不自动迁移到团队仓、不更新 Owner/Active/`review_after`，也不授权设备、发布、源仓写入或外部证据操作。逐篇审查意见记录在 Issue #176，仍需实际团队仓提交、许可、负向测试和必要的Owner验证。


## 历史高风险操作的执行阻断（2026-10-25）

以下链接仅为已归档、不可检索的原始Runbook，不是可直接复制执行的当前步骤；参见 [2026-10-25全库AI审读记录](https://github.com/jiying2007/knowledge-hub/issues/176)。已归档状态和旧示例里的“推荐”不授予当前设备、权限、测试或发布授权。

- [Core采集指南](runbooks/core-dump-capture-guide.md) 所示系统级 `suid_dumpable`、`core_pattern` 更改及 `chmod 1777` 公共可写core目录，可能改变全机崩溃材料收集权限。未经真实管理员批准、专用隔离目录和敏感数据控制，不得执行或作为生产默认设置。
- [崩溃材料打包指南](runbooks/crash-bundle-collection-guide.md) 的原始core、调试符号和内核日志必须按机密制品单独受控留存；不可上传公开Issue、公开仓库或Hub文本知识层，只可登记经许可的摘要、SHA-256及受控引用。
- [SPI NAND压测](runbooks/spi-nand-busybox-io-stress-guide.md) 中的 `--extra-cmd` OTA升级、`pkill -f`、`rm -rf` 与 `--dmesg-mode clear` 会触发升级、误杀、删除或清除内核日志风险；只能在已授权的隔离测试环境先验证目标，不能面向现场/量产直接运行。断电/冷启动后 `/tmp` 内容可能丢失，必须在断电前把取证结果保留到受控、非易失存储。
- [历史GDB调试指南](runbooks/gdb-debug-guide.md) 的 `gdbserver :2345` 网络监听、root SSH删除或软链接替换业务程序、修改全局 `core_pattern` 与临时glibc调试库，必须先取得授权、隔离端口和明确回滚/BuildID校验；不得把历史设备地址或旧工具链路径作为当前可连接端点，不能在生产设备照搬。
- [历史服务器Hook指南](runbooks/server-hook-setup-guide.md) 针对自托管bare Git服务器，不适用于GitHub受保护 `master` 的权限设置；不可用普通push或自行安装hook绕过真实GitHub Security/Quality审批。

这些限制是对历史执行误用的提示，**不修改任何历史正文、原始命令、owner、Active、review_after或真实运行环境**；真正整改须另有目标设备、源项目及安全/Owner审查证据。没有真实执行/制品证明时，保持 `needs-evidence`，不得声称问题已修复。

## Hub 候选门禁

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
```

如果需要恢复历史来源、迁移证据或 owner 边界，优先查看 `registry/retired-sources.jsonl`、`registry/source-tombstones.jsonl`、`indexes/by-source.md` 和团队仓迁移映射。

## 发布边界

- Hub 不直接写团队仓 remote，不自动 commit/push/merge/tag。
- 团队仓不接收 Hub registry、authorization、raw evidence、个人笔记或项目 lifecycle 正文。
- 发布正文在团队仓通过 `scripts/check-all.sh` 后，Hub 回写 validation/provenance；没有目标 commit 时只能声明本地待提交状态。
- X5 实机、外部下载入口等未验证项继续保留明确 draft/pending 边界，不因文件进入团队仓自动升级成熟度。
