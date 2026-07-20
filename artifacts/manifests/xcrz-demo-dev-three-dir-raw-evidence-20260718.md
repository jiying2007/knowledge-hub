---
id: xcrz-demo-dev-three-dir-raw-evidence-20260718
title: xcrz_sigmastar_demo_dev 三目录吸收冻结原始证据
kind: validation
domain: projects/xcrz-sigmastar-demo
path: artifacts/manifests/xcrz-demo-dev-three-dir-raw-evidence-20260718.md
scope: project-specific
visibility: team-internal
status: archived
searchable: false
owner: leiwenjun
source: null
review_after: '2026-10-18'
created_at: '2026-07-18'
updated_at: '2026-07-18'
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- source-absorption
- deletion
- provenance
related:
- projects/pcr02-ssc305/validation/2026-07-18-embedded-knowledge-absorption-validation.md
- sources/pcr02-project-docs/coverage.md
- sources/pcr02-project-knowledge/coverage.md
- sources/pcr02-project-scratch/coverage.md
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-18
- rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --strict --json
- rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json
artifact_refs:
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- /tmp/xcrz-demo-dev-docs-knowledge-scratch-20260718.tar.gz
target_version: ba398e5a
test_environment: Knowledge Hub host; source read-only audit plus exact-path deletion
summary_zh: 逐文件审计并吸收 xcrz_sigmastar_demo_dev 的 docs、knowledge、scratch，保留未覆盖项目文档、嵌套知识仓精确远端引用与 scratch 可复用结论；完成门禁和回滚备份后删除三个精确目录。
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: None
evidence_strength: null
evidence_refs:
- current-session exact user instruction: 完全吸收之后，删除三个目录
- backup sha256: 50c5d651142313dfc659766490867e98a235a1ad9cb71deeea2d4d058372b02c
- embedded/knowledge origin/main: cadbf4d6777319c8d43b15f842cbea002cd94cef
generated_by_ai: true
ai_role: extracted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
manual_validation_reason: 媒体休眠板测、50 轮压力、功耗和 Sensor 构建漂移尚未闭环；本条目不把历史计划或源 frontmatter 的 active 字样提升为当前事实。
aliases:
- xcrz_sigmastar_demo_dev 三目录完全吸收与删除验证
---

# xcrz_sigmastar_demo_dev 三目录完全吸收与删除验证

## 结论

本条目把待删除三目录中的 243 个非 Git 内容文件逐一纳入处置清单，并对没有其他可靠正文来源的 17 个项目文档保留完整文本。其余内容按 Knowledge Hub 的正文唯一性规则处理：已有 canonical 的不重复复制，嵌套 Git 仓以在线核验的精确 commit 保留，缓存和 Git 元数据明确排除，scratch 只做 extract-first。

这是一项 source 收口和删除证据，不是功能完成证明。特别是 media pipeline suspend 仍处于“实现已落地、验证受阻”状态，不能据此声称板端、功耗或 50 轮压力通过。

## 归档元数据

- Source：当前会话用户明确要求对 `workspace://xcrz-sigmastar-demo-dev/{docs,knowledge,scratch}` 完全吸收后删除；源身份和删除结果由逐文件 manifest、授权账本及恢复演练共同绑定。
- Topic：`source-absorption` / `project-docs-closeout` / `xcrz-sigmastar-demo-dev`。
- Archive Candidate Path：`projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md`（本条目，唯一长期正文）。
- Captured At：`2026-07-18`；Last Verified：`2026-07-18`。
- Sanitization：真实用户绝对路径改为 `workspace://xcrz-sigmastar-demo-dev`；不归档 secrets、raw session、完整脏工作树、core、日志、binary、cache 或 Git object 正文。
- Provenance：`artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`、`auth-20260718-xcrz-demo-dev-docs-knowledge-scratch-absorb-delete`、`embedded/knowledge@cadbf4d6777319c8d43b15f842cbea002cd94cef`。
- Verification：243/243 源文件删除前 hash 一致；删除后目标不存在；tar 隔离恢复 243/243 hash 一致；Knowledge Hub 主门禁通过。
- Memory Candidate：`no`；本轮不写 `~/.codex/memories`，历史事实继续以 Hub 条目和 manifest 为准。
- Gate Result：`pass-with-declared-unrelated-baseline`；本条目及相关 SSC305 条目无 property/link/MOC 错误，全局 link audit 仅保留任务前已存在的 QIVW `summary_zh` 镜像漂移，且 `blocking_broken_count=0`。
- Lifecycle Boundary：保持 `reviewing / promotion=none`；归档候选落盘不代表 owner approval、active promotion、功能验证完成或正式发布。

## 范围与身份

| 项目 | 证据 |
| --- | --- |
| 源根 | `workspace://xcrz-sigmastar-demo-dev`；绑定当前会话用户提供的绝对路径，长期正文按用户路径规则脱敏 |
| 外层 Git | branch `dev/camera_suspend_resume`，HEAD `ba398e5a`；三个目录在外层工作树中不属于可依赖的已提交正文 |
| `docs` | 44 个文件；27 个已有 Hub hash/provenance，17 个在本文附录保留完整文本 |
| `knowledge` | 191 个非 `.git` 文件；178 个非缓存文件由 `embedded/knowledge@cadbf4d` 精确保留，13 个 `.pyc` 排除 |
| `scratch` | 8 个 Markdown；逐文件 hash 已有 provenance，本次补充可复用结论与排除理由 |
| 合计 | 243 个非 Git 内容文件；0 个符号链接；另有 `knowledge/.git/**` 作为仓库元数据前缀处理 |
| 回滚备份 | `/tmp/xcrz-demo-dev-docs-knowledge-scratch-20260718.tar.gz`，456 KiB，SHA-256 `50c5d651142313dfc659766490867e98a235a1ad9cb71deeea2d4d058372b02c`，`gzip -t` 通过 |
| 删除授权 | `auth-20260718-xcrz-demo-dev-docs-knowledge-scratch-absorb-delete`；只允许在吸收和门禁通过后删除三个精确目录 |

完整逐文件路径、源 SHA-256、处置类别、Hub 落点和删除前后状态见 `artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`。

## docs 吸收结果

### 已有覆盖的 27 个文件

架构、既有计划、报告、项目 runbook、标准和示例等 27 个文件的当前 SHA-256 已能在 Hub 现有 source provenance 或 canonical 资产中命中，因此不复制第二份正文。manifest 对每个文件保留源 hash，并将处置标为 `covered-by-existing-hub-provenance`。

### 17 个未覆盖文件

这 17 个文件在本轮审计前没有当前 SHA-256 的 Hub 证据，也未在可依赖的外层 Git 历史或其他副本中发现。本文附录 A1–A17 保留完整文本，并在 manifest 中逐一绑定源 SHA-256。

处置边界如下：

- `docs/README.md` 的旧入口 `~/embedded/knowledge` 已被 `~/knowledge-hub` 取代，只保留历史索引和迁移语义。
- `diag-usage-guide.md` 保留发现先行、catalog/help、local/remote、provider 生命周期和 suite 语义；命令仍须以当前固件运行时 help 为准。
- Sensor/Task/App 联调指南保留为项目候选：`CAMERA` 管 pipeline，`VIDEO` 只管选定流；task/app 管理 lease；唤醒不自动开 camera；`AUDIO` 仍为 reserved；`MIC` 是历史 PCM 推送语义；必须检查每条 `DeviceCtrlAck.results`。
- 项目 skill 和 `openai.yaml` 只作为草案证据保留，没有安装到 Codex skill 目录，也没有自动启用。
- media pipeline suspend 的计划、风险账本和检查点全部保留，但以 `STATE.md` 与 P6 证据为当前摘要；P0–P5 中的 `pending` 是没有回填的历史状态，不能覆盖 P6 已记录的实现证据。

## media pipeline suspend 当前事实

已观察到的事实：

- API video/audio suspend、resume、isRunning 以及 DVR media suspend 方向已实现。
- API object build 已通过。
- Sensor orchestration 入口已实现，但全量和定向 Sensor object build 被既有 include/proto/header 漂移阻塞。
- DVR 的目标语义是保留 record intent、暂停数据面、不写空帧，并在恢复后等待有效关键帧路径。

尚未闭环：

- Sensor 已知构建漂移：缺失 common transport 头、display include/proto enum 漂移，以及 `VSHDIOS_Init` 声明不一致。
- idle、video、mic、DVR、remote monitor 板端 smoke 未执行。
- 50 轮 suspend/resume 压力未执行。
- camera/mic 功耗下降未测，是否需要 HDI power gate 仍未知。
- R5（功耗）、R6（远程监控降级语义）、R8（并发/压力）等风险仍未关闭。

因此本轮只声明“文档内容已吸收”，不声明 media pipeline 功能完成。

## scratch extract-first 结果

### 可复用结论

1. 多个随机 `SIGBUS` 分别出现在 Agora、TOF `_CopyBytes` 和 Sensor audio subscription 等不同线程/模块，且伴随 corrupt stack 特征；历史推断更偏向 UBIFS/存储或系统级不稳定，但缺少连续 ECC/坏块和内核日志闭环，仍须按“内核日志 + I/O 并发 + core 时间线”联合取证。
2. WAV 路径历史 core 指向 `audio_wav.c` 解析链；stream 层曾修复 fd=0、短读短写、`EINTR` 和 `Read8` 返回值，并增加 `[WAV_GUARD]`。由于旧 core 存在二进制漂移提示，必须用当前修复后二进制重新复现，不能把历史 core 当作当前根因证明。
3. Diag V4 历史方案采用 Hybrid 生命周期与双层 RefCount，强调 catalog/help 发现先行、owner-managed provider 和事务化维护语义。该结论已经进入既有项目 spec/provenance，本条目仅保留它与 scratch hash 的关联。
4. V4 会话接力记录了 APP_UART、HDI VI、API DVR 等 owner 生命周期拆分的阶段状态；它是 2026-05-10 的历史实现快照，使用前必须核对当前源码。

### 明确排除

4 份 `context-preflight` 主要是未填写模板、完整脏工作树列表、二进制变化和旧提交列表，没有可独立复用的结论。它们不复制到长期正文；manifest 仍保留每个文件的 SHA-256、`extract-first/no-long-term-body` 处置和原因。两份 session wrap 与两份 resume/wrap 也不复制 raw session，只保留上述结论。

未写入 `~/.codex/memories`。

## 安全与排除检查

- 没有符号链接，因此不存在链接逃逸。
- 关键密钥、常见云 token、Bearer header 和密码赋值模式的文件名扫描未发现真实 secret；唯一 password 规则命中是脚本中的 `echo "pwd=$(pwd)"`，属于当前目录打印，不是凭证。
- `knowledge/.git/**` 是 Git 对象和引用，只进入前缀级 provenance，不进入长期正文。
- 13 个 `__pycache__/*.pyc` 是可再生缓存，明确排除。
- raw logs、core、SDK 压缩包、release binary 和 memory 均未写入 Hub。

## 验证与删除门槛

| Command | 预期 | 本轮用途 |
| --- | --- | --- |
| `rtk gzip -t /tmp/xcrz-demo-dev-docs-knowledge-scratch-20260718.tar.gz` | 0 | 确认回滚备份可解压 |
| `rtk sha256sum /tmp/xcrz-demo-dev-docs-knowledge-scratch-20260718.tar.gz` | 固定为 `50c5d651…372b02c` | 绑定回滚身份 |
| `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-18` | 0 | Hub 主门禁 |
| `rtk bash ~/knowledge-hub/tools/knowledge-link-audit.sh --strict --json` | task scope 无错误 | 全局 `blocking_broken_count=0`，两个新增条目无 property/link/MOC 错误；仓内另有 1 个本任务前已存在的 QIVW 验证条目 `summary_zh` 镜像漂移，保持用户变更不动 |
| `rtk bash ~/knowledge-hub/tools/knowledge-orphan-files.sh --all --strict --json` | 0 | 长期正文均有精确 registry 或冻结集合覆盖 |
| 三个 `rtk test ! -e <exact-path>` | 0 | 删除后确认三个目录均不存在 |

删除准入要求为：备份完整性和固定 hash 通过、`knowledge-check` 通过、`knowledge-orphan-files --all --strict` 通过、link audit 对本轮两个新增条目无错误、全局无 blocking broken link，且 manifest 的 243 个文件均有明确处置。全局 link audit 的唯一既有 property drift 不属于本任务写入范围，已单独披露，不用修改用户的并行 QIVW 工作来换取表面全绿。删除不会扩大到源根其他路径。

## 删除与恢复演练结果

- 授权：`auth-20260718-xcrz-demo-dev-docs-knowledge-scratch-absorb-delete`。
- 删除：对 `<resolved-source-root>/docs`、`knowledge`、`scratch` 三个精确目录执行一次 `rtk rm -rf -- ...`，退出码为 0。
- 不存在性：删除后一次组合检查确认三个目录均不存在，退出码为 0；外层 Git 对三条 scoped path 无状态项。
- 备份：删除后再次执行 `gzip -t`，并确认 SHA-256 仍为 `50c5d651142313dfc659766490867e98a235a1ad9cb71deeea2d4d058372b02c`。
- 恢复演练：在 `/tmp` 隔离目录完整解压备份，重算 243 个非 Git 文件，`243/243` 匹配、0 mismatch；`knowledge/.git/HEAD` 和 object 目录存在。演练副本随后清理，不修改源项目。
- 边界：没有删除源根其他路径，没有写远端 Git、memory、active、owner decision 或外部系统。

## 剩余风险

- 本报告附录保存的是围栏内的完整文本，不把源 frontmatter 中的 `active`、旧 owner 或旧路径解释为 Hub 当前权威。
- `/tmp` 备份是本机回滚副本，不是远端发布或长期灾备；Hub 正文与远端 `embedded/knowledge@cadbf4d` 承担长期可检索/可追溯部分。
- 媒体休眠、Sensor 联调和 diag 命令仍须按当前源码、固件和设备重新验证。
- 删除后若需要恢复，应先检查父目录冲突，再按授权账本中的 rollback_path 解压并复核 243 个 SHA-256。

## 附录 A：17 个未覆盖项目文档完整文本

以下附录用于在删除原目录后保留其全部可读内容。每个源 SHA-256 以删除前字节计算；围栏内文本逐行来自源文件，围栏本身不是源文件内容。

### A1. `docs/README.md`

- 原始 SHA-256：`548a04bd5608b1a3c53aa12d3138feb661c3a71016d9986b6543f6152d59f9fb`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
---
title: 项目 Docs 总入口
doc_type: index
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-18
tags: [docs, project, knowledge]
related: []
validation_refs: []
---

# 项目 Docs 总入口

本目录只保留当前项目强绑定文档。团队通用知识库统一放在：

```text
~/embedded/knowledge
```

远程仓库：

```text
ssh://git@192.168.1.4:10022/embedded/knowledge.git
```

建议本机环境变量：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

## 本项目保留内容

1. `architecture/`：当前项目架构、模块边界、诊断命令架构。
2. `runbooks/`：当前项目构建部署、标定、专项工具使用。
3. `specs/`：当前项目设计规格。
4. `plans/`：当前项目实施计划归档；默认不作为当前执行来源。
5. `reports/`：当前项目分析、验证、复盘报告归档；默认不作为当前门禁来源。
6. `standards/`：当前项目特有依赖基线。
7. `skills/`：当前项目内可审查的 Codex skill 草案，不自动启用。
8. `../tools/`：当前项目对团队公共工具的轻量适配层。

## 团队知识库内容

以下内容不再放在当前项目仓，统一查阅 `~/embedded/knowledge`：

1. 通用 C/C++ 编码规范、Agent/Skill 工程基线。
2. ASAN、GDB、core dump、SIGBUS、crash bundle 等通用排障手册。
3. `tools/debug/`、`tools/sigmastar/` 等公共脚本。
4. `tools/.codex/skills/` 团队调试技能。
5. SigmaStar 平台通用知识、能力矩阵、主题索引与归档 manifest。
6. 文档模板与文档治理脚本。

## 文档状态规则

1. `status: active`：当前仍可作为设计、构建、排障或工具使用的有效入口。
2. `status: archived`：历史计划、历史报告或已完成会话记录，只能作为背景参考。
3. 归档计划中的未勾选步骤不是当前待办；重新启用前必须核对源码、构建脚本和实际产物。
4. 历史报告中的旧验证命令只代表当时执行记录；当前验证优先使用本项目现有脚本和 `~/embedded/knowledge` 的公共门禁。

## 当前生效项目文档

- `docs/architecture/project-overview-design.md`
- `docs/architecture/project-detailed-design.md`
- `docs/architecture/project-core-module-design.md`
- `docs/architecture/module-catalog.md`
- `docs/architecture/hdi-api-app-functional-overview.md`
- `docs/architecture/diag-command-architecture-final.md`
- `docs/specs/2026-05-10-diag-v4-hybrid-refcount-discovery-spec.md`
- `docs/runbooks/project-build-and-deploy-guide.md`
- `docs/runbooks/project-debug-tools-guide.md`
- `docs/runbooks/irlight-sw-threshold-calibration.md`
- `docs/runbooks/prog-tool-usage-guide.md`
- `docs/runbooks/sensor-task-app-media-control-integration-guide.md`
- `docs/standards/third-party-libraries-reference.md`

## 项目工具入口

- `tools/README.md`
- `tools/debug/README.md`
- `tools/debug/project-knowledge-debug.sh`

## 历史资料入口

- `docs/plans/`：历史计划与阶段性实施方案。
- `docs/reports/`：历史分析、发布说明、会话归档和验证记录。
~~~~

### A2. `docs/runbooks/diag-usage-guide.md`

- 原始 SHA-256：`5fa3be18064e02c4f6bbddd113034463105a5a0cb22582eed3bcddca0e207795`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
---
title: Diag 使用指南
doc_type: runbook
knowledge_type: guideline
maturity: active
status: active
owner: team-core
created: 2026-05-26
last_updated: 2026-05-27
tags: [diag, prog-cli, prog-tool, runbook]
related:
  - ../standards/diag-command-metadata-standard.md
  - ../architecture/diag-command-architecture-final.md
  - ../specs/2026-05-10-diag-v4-hybrid-refcount-discovery-spec.md
validation_refs: []
---

# Diag 使用指南

## 1. 定位

`diag` 是设备侧统一诊断命令体系。命令由运行时 provider 注册，参数说明由运行时
`diag.sys.catalog.run` 和 `diag.sys.help.run` 返回。

终态边界：

- `/customer/bin/prog_cli` 只作为上位机通用入口，不硬编码业务命令参数。
- `/customer/bin/prog_tool` 只作为本地/远端诊断执行器，不替代单命令 help。
- 业务命令是否存在、需要哪些参数、是否有副作用，以运行时 catalog/help 为准。
- `modules/api` 和 `modules/hdi` 不注册运行时 diag provider；运行时 provider 统一放在
  `modules/app/src/app_diag/provider/`。

## 2. 入口选择

### 2.1 通过 `prog_cli` 调用运行中设备

适用于设备业务进程和 `cmd_server` 已运行的场景。

```bash
/customer/bin/prog_cli diag list
/customer/bin/prog_cli diag catalog
/customer/bin/prog_cli diag help
/customer/bin/prog_cli diag help <diag.command>
/customer/bin/prog_cli diag run <diag.command> '<json>'
```

常用状态入口：

```bash
/customer/bin/prog_cli diag provider registry state list
/customer/bin/prog_cli diag provider manager state list
```

### 2.2 通过 `prog_tool` 直接执行

`prog_tool` 支持本地进程内执行和远端转发执行。

```bash
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=local
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=remote
```

模式差异：

| mode | 执行位置 | 依赖 | 典型用途 |
|---|---|---|---|
| `local` | `prog_tool` 进程内启动 APPDIAG runtime | 自动拉起本地 providers 和必要依赖 | 本地单元/组件诊断、strict suite |
| `remote` | 通过 `cmd_server` 转发到目标业务进程 | 目标进程和 `cmd_server` 已在线 | 现场设备诊断、业务运行态检查 |

本地模式若 provider up 失败，会直接返回失败，不再继续伪装成 command-not-found。
失败时 `prog_tool` 会输出本地 provider up 摘要，列出失败 provider 和返回码。

## 3. 标准发现流程

不要凭文档猜参数。标准流程固定为：

1. 确认诊断链路可用。
2. 查询命令目录。
3. 查询单命令 help。
4. 按 help 返回的 example 执行。
5. 根据返回 JSON 判断结果。

示例：

```bash
/customer/bin/prog_cli diag list
/customer/bin/prog_cli diag catalog
/customer/bin/prog_cli diag help <diag.command>
/customer/bin/prog_cli diag run <diag.command> '<json>'
```

使用 `prog_tool` 时：

```bash
/customer/bin/prog_tool run-cmd diag.sys.catalog.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=local
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=local
```

远端场景把 `--mode=local` 换成 `--mode=remote`。

读取设备 SN 的只读命令：

```bash
/customer/bin/prog_cli diag help diag.api.factory.identity.sn.get.run
/customer/bin/prog_cli diag run diag.api.factory.identity.sn.get.run '{}'
```

## 4. 测试人员常用指令

本节命令面向设备侧测试人员，默认使用发布路径 `/customer/bin/prog_tool`，并使用 `--mode=local`
在工具进程内拉起本地 diag runtime 和 providers。执行具体业务命令前，仍建议先执行 help 查看当前固件实际参数说明。

### 4.1 基础发现

```bash
/customer/bin/prog_tool run-cmd diag.sys.ping.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.sys.catalog.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=local
```

### 4.2 Provider 状态

```bash
/customer/bin/prog_tool run-cmd diag.provider.registry.state.list.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.provider.manager.state.list.run '{}' --mode=local
```

### 4.3 读取设备 SN

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.api.factory.identity.sn.get.run"}' --mode=local
/customer/bin/prog_tool run-cmd diag.api.factory.identity.sn.get.run '{}' --mode=local
```

### 4.4 UART 与版本检查

```bash
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"right"}' --mode=local
```

如果这些命令失败，先处理 UART/MCU 链路，不要继续做电机 OTA 或温度阈值写入。

### 4.5 修改充电温度保护阈值

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"diag.app.uart.charge_temp_range.set.run"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.charge_temp_range.set.run '{"low_cutoff_c":-3,"low_recover_c":1,"high_recover_c":42,"high_cutoff_c":46}' --mode=local
```

阈值必须满足：

```text
low_cutoff_c < low_recover_c < high_recover_c < high_cutoff_c
```

### 4.6 主板 MCU OTA

主板 MCU OTA 使用 `maint.app.uart.ota.*` 命令，不带 `target` 参数。执行前确认固件文件已经在设备本地，
例如 `/tmp/mcu.bin`。

先确认维护命令参数：

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"maint.app.uart.ota.upgrade.run"}' --mode=local
```

执行升级：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.upgrade.run '{"file":"/tmp/mcu.bin","retry":3}' --mode=local
```

升级成功后重启主板 MCU，并查询版本确认：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.reboot.run '{}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.versions.get.run '{}' --mode=local
```

失败排查时可查询 OTA 状态；如果确认需要清除 OTA 标记，再执行 `clear_flag`：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.ota.status.run '{}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.ota.clear_flag.run '{}' --mode=local
```

### 4.7 电机 MCU OTA

先确认维护命令参数：

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"maint.app.uart.motor_ota.upgrade.run"}' --mode=local
```

升级左电机：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"left","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"left"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"left"}' --mode=local
```

升级右电机：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"right","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"right"}' --mode=local
/customer/bin/prog_tool run-cmd diag.app.uart.motor.app_version.run '{"target":"right"}' --mode=local
```

左右电机使用同一固件时可使用 `target=both`，但现场排障优先建议左右分开升级：

```bash
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.upgrade.run '{"target":"both","file":"/tmp/motor.bin","retry":3}' --mode=local
/customer/bin/prog_tool run-cmd maint.app.uart.motor_ota.reboot.run '{"target":"both"}' --mode=local
```

### 4.8 本地 suite

```bash
/customer/bin/prog_tool list
/customer/bin/prog_tool run strict --mode=local
/customer/bin/prog_tool run hdi.strict --mode=local
/customer/bin/prog_tool run api.strict --mode=local
/customer/bin/prog_tool run app.strict --mode=local
```

`env` suite 依赖硬件、网络、存储和业务状态，现场执行时建议带 `--continue`：

```bash
/customer/bin/prog_tool run env --mode=local --continue
```

## 5. 系统命令

| 命令 | 用途 |
|---|---|
| `diag.sys.ping.run` | 验证 diag 调用路径是否可达 |
| `diag.sys.list.run` | 返回已注册命令名列表 |
| `diag.sys.catalog.run` | 返回命令目录、summary、args_schema、example |
| `diag.sys.help.run` | 返回单命令帮助 |
| `diag.sys.version.matrix.run` | 返回 diag 版本和命令数量 |
| `diag.provider.registry.state.list.run` | 返回 registry provider 状态、引用计数和最近错误 |
| `diag.provider.manager.state.list.run` | 返回 `cmd_node` 托管策略和最近 up/down 返回码 |
| `diag.provider.up.run` | 拉起允许外部管理的 provider |
| `diag.provider.down.run` | 下线允许外部管理的 provider |

provider 状态查询必须明确对象：

- 查 registry 状态：`diag.provider.registry.state.list.run`
- 查 `cmd_node` 托管状态：`diag.provider.manager.state.list.run`

## 6. Provider 状态判断

### 6.1 Registry 状态

```bash
/customer/bin/prog_cli diag run diag.provider.registry.state.list.run '{}'
```

关注字段：

| 字段 | 含义 |
|---|---|
| `provider` | provider 名称 |
| `state` | registry 内状态 |
| `owner_ref` | owner 生命周期引用计数 |
| `ext_ref` | 外部管理引用计数 |
| `last_error` | registry 最近错误 |

### 6.2 Manager 状态

```bash
/customer/bin/prog_cli diag run diag.provider.manager.state.list.run '{}'
```

关注字段：

| 字段 | 含义 |
|---|---|
| `provider` / `alias` | provider 名称和 shortcut |
| `auto_up` | 是否随 `cmd_node` 初始化自动拉起 |
| `allow_external_control` | 是否允许 `diag.provider.up/down.run` 管理 |
| `managed_up` | `cmd_node` 当前是否认为该 provider 已托管上线 |
| `last_up_ret` | 最近一次 up 返回码 |
| `last_down_ret` | 最近一次 down 返回码 |

判断规则：

- catalog 中缺少某类命令时，先查 manager 状态，看 `last_up_ret` 是否非 0。
- manager 显示 up 成功但 registry 缺 provider 时，优先检查 provider 注册/反注册路径。
- `allow_external_control=false` 的 provider 不能用 `diag.provider.up/down.run` 手动管理。

## 7. Provider 生命周期

终态规则：

- 自动 provider 的 `ModuleUp()` 只能注册命令和元数据。
- 不允许在 `ModuleUp()` 中初始化硬件、连接网络、启动业务线程、订阅事件、覆盖业务 callback。
- 会改变设备状态或占用资源的动作必须是显式 `*.run` 命令。
- provider down 只负责释放 diag 自己持有的资源，不能误清业务 owner 的资源。
- owner 模块自管的 provider 不进入 `cmd_node` 托管表。

外部管理命令只适用于 `allow_external_control=true` 的 provider：

```bash
/customer/bin/prog_cli diag run diag.provider.up.run '{"provider":"<provider>"}'
/customer/bin/prog_cli diag run diag.provider.down.run '{"provider":"<provider>"}'
```

## 8. 返回值判断

标准 diag 返回 JSON：

```json
{"code":0,"msg":"ok","data":{}}
```

判断顺序：

1. 先看工具进程退出码。
2. 再看 diag 返回 JSON 的 `code`。
3. 再看 `msg` 和 `data` 中的业务字段。

常见语义：

| 现象 | 优先检查 |
|---|---|
| command not found | provider 是否注册、catalog 是否包含命令 |
| provider_owner_managed | 该 provider 不允许外部 up/down |
| bad_request | JSON 参数缺失或类型不符合 help |
| unsupported_provider | provider 名称或 profile 不支持 |
| reply_too_large | 命令返回超过当前回复缓冲 |
| local provider up failed | 本地依赖、provider `ModuleUp()` 和静态门禁 |

## 9. Suite 使用

`prog_tool` 支持批量 suite：

```bash
/customer/bin/prog_tool list
/customer/bin/prog_tool run <suite> --mode=local
/customer/bin/prog_tool run <suite> --mode=remote
```

常见 suite：

| suite | 定位 |
|---|---|
| `strict` | 全部确定性 strict 用例 |
| `env` | 全部环境依赖用例 |
| `all` | strict + env |
| `hdi.strict` / `api.strict` / `app.strict` | 分层确定性用例 |
| `hdi.env` / `api.env` / `app.env` | 分层环境依赖用例 |

执行原则：

- strict 用例必须稳定，不能依赖在线设备、外设状态或现场网络。
- env 用例允许受硬件、存储、网络、业务进程状态影响。
- 不要通过放宽 strict 期望来隐藏真实初始化错误。

## 10. Session 模式

交互或脚本化连续诊断使用 session：

```bash
/customer/bin/prog_tool session --mode=local
/customer/bin/prog_tool session --mode=remote
/customer/bin/prog_tool session --mode=remote --script=<file>
```

脚本适合把 catalog、help、状态查询和业务命令串联成一次可复现诊断流程。脚本中仍应先查
`diag.sys.help.run`，再执行具体命令。

## 11. 新增命令后的检查

新增或修改 diag 命令后至少运行：

```bash
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_command_quality.py
rtk python3 tools/diag/checks/check_diag_naming.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_layer_deps.py
```

涉及 C 代码时，还要运行对应模块构建，例如：

```bash
rtk make modules/app_obj_all -j20
rtk make app_tool_app_all -j20
rtk make cli_app_all -j20
```

## 12. 快速排障路径

1. `diag.sys.ping.run` 不通：先查 `cmd_server`、IPC endpoint、目标进程是否在线。
2. `diag.sys.catalog.run` 无目标命令：查 manager 状态和 registry 状态。
3. help 返回参数不完整：修 provider 的 `pfnCollectMeta`，不要改 `cli` usage。
4. local 模式失败、remote 模式正常：查 `prog_tool` 本地依赖和 provider up。
5. remote 模式失败、local 模式正常：查目标业务进程、cmd_server 转发和目标环境依赖。
6. 命令有副作用：确认是否属于 env suite，并确认 stop/cleanup 路径。

本地 `run-cmd` 返回 `no_active_handler` 时，如果本次启动存在 provider up 失败，`prog_tool` 会追加
`provider/up_failures` 摘要。该摘要只用于工具侧排障，不属于 diag 命令自身 reply。
~~~~

### A3. `docs/runbooks/sensor-task-app-media-control-integration-guide.md`

- 原始 SHA-256：`a267d195bc991aa0afa4df78ff8c74b6bc8ed9554d1a31fcb6778977c660a65f`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
---
title: Sensor 与 Task/App 音视频流控联调指南
doc_type: runbook
knowledge_type: integration
maturity: draft
status: active
owner: sensor-task-app
created: 2026-07-07
last_updated: 2026-07-07
tags: [sensor, task, app, video, audio, camera, dvr, sleep, integration]
related:
  - docs/plans/media-pipeline-suspend/PLAN.md
  - docs/plans/media-pipeline-suspend/RISK_LEDGER.md
  - modules/proto/sensor_ctrl.proto
  - modules/proto/sensor_info.proto
validation_refs:
  - modules/sensor/main/sensor_entry.cpp
  - modules/sensor/video/video_capture.cpp
  - modules/sensor/hardware/hardware_api.cpp
  - modules/sensor/video/video_encoded_frame_hub.cpp
  - modules/sensor/video/video_raw_frame_hub.cpp
---

# Sensor 与 Task/App 音视频流控联调指南

本文面向 `task/app/iot/ai` 侧对接 sensor 音视频控制链路。当前终态方向是：task/app 负责业务 lease 和调用时机，sensor 只被动执行 camera pipeline 与视频流推送控制，不在 sensor 内做业务判断。

## 1. 当前结论

1. 摄像头控制拆成两个维度：
   - `CAMERA`：打开或关闭摄像头 pipeline，包含 VI 与 DVR media suspend/resume 编排。
   - `VIDEO`：开启或关闭某一路视频流推送，不自动打开 camera。
2. task/app 必须先 `CAMERA enable=true`，再 `VIDEO enable=true`。如果 camera 未运行直接开视频流，sensor 返回 `camera pipeline is not running`。
3. 唤醒后不自动打开 camera。只有远程监控、录像、QR、AI vision 等业务存在明确 video lease 时，task/app 才打开 camera 和所需视频流。
4. audio input pipeline 默认由 sensor 内部初始化和管理。`AUDIO` 协议已预留，但当前 sensor 返回 `audio stream control is reserved`，不要作为正式音频流控入口。
5. 历史 `MIC` 仍表示 PCM 推送控制，不是底层 audio pipeline suspend/resume。

## 2. 控制通道

本地同进程或同运行环境使用 `ThreadClient` 访问 sensor 控制服务：

```cpp
common::ThreadClient client(common::ChannelList::channel_sensor_dev_ctrl_, 3000);
```

通道与消息：

| 项目 | 值 |
| --- | --- |
| 请求通道 | `common::ChannelList::channel_sensor_dev_ctrl_` |
| 通道字符串 | `sensor/dev/ctrl` |
| 请求消息 | `proto.sensor_ctrl.DeviceCtrl` |
| 应答消息 | `proto.sensor_info.DeviceCtrlAck` |
| 建议超时 | 本地 3000 ms；bridge 转发可放宽到 30000 ms |

bridge/TCP 转发场景中，bridge 会把 TCP request 转发到内部 `sensor/dev/ctrl`。默认 request 端口当前为 `17002`，成功时仍返回 `DeviceCtrlAck`。如果 bridge 层解析失败，可能返回 `proto.common.AckResult`，调试工具应先尝试解析 `DeviceCtrlAck`，失败时再解析 `AckResult`。

## 3. 视频控制协议

`DeviceCommand::CAMERA` 使用 `CameraPayload`：

```proto
message CameraPayload {
    bool enable = 1;
}
```

`DeviceCommand::VIDEO` 使用 `VideoPayload`：

```proto
message VideoPayload {
    enum Stream {
        STREAM_UNKNOWN = 0;
        MAIN_ENC       = 1;
        LOW_ENC        = 2;
        DS1_RAW        = 3;
        DS2_RAW        = 4;
    }

    bool            enable  = 1;
    repeated Stream streams = 2;
}
```

流含义与数据通道：

| Stream | 用途 | 数据通道 |
| --- | --- | --- |
| `MAIN_ENC` | 主码流编码帧，面向高清远程监控/IOT | `shm/video/h264/main` |
| `LOW_ENC` | 低码流编码帧，面向低清远程监控/IOT | `shm/video/h264/low` |
| `DS1_RAW` | DS1 裸帧，当前主要给 QR/display 内部路径 | `shm/video/yuv/ds1` |
| `DS2_RAW` | DS2 裸帧，当前主要给 AI vision | `shm/video/yuv/ds2` |

编码帧和裸帧都通过 SHM 发布，帧元数据为 `proto.sensor_info.VideoFrameMeta`。控制 ACK 只表示命令执行结果，不携带视频帧。

## 4. 标准调用顺序

### 4.1 远程监控主码流

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[MAIN_ENC]
3. 订阅 shm/video/h264/main
4. 业务结束后 VIDEO enable=false streams=[MAIN_ENC]
5. 如果没有其他 camera lease，再 CAMERA enable=false
```

### 4.2 远程监控低码流

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[LOW_ENC]
3. 订阅 shm/video/h264/low
4. 业务结束后 VIDEO enable=false streams=[LOW_ENC]
5. 如果没有其他 camera lease，再 CAMERA enable=false
```

### 4.3 AI vision 使用 DS2

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[DS2_RAW]
3. 订阅 shm/video/yuv/ds2
4. AI vision 停止后 VIDEO enable=false streams=[DS2_RAW]
5. 如果没有其他 camera lease，再 CAMERA enable=false
```

### 4.4 QR/display 使用 DS1

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[DS1_RAW]
3. 订阅 shm/video/yuv/ds1
4. QR/display 停止后 VIDEO enable=false streams=[DS1_RAW]
5. 如果没有其他 camera lease，再 CAMERA enable=false
```

DS1 与 DS2 的互斥由 HDI 层处理。task/app 侧仍应避免无意义的同时申请；若必须竞争，按业务约定 DS1 优先，DS2 失败或无帧时降级处理。

### 4.5 休眠与唤醒

进入休眠：

```text
1. 停止远程监控、AI vision 等外部 VIDEO lease。
2. 保留录像/QR/display 等仍有效的业务意图，但关闭不需要继续出帧的外部流。
3. 如果没有任何 camera lease，发送 CAMERA enable=false。
4. 确认视频 SHM 不再有新帧，摄像头进入省电状态。
```

唤醒：

```text
1. 不自动打开 CAMERA。
2. 当远程监控、录像、QR、AI vision 等业务明确申请时，发送 CAMERA enable=true。
3. 再按需发送 VIDEO enable=true streams=[...]。
```

录像注意事项：

```text
1. DVR_RECORD START/STOP 仍由 DVR_RECORD 命令控制。
2. CAMERA close 会触发 DVR media suspend，保留录像意图但停止写入新音视频帧。
3. CAMERA open 会触发 DVR media resume；如果仍存在录像意图，media 通路恢复。
4. 休眠期间录像空转不应产生新音视频文件数据；唤醒恢复后从新帧继续。
```

## 5. C++ 发送示例

通用发送函数：

```cpp
#include "absl/time/clock.h"
#include "absl/time/time.h"
#include "modules/common/transport/channel_list.h"
#include "modules/common/transport/thread_req_rep.h"
#include "modules/proto/sensor_ctrl.pb.h"
#include "modules/proto/sensor_info.pb.h"

bool SendSensorCtrl(const proto::sensor_ctrl::DeviceCtrl &req,
                    proto::sensor_info::DeviceCtrlAck *ack) {
    common::ThreadClient client(common::ChannelList::channel_sensor_dev_ctrl_, 3000);

    const std::string req_buf = req.SerializeAsString();
    if (req_buf.empty()) {
        return false;
    }

    const std::string ack_buf = client.sendRequest(req_buf);
    if (ack_buf.empty() || ack == nullptr) {
        return false;
    }

    return ack->ParseFromString(ack_buf);
}
```

打开 camera：

```cpp
proto::sensor_ctrl::DeviceCtrl req;
req.mutable_header()->set_timestamp(absl::ToUnixMicros(absl::Now()));
req.mutable_header()->set_sequence(next_sequence++);

auto *cmd = req.add_commands();
cmd->set_command_id(1);
cmd->set_device_type(proto::sensor_ctrl::DeviceCommand::CAMERA);
cmd->mutable_camera()->set_enable(true);

proto::sensor_info::DeviceCtrlAck ack;
const bool ok = SendSensorCtrl(req, &ack);
```

开启主码流：

```cpp
proto::sensor_ctrl::DeviceCtrl req;
req.mutable_header()->set_timestamp(absl::ToUnixMicros(absl::Now()));
req.mutable_header()->set_sequence(next_sequence++);

auto *cmd = req.add_commands();
cmd->set_command_id(2);
cmd->set_device_type(proto::sensor_ctrl::DeviceCommand::VIDEO);

auto *video = cmd->mutable_video();
video->set_enable(true);
video->add_streams(proto::sensor_ctrl::VideoPayload::MAIN_ENC);

proto::sensor_info::DeviceCtrlAck ack;
const bool ok = SendSensorCtrl(req, &ack);
```

关闭主码流：

```cpp
proto::sensor_ctrl::DeviceCtrl req;
req.mutable_header()->set_timestamp(absl::ToUnixMicros(absl::Now()));
req.mutable_header()->set_sequence(next_sequence++);

auto *cmd = req.add_commands();
cmd->set_command_id(3);
cmd->set_device_type(proto::sensor_ctrl::DeviceCommand::VIDEO);

auto *video = cmd->mutable_video();
video->set_enable(false);
video->add_streams(proto::sensor_ctrl::VideoPayload::MAIN_ENC);

proto::sensor_info::DeviceCtrlAck ack;
const bool ok = SendSensorCtrl(req, &ack);
```

关闭 camera：

```cpp
proto::sensor_ctrl::DeviceCtrl req;
req.mutable_header()->set_timestamp(absl::ToUnixMicros(absl::Now()));
req.mutable_header()->set_sequence(next_sequence++);

auto *cmd = req.add_commands();
cmd->set_command_id(4);
cmd->set_device_type(proto::sensor_ctrl::DeviceCommand::CAMERA);
cmd->mutable_camera()->set_enable(false);

proto::sensor_info::DeviceCtrlAck ack;
const bool ok = SendSensorCtrl(req, &ack);
```

## 6. ACK 判定

`DeviceCtrlAck.success` 表示这一批 commands 是否全部成功。每条命令必须检查 `results`：

```text
command_id: 对应请求 command_id
success:    单条命令是否成功
error_code: 0 成功，非 0 失败
error_msg:  失败原因
```

建议调试打印：

```cpp
for (const auto &result : ack.results()) {
    printf("cmd=%u success=%d code=%u msg=%s\n",
           result.command_id(),
           result.success(),
           result.error_code(),
           result.error_msg().c_str());
}
```

当前关键错误码：

| error_code | 含义 | 常见原因 |
| --- | --- | --- |
| `0` | 成功 | 命令执行成功 |
| `1` | 参数非法 | payload 缺失、VIDEO streams 为空、stream 不支持 |
| `2` | 不支持 | 当前命令预留或未实现，如 `AUDIO` |
| `3` | 执行失败 | API/HDI/sensor 内部执行失败 |
| `4` | camera 未运行 | 未先 `CAMERA enable=true` 就开启 `VIDEO` |

## 7. task/app 侧 lease 管理

不要让业务模块散落直接发送 camera 开关。建议集中到一个 manager：

```text
CameraLeaseManager
  camera_ref_count
  stream_ref_count[MAIN_ENC]
  stream_ref_count[LOW_ENC]
  stream_ref_count[DS1_RAW]
  stream_ref_count[DS2_RAW]
  owner -> streams 映射
```

申请：

```text
AcquireVideoLease(owner, stream):
  如果 owner 已持有 stream，直接返回成功。
  如果 camera_ref_count == 0，发送 CAMERA enable=true。
  CAMERA 成功后 camera_ref_count++。
  如果 stream_ref_count[stream] == 0，发送 VIDEO enable=true streams=[stream]。
  VIDEO 成功后 stream_ref_count[stream]++，记录 owner。
```

释放：

```text
ReleaseVideoLease(owner, stream):
  如果 owner 未持有 stream，忽略或打印 warning。
  stream_ref_count[stream]--。
  如果 stream_ref_count[stream] == 0，发送 VIDEO enable=false streams=[stream]。
  camera_ref_count--。
  如果 camera_ref_count == 0，发送 CAMERA enable=false。
```

失败处理：

```text
CAMERA open 失败:
  不增加任何 ref_count。

VIDEO open 失败:
  回滚本次 camera_ref_count。
  如果 camera_ref_count 回到 0，发送 CAMERA enable=false。

VIDEO close 失败:
  标记 stream 为 close_pending。
  后台重试一次；休眠前必须强制清理。

CAMERA close 失败:
  标记 camera 状态 unknown。
  下一次休眠前重试 CAMERA enable=false。
```

## 8. 联调用例

最小正向用例：

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[MAIN_ENC]
3. 订阅 shm/video/h264/main，确认 2 秒内有帧
4. VIDEO enable=false streams=[MAIN_ENC]
5. CAMERA enable=false
```

边界用例：

```text
1. 不开 CAMERA，直接 VIDEO enable=true streams=[MAIN_ENC]
2. 期望 ACK 失败：error_code=4，error_msg=camera pipeline is not running
```

多流用例：

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[MAIN_ENC, LOW_ENC]
3. 分别订阅 shm/video/h264/main、shm/video/h264/low
4. VIDEO enable=false streams=[LOW_ENC]
5. MAIN_ENC 应继续有帧，LOW_ENC 停止
6. VIDEO enable=false streams=[MAIN_ENC]
7. CAMERA enable=false
```

DS 互斥用例：

```text
1. CAMERA enable=true
2. VIDEO enable=true streams=[DS1_RAW]
3. 再 VIDEO enable=true streams=[DS2_RAW]
4. 观察 ACK 和 SHM 出帧；task/app 必须能处理 DS2 失败或无帧
5. 按实际成功流释放
```

休眠唤醒用例：

```text
1. 开启 MAIN_ENC，确认有帧。
2. 进入休眠：VIDEO disable MAIN_ENC，再 CAMERA disable。
3. 确认视频帧停止。
4. 唤醒但不申请业务：CAMERA 不应自动打开。
5. 重新申请 MAIN_ENC：CAMERA enable，再 VIDEO enable MAIN_ENC。
6. 确认恢复出帧。
```

## 9. 日志与排障

sensor 侧关键日志：

```text
camera pipeline opened
camera pipeline closed
camera open failed
camera close failed
video stream enable rejected: camera pipeline is not running
Video encoded source callback registered
Video encoded source callback unregistered
Video raw source callback registered
Video raw source callback unregistered
audio stream control is reserved
```

ACK 成功但没有帧时，优先检查：

```text
1. 是否订阅了正确 SHM channel。
2. VIDEO stream 是否真正 enable。
3. camera 是否仍 running。
4. DS1/DS2 是否互斥。
5. SHM subscriber 是否过慢导致 LATEST_ONLY 丢帧。
6. 编码流是否需要等待 I 帧或 SPS/PPS。
```

## 10. 禁止做法

1. 不要用 `VIDEO enable=true` 期望 sensor 自动打开 camera。
2. 不要在唤醒时让 sensor 自动恢复所有流；恢复必须由 task/app 根据 lease 决定。
3. 不要把 `AUDIO` 当作已实现的音频流控。
4. 不要把 `MIC` 当作 audio pipeline 开关。
5. 不要在多个业务模块中直接散落 `CAMERA enable=false`。
6. 不要提交只看 `DeviceCtrlAck.success` 的调用逻辑；必须逐条检查 `results`。

## 11. 是否生成 agent 或 skill

可以生成。推荐分两层：

1. 项目内文档：本文作为 task/app 与 sensor 联调的稳定 runbook。
2. Codex skill：将本文中的契约、调用顺序、排障流程压缩成可触发的 skill，用于后续让 agent 自动审查或生成 task/app 对接代码。

当前已提供项目内 skill 草案：

```text
docs/skills/sensor-task-app-media-control/SKILL.md
docs/skills/sensor-task-app-media-control/agents/openai.yaml
```

该草案不会自动启用。若要正式启用，需要迁移到 `$CODEX_HOME/skills` 或 `~/.codex/skills`，再按 Codex skill 资产链路验证。
~~~~

### A4. `docs/skills/sensor-task-app-media-control/SKILL.md`

- 原始 SHA-256：`cb37ea936b8197cbf2d92ed539ad12d3bc84627a0720033447b6b7541dd5e2d3`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
---
name: sensor-task-app-media-control
description: Use when working on PCR02 sensor/task/app integration for camera pipeline control, video stream leases, sleep/wake media behavior, DVR media suspend/resume, or debugging DeviceCtrl commands around CAMERA, VIDEO, MIC, AUDIO, MAIN_ENC, LOW_ENC, DS1_RAW, and DS2_RAW.
---

# Sensor Task/App Media Control

Use this project skill to design, review, or implement task/app integration with `modules/sensor` media control.

## Required References

Read these files before changing code or giving a final integration answer:

- `docs/runbooks/sensor-task-app-media-control-integration-guide.md`
- `modules/proto/sensor_ctrl.proto`
- `modules/proto/sensor_info.proto`
- `modules/sensor/main/sensor_entry.cpp`
- `modules/sensor/video/video_capture.cpp`
- `modules/sensor/hardware/hardware_api.cpp`

Read these files when frame channels or SHM behavior matter:

- `modules/common/transport/channel_list.cpp`
- `modules/sensor/video/video_encoded_frame_hub.cpp`
- `modules/sensor/video/video_raw_frame_hub.cpp`

## Workflow

1. Classify the requested behavior as one of:
   - camera pipeline lifecycle
   - video stream push lifecycle
   - task/app lease management
   - sleep/wake behavior
   - DVR record interaction
   - audio or mic behavior
2. Preserve the boundary:
   - task/app owns business leases and decides when to request camera or streams.
   - sensor passively executes `CAMERA` and `VIDEO`.
   - `VIDEO` must not auto-open camera.
   - wake must not auto-open camera without an explicit lease.
3. Use the current protocol:
   - `DeviceCommand::CAMERA` with `CameraPayload.enable`.
   - `DeviceCommand::VIDEO` with `VideoPayload.enable` and `streams`.
   - video streams are `MAIN_ENC`, `LOW_ENC`, `DS1_RAW`, `DS2_RAW`.
   - `AUDIO` is reserved unless implementation has changed.
   - `MIC` is historical PCM push control, not audio pipeline suspend/resume.
4. For task/app code, require a centralized lease manager. Do not scatter raw camera close calls across business modules.
5. For debugging, always inspect `DeviceCtrlAck.results`, not only top-level `success`.
6. For validation, include at least:
   - `CAMERA enable -> VIDEO enable -> SHM frame observed`
   - `VIDEO enable without CAMERA` fails with camera-not-running
   - `VIDEO disable` stops the selected stream while other streams remain active
   - sleep disables streams and closes camera only when no camera lease remains

## Common Pitfalls

- Do not use `VIDEO enable=true` as a combined camera-open and stream-open command.
- Do not implement automatic camera restore after wake in sensor.
- Do not treat the reserved `AUDIO` command as production-ready.
- Do not use DS1 and DS2 simultaneously without handling HDI mutual exclusion behavior.
- Do not conclude a command succeeded unless each `DeviceCommandResult` succeeded.

## Output Expectations

When producing guidance or code review, include:

- the exact command sequence
- affected streams and SHM channels
- expected ACK success or error
- lease owner and release behavior
- validation commands or board smoke steps
- residual risks, especially DS1/DS2 mutual exclusion and board power evidence
~~~~

### A5. `docs/skills/sensor-task-app-media-control/agents/openai.yaml`

- 原始 SHA-256：`33dd6070ffccc3c8a2d1218f8b3a95496e8f8d8b1a6ed4607260472ac4a27c80`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~yaml
display_name: Sensor Task/App Media Control
short_description: Guide PCR02 task/app integration with sensor camera, video stream leases, sleep/wake, DVR, and media debug flows.
default_prompt: "Use $sensor-task-app-media-control to design, review, or debug PCR02 task/app integration with sensor CAMERA and VIDEO controls, lease management, and media stream validation."
~~~~

### A6. `docs/plans/media-pipeline-suspend/PLAN.md`

- 原始 SHA-256：`b1a90937cf3b7b7ecf9cb5a9c3543cb6bbb97e8898b79abacb0ed90a935f8150`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Media Pipeline Suspend Execution Plan

## Goal

实现 PCR02 Sensor 统一编排的 camera + mic media pipeline suspend/resume。
休眠时关闭音视频 pipeline，DVR/监控控制面保持空转或降级；唤醒后只根据 active lease 或 record intent 恢复音视频，不无条件启动 camera/mic。

## Scope

In:

- 新增 `VSAPIVIDEO_ViSuspend`、`VSAPIVIDEO_ViResume`、`VSAPIVIDEO_ViIsRunning`。
- 新增 `VSAPIAUDIO_AiSuspend`、`VSAPIAUDIO_AiResume`、`VSAPIAUDIO_AiIsRunning`。
- 新增或接入 DVR media suspended 状态，保留 record intent，不写空帧。
- 在 Sensor `HardwareApi` 增加 `suspend_media_pipeline`、`resume_media_pipeline`、`is_media_pipeline_running`。
- 在 `SensorEntry` 接入休眠/唤醒状态闭环和日志证据。

Out:

- 不做整机 SoC deep sleep、poweroff 或 MCU 常电域联动。
- 不让 task/app 直接调用 `VSAPIVIDEO_*`、`VSAPIAUDIO_*` 或 `VSHDI*`。
- 第一阶段不修改 `modules/hdi/**`，除非板端功耗验证证明 API suspend 不足。
- 不写空帧、不造假音频、不生成无真实媒体数据的录像内容。

## Parallel Suitability

部分可并行。共享 contract 必须串行冻结，`api_video.c` 和 `api_audio.c` 在 contract 冻结后可并行。

串行路径:

```text
P0 baseline
  -> P1 contract freeze
      -> P2A api_video + P2B api_audio
          -> P3 api_dvr media suspend
              -> P4 sensor HardwareApi
                  -> P5 SensorEntry
                      -> P6 integration validation
```

## Frozen Shared Boundaries

禁止并行写入:

- `modules/api/include/api_video.h`
- `modules/api/include/api_audio.h`
- `modules/api/include/api_dvr.h`
- `modules/proto/*.proto`
- root `Makefile`
- `build/*.mk`
- lockfile / generated artifacts

默认禁止写入:

- `modules/hdi/**`

若需要修改 `modules/hdi/**`，必须新增 `T8 HDI power gate` 并重新计划审查。

## Stages

| Stage | Goal | Scope Write | Done Criteria | Verification |
| --- | --- | --- | --- | --- |
| P0 | 冻结基线和触点清单 | none | 子仓状态、风险、下一步明确 | `rtk git -C modules/api status --short --branch` |
| P1 | 固化 API/DVR contract | API headers | 接口、幂等、错误语义固定 | `rtk make modules/api_obj_all -j20` |
| P2A | 实现 video suspend/resume/isRunning | `api_video.c` | video pipeline 幂等 suspend/resume | `rtk make modules/api_obj_all -j20` |
| P2B | 实现 audio suspend/resume/isRunning | `api_audio.c` | AI/mic pipeline 幂等 suspend/resume | `rtk make modules/api_obj_all -j20` |
| P3 | DVR media suspended 空转 | `api_dvr_record.c`, optional `api_dvr.h` | 保留 intent，不写空帧，可恢复 | `rtk make modules/api_obj_all -j20` |
| P4 | Sensor HardwareApi 编排 | `hardware_api.*` | 统一 suspend/resume media pipeline | `rtk make modules/sensor_obj_all -j20` |
| P5 | SensorEntry 状态闭环 | `sensor_entry.*` | 休眠/唤醒入口、状态、日志闭环 | `rtk make modules/sensor_obj_all -j20` |
| P6 | 集成验证 | tests/reports only | 编译、smoke、压力、功耗证据齐全 | see Final Gate |

## API Contract Candidate

```c
VS_S32 VSAPIVIDEO_ViSuspend(VS_VOID);
VS_S32 VSAPIVIDEO_ViResume(VSHDIVI_InitParam_t *pstInitParam);
VS_S32 VSAPIVIDEO_ViIsRunning(VS_BOOL *pbRunning);

VS_S32 VSAPIAUDIO_AiSuspend(VS_VOID);
VS_S32 VSAPIAUDIO_AiResume(VS_VOID);
VS_S32 VSAPIAUDIO_AiIsRunning(VS_BOOL *pbRunning);

VS_S32 VSAPIDVR_RecordMediaSuspend(VS_VOID);
VS_S32 VSAPIDVR_RecordMediaResume(VS_VOID);
VS_S32 VSAPIDVR_RecordIsMediaSuspended(VS_BOOL *pbSuspended);
```

Contract rules:

- `Suspend` is idempotent. Already suspended returns `VS_SUCCESS`.
- `Resume` is idempotent. Already running returns `VS_SUCCESS`.
- `IsRunning` / `IsMediaSuspended` return `VS_FAILURE` when output pointer is null.
- Existing `Init` / `DeInit` public behavior must not regress.
- DVR media suspend keeps record intent and pauses data plane.

## Final Gate

Required commands:

```bash
rtk make modules/api_obj_all -j20
rtk make modules/sensor_obj_all -j20
rtk make modules/hdi_obj_all -j20
rtk python3 tools/diag/checks/check_diag_layer_deps.py
rtk git -C modules/api diff --check
rtk git -C modules/sensor diff --check
rtk git -C modules/hdi diff --check
rtk bash ~/codex/scripts/final-ready.sh
```

Board validation:

- idle -> suspend -> resume: no lease should not auto-start camera/mic.
- video stream -> suspend -> resume: frames stop and can recover.
- mic capture -> suspend -> resume: PCM stops and can recover.
- record -> suspend 30s -> resume -> stop: no empty frame, new segment starts from key frame.
- remote monitor + record -> suspend -> resume: control plane remains, media plane degrades and recovers.
- suspend/suspend and resume/resume are idempotent.
- 50 suspend/resume cycles: no core, watchdog, deadlock, reader leak or callback use-after-free.
- Power meter confirms camera/mic pipeline current drops after suspend.
~~~~

### A7. `docs/plans/media-pipeline-suspend/STATE.md`

- 原始 SHA-256：`21000ea9169bd4e528964f79f6bdc3c5f319f8cfe718adc44c02a376a4277153`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Media Pipeline Suspend State

## Current Status

status: implemented-with-validation-blockers
current_stage: P6
last_updated: 2026-07-05

## Baseline

Observed before implementation:

- `modules/api`: `master...origin/master`, clean.
- `modules/sensor`: `master...origin/master`, clean.
- `modules/hdi`: `master...origin/master`, clean.

## Execution Rules

- All shell commands must use `rtk`.
- Manual file edits must use `apply_patch`.
- Do not commit, push, merge or rebase unless explicitly requested.
- Do not modify `modules/hdi/**` in this change unless `T8 HDI power gate` is created after replan.
- Do not modify `modules/proto/**` without replan.
- Do not let any worker change shared headers after P1 is frozen.

## Goal Closure

goal_statement:

```text
实现 PCR02 Sensor 统一编排的 camera + mic media pipeline suspend/resume。
休眠时关闭音视频 pipeline，DVR/监控控制面保持空转或降级；唤醒后只根据 active lease 或 record intent 恢复音视频，不无条件启动 camera/mic。
```

completion_claim:

```text
API layer and Sensor orchestration entrypoints are implemented. API object build passes. Sensor object build is blocked
by pre-existing include/proto/header drift outside the media suspend change path; board validation is not executed.
```

required_evidence:

- API video/audio suspend/resume/isRunning compile and behave idempotently.
- DVR media_suspended keeps record intent and does not write empty frames.
- Sensor `suspend_media_pipeline` and `resume_media_pipeline` compile and serialize state.
- Integration smoke passes for video, mic, DVR and remote monitor scenarios.
- 50-cycle suspend/resume stress has no core, watchdog, deadlock or reader leak.
- Board power evidence proves camera/mic current drop after suspend.

claimant: implementation owner
verifier: final integration reviewer
open_items:

- Sensor full object build is blocked by existing missing `modules/common/transport/*.h`, display include drift, and
  display proto enum drift.
- Targeted Sensor object builds are blocked by existing `VSHDIOS_Init(VS_TRUE)` vs root `hdi_os.h` declaration drift and
  the same missing common transport headers.
- Board validation not yet executed.
- HDI power gate necessity unknown until power test.

## Anti-Stall

retry_budget:

- Each stage can retry the same failing verification command at most 2 times.
- If the same command fails twice without root cause, stop and replan.

staleness_threshold:

- If a stage has no new evidence for 2 hours, update this file and re-evaluate assumptions.

heartbeat:

- Update the relevant checkpoint after each stage.
- Record changed files and verification result before moving to the next stage.

stop_condition:

- `pass`: stage verification passed.
- `replan`: contract conflict, scope expansion or repeated verification failure.
- `split`: a stage grows beyond 8 hours or touches new modules.
- `blocked`: missing board, owner decision or contract semantic.
- `abort`: direction proven unsafe or damaging to existing media flow.

## Next Actions

1. Resolve Sensor baseline include/proto/header drift or choose a known-good Sensor build profile.
2. Re-run `rtk make modules/sensor_obj_all -j20`.
3. Run board smoke for idle suspend/resume, active video, active mic, DVR record, and remote monitor.
4. Use power measurement to decide whether `modules/hdi/**` power gate is required.
~~~~

### A8. `docs/plans/media-pipeline-suspend/RISK_LEDGER.md`

- 原始 SHA-256：`e2ffdd894bc7dea5250eff974250f7656a79bdd37730d8e4a8198cc78a24124a`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Media Pipeline Suspend Risk Ledger

| ID | Risk | Severity | Detection | Mitigation | Status |
| --- | --- | --- | --- | --- | --- |
| R1 | DVR reader state becomes stale after video/audio suspend | high | record -> suspend -> resume smoke | Add DVR media_suspended and close/reopen readers | implemented, needs board smoke |
| R2 | Existing `ViInit/AiInit` non-idempotent behavior conflicts with resume | high | repeated resume/resume test | Add dedicated suspend/resume state guards | implemented, needs stress |
| R3 | MP4 segment crosses suspend gap and creates invalid duration | high | inspect recorded file segments | Flush/close current segment at media suspend | implemented, needs file inspection |
| R4 | Resume starts recording from non-key frame | high | verify first frame of resumed segment | Wait for video key frame before opening new segment | implemented by existing key-frame gate, needs smoke |
| R5 | Suspend does not reduce camera/mic power enough | high | board power measurement | Create `T8 HDI power gate` after replan | open |
| R6 | Remote monitor treats media suspended as connection failure | medium | remote monitor smoke | Report degraded media state and keep control plane alive | open |
| R7 | New API headers break existing callers | medium | full API build | Keep existing Init/DeInit semantics and add new APIs only | API build passed |
| R8 | Concurrent suspend/resume causes state race | high | 50-cycle and concurrent smoke | Serialize in Sensor and use idempotent API state | partly implemented, needs stress |
| R9 | Audio player/AO is accidentally affected by AI/mic suspend | medium | audio playback smoke | Limit scope to `VSAPIAUDIO_Ai*` only | implemented, needs playback smoke |
| R10 | Proto expansion becomes necessary | medium | Sensor control integration review | Replan before modifying `modules/proto/**` | open |

## Replan Triggers

- Need to modify `modules/hdi/**`.
- Need to modify `modules/proto/**`.
- Need to change frozen API contract after P1.
- DVR cannot keep record intent while media is suspended.
- Board power does not drop after API suspend.
- Any final gate command fails twice without root cause.
~~~~

### A9. `docs/plans/media-pipeline-suspend/PARALLEL_TASKS.md`

- 原始 SHA-256：`19d26f55024da7586498651e0c944b53421550a792681373a6e1165bed819985`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Parallel Task Packages

## Admission

Parallel Suitability: partial.

Allowed parallel window:

```text
P1 contract frozen -> parallel(P2A-api-video, P2B-api-audio) -> P3
```

Not allowed:

- Do not run P3 before P2A/P2B are done.
- Do not run Sensor implementation before P3 is done.
- Do not let workers modify shared headers, proto, root config or HDI.

## P2A API Video Worker

```md
[parallel-task]
id: P2A-api-video
primary_skill: adk-parallel-agent-governance
goal: Implement `VSAPIVIDEO_ViSuspend`, `VSAPIVIDEO_ViResume`, and `VSAPIVIDEO_ViIsRunning` while preserving existing `ViInit` and `ViDeInit` behavior.
owner: worker-video
scope_write:
  - modules/api/src/api_video_pipe/api_video.c
scope_read:
  - modules/api/include/api_video.h
  - modules/hdi/include/hdi_vi.h
  - modules/hdi/src/hdi_video/hdi_vi.c
must_not_touch:
  - modules/api/include/api_video.h
  - modules/api/include/api_audio.h
  - modules/api/include/api_dvr.h
  - modules/sensor/**
  - modules/hdi/**
  - modules/proto/**
dependencies:
  - P1 contract frozen
verification_commands:
  - rtk make modules/api_obj_all -j20
blocked_conditions:
  - Need to change API header.
  - Need to modify HDI.
  - Existing `ViDeInit` cannot be safely reused for suspend.
expected_output:
  - DONE|BLOCKED|NEEDS_CONTEXT
  - changed_files
  - verified_facts
  - inferences
  - verification
  - risks
handoff_summary_required: yes
```

## P2B API Audio Worker

```md
[parallel-task]
id: P2B-api-audio
primary_skill: adk-parallel-agent-governance
goal: Implement `VSAPIAUDIO_AiSuspend`, `VSAPIAUDIO_AiResume`, and `VSAPIAUDIO_AiIsRunning` while preserving existing `AiInit` and `AiDeInit` behavior.
owner: worker-audio
scope_write:
  - modules/api/src/api_audio_pipe/api_audio.c
scope_read:
  - modules/api/include/api_audio.h
  - modules/hdi/include/hdi_ai.h
  - modules/hdi/src/hdi_audio/hdi_ai.c
must_not_touch:
  - modules/api/include/api_video.h
  - modules/api/include/api_audio.h
  - modules/api/include/api_dvr.h
  - modules/sensor/**
  - modules/hdi/**
  - modules/proto/**
dependencies:
  - P1 contract frozen
verification_commands:
  - rtk make modules/api_obj_all -j20
blocked_conditions:
  - Need to change API header.
  - Need to modify HDI.
  - Existing `AiDeInit` cannot be safely reused for suspend.
expected_output:
  - DONE|BLOCKED|NEEDS_CONTEXT
  - changed_files
  - verified_facts
  - inferences
  - verification
  - risks
handoff_summary_required: yes
```

## P3 DVR Worker

```md
[parallel-task]
id: P3-api-dvr-media-suspend
primary_skill: adk-parallel-agent-governance
goal: Implement DVR media_suspended mode. Keep record intent, pause mux data plane, avoid empty frames, and recover on resume from next key frame.
owner: worker-dvr
scope_write:
  - modules/api/src/api_dvr/api_dvr_record.c
  - modules/api/include/api_dvr.h
scope_read:
  - modules/api/include/api_video.h
  - modules/api/include/api_audio.h
  - modules/api/src/api_video_pipe/api_video.c
  - modules/api/src/api_audio_pipe/api_audio.c
must_not_touch:
  - modules/sensor/**
  - modules/hdi/**
  - modules/proto/**
  - root Makefile
  - build/*.mk
dependencies:
  - P2A-api-video DONE
  - P2B-api-audio DONE
verification_commands:
  - rtk make modules/api_obj_all -j20
blocked_conditions:
  - Need to change video/audio API contract.
  - Need to modify proto.
  - Cannot close current MP4 segment safely on suspend.
expected_output:
  - DONE|BLOCKED|NEEDS_CONTEXT
  - changed_files
  - media_suspended state transitions
  - verification
  - risks
handoff_summary_required: yes
```

## Worker Report Schema

Each worker must report:

```md
status: DONE|BLOCKED|NEEDS_CONTEXT
changed_files:
verified_facts:
inferences:
verification:
risks:
scope_deviation: yes|no
handoff_notes:
```

Any `scope_deviation: yes` stops integration until replan.
~~~~

### A10. `docs/plans/media-pipeline-suspend/resume-prompt.md`

- 原始 SHA-256：`5df6e1f8a555af5caf5ae9e8e33b99d8e613011c06d1b883558eb105a57cd5d1`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Resume Prompt - Media Pipeline Suspend

Continue PCR02 media pipeline suspend/resume implementation from the planning artifacts in:

```text
docs/plans/media-pipeline-suspend/
```

Current status is tracked in `STATE.md`.

Goal:

```text
Implement Sensor-owned camera + mic media pipeline suspend/resume.
Keep DVR/monitor control plane alive or degraded during suspend.
Do not auto-start camera/mic after wake unless active lease or record intent requires it.
```

Execution order:

```text
P0 baseline
P1 API/DVR contract freeze
P2A/P2B parallel video/audio API implementation
P3 DVR media_suspended
P4 Sensor HardwareApi orchestration
P5 SensorEntry state closure
P6 integration validation
```

Hard constraints:

- Use `rtk` for all shell commands.
- Use `apply_patch` for manual edits.
- Do not modify `modules/hdi/**` unless replan creates `T8 HDI power gate`.
- Do not modify `modules/proto/**` unless replan approves contract expansion.
- Do not let parallel workers modify shared headers after P1.
- Do not claim complete without final integration verification.

Next action:

1. Mark `checkpoint-P0-baseline.md` done with current baseline evidence.
2. Start P1 by adding API declarations in `modules/api/include/api_video.h`, `modules/api/include/api_audio.h`, and if needed `modules/api/include/api_dvr.h`.
3. Run `rtk make modules/api_obj_all -j20`.
~~~~

### A11. `docs/plans/media-pipeline-suspend/checkpoint-P0-baseline.md`

- 原始 SHA-256：`b3ebb8f74ecfd254354e3fb698f73e982dc5440ef3a1bf0e61d80b010280acba`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P0 - Baseline

status: pending
owner: main
stage: P0

## Scope

scope_write:

- `docs/plans/media-pipeline-suspend/**`

scope_read:

- `modules/api/**`
- `modules/sensor/**`
- `modules/hdi/**`

## Done Criteria

- Module subrepo status recorded.
- Shared write boundaries frozen.
- Execution order and replan triggers documented.

## Verification Commands

```bash
rtk git -C modules/api status --short --branch --untracked-files=all
rtk git -C modules/sensor status --short --branch --untracked-files=all
rtk git -C modules/hdi status --short --branch --untracked-files=all
```

## Evidence

pending

## Next Action

Move to P1 contract freeze after this checkpoint is marked done.
~~~~

### A12. `docs/plans/media-pipeline-suspend/checkpoint-P1-contract.md`

- 原始 SHA-256：`7be82d38617b6cb09438e8736e6b3b6b9bceddd546e11d2059be89d2fdc41e79`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P1 - API Contract Freeze

status: pending
owner: main/api
stage: P1

## Scope

scope_write:

- `modules/api/include/api_video.h`
- `modules/api/include/api_audio.h`
- `modules/api/include/api_dvr.h`

scope_read:

- `modules/api/src/api_video_pipe/api_video.c`
- `modules/api/src/api_audio_pipe/api_audio.c`
- `modules/api/src/api_dvr/api_dvr_record.c`

must_not_touch:

- `modules/hdi/**`
- `modules/sensor/**`
- `modules/proto/**`
- root config / build config

## Done Criteria

- New video/audio/DVR APIs are declared.
- Idempotency and null-output semantics are documented in comments.
- Existing Init/DeInit API semantics remain intact.
- API object build passes.

## Verification Commands

```bash
rtk make modules/api_obj_all -j20
```

## Evidence

pending

## Next Action

If pass, allow P2A and P2B parallel execution.
~~~~

### A13. `docs/plans/media-pipeline-suspend/checkpoint-P2-api-video-audio.md`

- 原始 SHA-256：`fdc94bf89a355a126ada1aadcd9e98785dfe3ec704b247b7b92129fc09d0c004`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P2 - API Video And Audio

status: pending
owner: worker-video / worker-audio / main integrator
stage: P2

## Parallel Window

Allowed:

- P2A writes only `modules/api/src/api_video_pipe/api_video.c`.
- P2B writes only `modules/api/src/api_audio_pipe/api_audio.c`.

Not allowed:

- Modifying API headers after P1.
- Modifying DVR, Sensor, HDI or proto.

## Done Criteria

- `VSAPIVIDEO_ViSuspend/ViResume/ViIsRunning` implemented and idempotent.
- `VSAPIAUDIO_AiSuspend/AiResume/AiIsRunning` implemented and idempotent.
- Repeated suspend/resume paths do not regress `Init/DeInit`.
- API object build passes after integrating both tasks.

## Verification Commands

```bash
rtk make modules/api_obj_all -j20
```

## Evidence

pending

## Next Action

If both workers report DONE and integrated build passes, move to P3.
~~~~

### A14. `docs/plans/media-pipeline-suspend/checkpoint-P3-dvr.md`

- 原始 SHA-256：`5d870a59616f4c4bc27c48add7348bd412130e9a138cd9dacc5c1d5245908078`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P3 - DVR Media Suspended

status: pending
owner: api-dvr
stage: P3

## Scope

scope_write:

- `modules/api/src/api_dvr/api_dvr_record.c`
- `modules/api/include/api_dvr.h` if public API is required by P1

scope_read:

- `modules/api/include/api_video.h`
- `modules/api/include/api_audio.h`
- `modules/api/src/api_video_pipe/api_video.c`
- `modules/api/src/api_audio_pipe/api_audio.c`

must_not_touch:

- `modules/sensor/**`
- `modules/hdi/**`
- `modules/proto/**`
- root config / build config

## Done Criteria

- DVR can enter `media_suspended` while keeping record intent.
- Mux data plane stops or early returns during media suspend.
- Existing open MP4 segment is flushed/closed on suspend.
- Resume reopens readers if record intent remains.
- New recording segment starts only after next video key frame.
- No empty frame or fake audio is written.

## Verification Commands

```bash
rtk make modules/api_obj_all -j20
```

## Board Smoke

```text
start_record -> media_suspend -> wait 30s -> media_resume -> stop_record
```

## Evidence

pending

## Next Action

If pass, move to Sensor HardwareApi orchestration.
~~~~

### A15. `docs/plans/media-pipeline-suspend/checkpoint-P4-sensor-hardware.md`

- 原始 SHA-256：`9d9f6ffc4289d0c0b7e7a118cbf35beab8cc837bfcaa1cbc71344aab95c29e0b`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P4 - Sensor HardwareApi Orchestration

status: pending
owner: sensor
stage: P4

## Scope

scope_write:

- `modules/sensor/hardware/hardware_api.h`
- `modules/sensor/hardware/hardware_api.cpp`

scope_read:

- `modules/api/include/api_video.h`
- `modules/api/include/api_audio.h`
- `modules/api/include/api_dvr.h`
- `modules/sensor/audio/audio_capture.*`
- `modules/sensor/video/video_capture.*`

must_not_touch:

- `modules/hdi/**`
- `modules/proto/**`
- root config / build config

## Done Criteria

- `suspend_media_pipeline()` serializes media suspend.
- `resume_media_pipeline()` serializes media resume.
- `is_media_pipeline_running()` queries API state.
- Shutdown path keeps existing `deinit_before_shutdown_confirm()` behavior.
- Logs include reason, old state, new state, return code and elapsed time.

## Verification Commands

```bash
rtk make modules/sensor_obj_all -j20
```

## Evidence

pending

## Next Action

Move to SensorEntry state integration.
~~~~

### A16. `docs/plans/media-pipeline-suspend/checkpoint-P5-sensor-entry.md`

- 原始 SHA-256：`8369d1ef5134f35bf6f3d82c4e3779aa645e5a5e3f6204145fc63b04c9ae5918`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P5 - SensorEntry State Closure

status: pending
owner: sensor
stage: P5

## Scope

scope_write:

- `modules/sensor/main/sensor_entry.h`
- `modules/sensor/main/sensor_entry.cpp`

scope_read:

- `modules/sensor/hardware/hardware_api.*`
- `modules/sensor/video/video_capture.*`
- `modules/sensor/audio/audio_capture.*`
- `modules/sensor/dvr/**`

must_not_touch:

- `modules/proto/**` unless replan approves it.
- `modules/hdi/**`
- root config / build config

## Done Criteria

- Sensor owns media pipeline state.
- Suspend/resume are idempotent and serialized.
- New video/mic/QR/AI requests during media suspend have explicit behavior.
- Wake without lease does not auto-start camera/mic.
- Active record intent can trigger media resume when appropriate.

## Verification Commands

```bash
rtk make modules/sensor_obj_all -j20
```

## Evidence

pending

## Next Action

Move to final integration validation.
~~~~

### A17. `docs/plans/media-pipeline-suspend/checkpoint-P6-validation.md`

- 原始 SHA-256：`163a103c44d88fcebfb3c77705e6af476bae2b204125b6aaba5991fc689b6f26`
- 保留方式：以下围栏内逐行保留源文件完整文本；围栏与本报告元数据不属于原文件。

~~~~markdown
# Checkpoint P6 - Integration Validation

status: partial-pass-blocked
owner: main integrator
stage: P6

## Scope

scope_write:

- validation report only, if needed

scope_read:

- all modified files
- build logs
- board logs
- power logs

## Done Criteria

- All required build commands pass or failures are documented with root cause.
- DVR media suspend smoke passes.
- Remote monitor and record control plane behavior is verified.
- 50-cycle suspend/resume stress passes.
- Board power evidence is captured.
- Final gate passes through completion verification.

## Verification Commands

```bash
rtk make modules/api_obj_all -j20
rtk make modules/sensor_obj_all -j20
rtk make modules/hdi_obj_all -j20
rtk python3 tools/diag/checks/check_diag_layer_deps.py
rtk git -C modules/api diff --check
rtk git -C modules/sensor diff --check
rtk git -C modules/hdi diff --check
rtk bash ~/codex/scripts/final-ready.sh
```

## Board Evidence Required

- idle suspend/resume log
- video stream suspend/resume log
- mic capture suspend/resume log
- record suspend/resume file list and segment metadata
- remote monitor + record suspend/resume log
- 50-cycle stress log
- power measurement before/after suspend

## Evidence

- `rtk make modules/api_obj_all -j20`: pass after syncing root `include/api` declarations with module headers.
- `rtk make modules/sensor_obj_all -j20`: blocked before completing modified Sensor files by existing build drift:
  - `modules/sensor/display/display_module.cpp` includes missing `modules/display/display_module.h`.
  - `modules/sensor/audio/audio_frame_hub.h` and DVR replay path include missing
    `modules/common/transport/shm_channel_config.h`.
  - `modules/sensor/display/qr/qr_scene.h` includes missing `modules/common/transport/shm_pub_sub.h`.
  - `modules/sensor/display/display_control.cpp` references missing
    `proto::display_info::RobotEye::EXPRESSION_POWEROFF`.
- Targeted object attempts through `build/build.mk`:
  - `hardware_api.cpp`: blocked by existing `VSHDIOS_Init(VS_TRUE)` call while root `include/hdi/hdi_os.h` declares
    `VSHDIOS_Init(VS_VOID)`.
  - `dvr_service.cpp` and `sensor_module.cpp`: blocked by missing common transport headers above.

Board evidence is not captured in this session.

## Final Gate

Run `adk-verification-before-completion` before claiming complete.
~~~~
