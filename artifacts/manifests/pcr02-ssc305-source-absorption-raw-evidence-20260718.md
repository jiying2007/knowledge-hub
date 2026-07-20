---
id: pcr02-ssc305-source-absorption-raw-evidence-20260718
title: PCR02 SSC305 来源吸收冻结原始证据
kind: validation
domain: projects/pcr02-ssc305
path: artifacts/manifests/pcr02-ssc305-source-absorption-raw-evidence-20260718.md
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
- pcr02-ssc305
- embedded-knowledge
- source-absorption
- provenance
related:
- projects/xcrz-sigmastar-demo/validation/2026-07-18-dev-copy-three-dir-absorption-validation.md
- sources/embedded-knowledge/coverage.md
- sources/pcr02-project-knowledge/coverage.md
validation_refs:
- rtk git ls-remote origin refs/heads/main
- rtk git ls-tree -r --name-only origin/main
- rtk git status --short --ignored
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-18
artifact_refs:
- artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl
- /tmp/xcrz-demo-dev-docs-knowledge-scratch-20260718.tar.gz
target_version: cadbf4d6777319c8d43b15f842cbea002cd94cef
test_environment: host-side Git and filesystem audit; no device validation
summary_zh: 核验并吸收 xcrz_sigmastar_demo_dev/knowledge 嵌套仓：178 个非缓存文件由远端 origin/main=cadbf4d 精确保留，7 篇 SSC305 方法提炼为项目候选，13 个 pyc
  与 Git 元数据按治理规则排除。
review_status: manual-entry-pending-review
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: None
evidence_strength: null
evidence_refs:
- ssh://git@192.168.1.4:10022/embedded/knowledge.git
- origin/main=cadbf4d6777319c8d43b15f842cbea002cd94cef
- backup sha256=50c5d651142313dfc659766490867e98a235a1ad9cb71deeea2d4d058372b02c
generated_by_ai: true
ai_role: extracted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-18'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
manual_validation_reason: 7 篇 SSC305 方法中的历史路径、命令和设备步骤尚未逐项在当前 Hub、SDK 和真实板卡复验。
aliases:
- embedded/knowledge SSC305 方法与工具引用吸收验证
---

# embedded/knowledge SSC305 方法与工具引用吸收验证

## 结论

`xcrz_sigmastar_demo_dev/knowledge` 是独立的 `embedded/knowledge` Git 仓副本，不应继续作为项目副本内的第二知识入口。其 178 个非缓存内容文件由远端 `origin/main=cadbf4d6777319c8d43b15f842cbea002cd94cef` 精确保留；Knowledge Hub 通过现有 `domains/embedded/` canonical、source control、本文中文提炼和逐文件 manifest 接管检索与治理。

本轮不把其中声明为 `active` 的旧文档直接提升为 Hub active，也不把项目路径改写成团队标准。7 篇 SSC305 方法是有价值的项目候选，但历史命令仍需按当前 Hub/SDK/设备复验。

## 仓库身份与完整性

| 项目 | 结果 |
| --- | --- |
| remote | `ssh://git@192.168.1.4:10022/embedded/knowledge.git` |
| 本地分支 | `main`，本地 HEAD `b51d477`，相对 `origin/main` behind 1 |
| 远端在线验证 | `rtk git ls-remote origin refs/heads/main` 返回 `cadbf4d6777319c8d43b15f842cbea002cd94cef` |
| 远端树 | `origin/main` 列出 178 个跟踪文件 |
| 本地非缓存文件 | 178 个；已跟踪内容与 `origin/main` 无正文差异；7 个本地显示 untracked 的 SSC305 文档逐一与远端 blob 内容/hash 一致 |
| 可再生缓存 | 13 个 `docs/governance/**/__pycache__/*.pyc`，不在远端树中 |
| Git 元数据 | `knowledge/.git/**` 只作为仓库身份和回滚元数据，不进入 Hub 正文 |
| 回滚 | 三目录 tar 备份包含嵌套 `.git`；另可从精确远端 commit 重建非缓存内容 |

因此删除项目副本内的 `knowledge` 不删除 `embedded/knowledge` 的远端历史，也不会使脚本和文档失去可恢复来源。

## 7 篇 SSC305 方法候选

| `docs/standards/ssc305-feishu-knowledge-map.md` | `27d8fc2648a642196f0de6a85f9f02250869aa98f54c4b08ec59a070b2e81ea1` |
| `docs/runbooks/ssc305-build-burn-upgrade-method.md` | `f857c1897fc3a097e9ec758df6d6f20654d0eb9ad4366018bbc65d0e1771b75e` |
| `docs/runbooks/ssc305-debug-toolchain-method.md` | `a71101b7279695ce48dde9d2a5ebe10fde5e6f91026a543b721eb219bf6d0068` |
| `docs/runbooks/ssc305-diag-regression-method.md` | `64448f3ea1a8537be1ff32df07072162a59964ff10dab407b0411ef195201e24` |
| `docs/runbooks/ssc305-dualos-cm4-low-power-method.md` | `928af6c4bb634cab9b77bd2ac68b7743d72443fc40968eac0608f0ad90100817` |
| `docs/runbooks/ssc305-media-sensor-ai-triage-method.md` | `138a44a2dd34dc895e44ab177b49ec7aa79f846c3e24500abf6d53f87ee975b5` |
| `docs/runbooks/ssc305-sigdoc-lookup-method.md` | `96defdebc763ae4410c5b2b2a8da522cb3ecaad7c62735deb4bb8bb103ae8ffb` |

### 中文提炼

1. **资料/飞书导航**：以 `sigmastar-ssc305-20260516-v2`、115 个主题索引和能力域为检索骨架；引用 sigdoc 只保留 archive/topic/path，不复制官方大段原文。飞书目录是建议结构，不是已发布事实。
2. **构建、烧录与升级**：构建、install、产物核对、同批次镜像、首次启动 smoke、OTA 打包/传输/写入/切换和回滚必须形成闭环；`make all` 成功不等于 release 可交付。
3. **调试工具链**：先固定进程、binary、sysroot 和固件身份，再采 runtime/media/crash bundle；core 必须先做二进制匹配，再 fastpass/deeppass；原始长日志、core 和设备材料不进入 Git。
4. **diag/prog_tool 回归**：`local` 用于工具进程内 runtime，`remote` 走 `cmd_server`；strict 与 env 分离；新增命令需要 metadata、quality、naming、coverage、layer dependency 等静态门禁；没有实际回归不得声称通过。
5. **DualOS/CM4/低功耗**：先明确 Boot、RTOS、CM4、Linux、App 的资源 owner，再拆分启动/休眠/唤醒时序；功耗结论必须绑定测量点、平均/峰值电流、唤醒源、软件和配置版本。
6. **媒体/Sensor/AI**：按 Sensor/电源/I2C → MIPI/VIF → ISP/3A/IQ → SCL/VENC/RGN → IPU/算法 → App 分层定位；AI 结论必须绑定模型、输入、前后处理和单帧耗时，IR/日夜阈值必须实测。
7. **sigdoc 定位**：先判定 BSP、MI、ISP、IPU_Algo、Audio_algo、DualOS、CM4 等能力域，再用主题 ID/路径回到项目源码和设备证据；资料命中不等于项目已实现或功能已验证。

### 使用边界

- 文档中的 `$EMBEDDED_KNOWLEDGE_HOME`、`~/embedded/knowledge` 和 `tools/debug/project-knowledge-debug.sh` 属于旧仓布局，不能直接当作当前 Hub 可执行入口。
- 这些方法当前保持 `reviewing / manual_validation_pending`，只能作为 PCR02/SSC305 项目候选和远端来源提炼。
- 需要跨项目提升时，应逐篇核对 `domains/embedded/` 现有 canonical，避免把 SSC305 项目细节写入团队 standard。
- `ssc305-feishu-knowledge-map.md` 只是信息架构建议；本轮没有调用 connector、上传飞书或改变外部系统。

## 工具与脚本处置

嵌套仓共有 32 个 shell 脚本。Hub 不复制第二套可执行源码，而是把它们绑定到精确 commit；长期方法由 `domains/embedded/runbooks/`、`domains/embedded/skills/` 和工具说明承接。脚本清单如下：

- `scripts/bootstrap-dev-tools.sh`
- `scripts/check-all.sh`
- `scripts/check-artifacts.sh`
- `scripts/check-release-manifest.sh`
- `scripts/check-repository-shape.sh`
- `scripts/check-secrets.sh`
- `scripts/check-shell-style.sh`
- `scripts/check-tools.sh`
- `scripts/generate-release-manifest.sh`
- `scripts/install-codex-skills.sh`
- `scripts/new-doc.sh`
- `scripts/new-skill.sh`
- `scripts/pre-receive-knowledge.sh`
- `scripts/release.sh`
- `scripts/verify-artifact-storage.sh`
- `tools/.codex/skills/voice-audio-normalizer/scripts/normalize_voice_audio.sh`
- `tools/debug/asan-log-symbolize.sh`
- `tools/debug/audit-binary-deps.sh`
- `tools/debug/busybox-kernel-io-watch.sh`
- `tools/debug/collect-ai-vision-bundle.sh`
- `tools/debug/collect-crash-bundle.sh`
- `tools/debug/collect-media-pipeline-snapshot.sh`
- `tools/debug/collect-runtime-baseline.sh`
- `tools/debug/core-env-snapshot.sh`
- `tools/debug/extract-crash-signature.sh`
- `tools/debug/gdb-core-deeppass.sh`
- `tools/debug/gdb-core-fastpass.sh`
- `tools/debug/match-build-artifact.sh`
- `tools/debug/summarize-gdb-fastpass.sh`
- `tools/debug/triage-crash-bundle.sh`
- `tools/debug/verify-core-match.sh`
- `tools/sigmastar/archive_sigdoc_artifact.sh`

这些脚本没有在本轮执行功能回归，因此“远端可恢复”不等于“当前 Hub 环境可直接运行”。如需重新采用，应从 `cadbf4d` 提取到受治理工具源、复核依赖和 secret、运行语法/help/dry-run，再按工具链规范登记。

## 其他 171 个非缓存文件

除 7 篇 SSC305 候选外，其余 171 个非缓存文件按以下类别吸收：

| 类别 | 处置 |
| --- | --- |
| 通用 architecture/runbook/standard/template | 由现有 `domains/embedded/` canonical 或 source provenance 承接，不复制第二份正文 |
| Codex skill 草案 | 只保留远端 commit 与 Hub 已有领域 skill 映射，不自动安装到 `~/.codex/skills` |
| governance/tests | 作为旧知识仓实现资产保留 commit 引用；不复制进 Hub 当前 `tools/` |
| CI、hook、profile、CODEOWNERS/OWNERS | 旧仓自身治理配置，不是 Hub 当前规则；标为 superseded/source-repo-only |
| debug/sigmastar/root scripts | 精确 commit 级 source reference；未做当前 runtime 采用声明 |
| README/AGENTS/CHANGELOG | 旧仓说明与历史 provenance；Hub 根规则和当前 AGENTS 优先 |

逐文件分类见 `artifacts/manifests/xcrz-demo-dev-three-dir-absorption-20260718.jsonl`，不存在“未决定”行。

## 排除项

- 13 个 `.pyc`：generated cache，可由对应 Python 源和解释器重新生成。
- `knowledge/.git/**`：Git object/ref/index/log 元数据；回滚备份中保留，但不进入长期知识层。
- 没有复制 raw logs、core、SDK、release binary 或凭证。
- 没有修改 `embedded/knowledge` 远端、分支或 commit。

## 验证证据

| Command | Exit Code | 结果 | 证据边界 |
| --- | ---: | --- | --- |
| `rtk git ls-remote origin refs/heads/main` | 0 | 在线返回 `cadbf4d6777319c8d43b15f842cbea002cd94cef` | 证明当前远端 branch identity，不证明长期留存 SLA |
| `rtk git ls-tree -r --name-only origin/main` | 0 | 178 个跟踪文件 | 证明 commit 路径集合 |
| `rtk git ls-files --others --exclude-standard` | 0 | 仅 7 篇 SSC305 文档 | 结合逐文件 blob/hash 核验解释本地 behind 状态 |
| `rtk git status --short --ignored` | 0 | 7 篇 untracked、1 个 README modified、13 个 pyc ignored | 与本地 HEAD `b51d477` 的状态，不等于远端缺失 |
| secret filename scan | 0/1 | 无真实 secret；唯一密码规则命中为 `echo "pwd=$(pwd)"` | 规则扫描不能替代人工全面安全审计 |

## 结论与剩余风险

本嵌套仓已达到“可删除本地副本”的知识吸收条件：所有 191 个非 Git文件均有逐文件处置，178 个内容文件有精确远端 commit，7 篇新增方法有中文提炼，13 个缓存有明确排除，Git 元数据有回滚和远端替代来源。

仍保留的风险：

- 7 篇方法没有逐条在当前 SDK、设备和 Hub 路径上验证，不能提升 active。
- 远端在线核验是当前时点证据，不是备份 SLA；本轮 tar 提供本机恢复路径。
- 工具脚本只证明来源可恢复，尚未证明依赖、兼容性或安全性满足当前采用要求。
