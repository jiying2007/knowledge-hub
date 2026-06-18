# PCR02 ASAN Split Targets - 2026-06-18

## 摘要

本 manifest 固化 `runbooks/asan-debug-guide.md` 的拆分边界和后续 owner gate。它不是迁移结果，不复制源 runbook 正文，不创建 active runbook，也不把 PCR02 专属内容提升为团队标准。

## Scope

- Source id: `pcr02-project-docs`
- Source path: `runbooks/asan-debug-guide.md`
- Source root: `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs`
- Source sha256: `d65cf6796eac2c306b6bd0fa101450a1307d5c49ba7b7640e6a329d4263d8e88`
- Source size: `4736`
- Baseline package: `artifacts/manifests/pcr02-owner-review-package-20260618.md`
- Follow-up package: `artifacts/manifests/pcr02-owner-review-follow-up-20260618.md`
- Owner worksheet: `artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md`

## 当前结论

ASAN 源 runbook 继续保持 `split-required`。现阶段允许登记拆分目标和 owner gate，但不得生成 active 正文。

| 目标 | 路径 | 当前状态 | 说明 |
| --- | --- | --- | --- |
| PCR02-local runbook | `domains/projects/pcr02/current/runbooks/asan-debug-guide.md` | `blocked-pending-owner-review` | 仅在 owner 批准后创建，内容只保留 PCR02 构建、部署、路径和验证细节。 |
| Team-level candidate | `domains/embedded/runbooks/asan-debug-guide.md` | `candidate-only-after-separate-team-review` | 仅作为未来候选；必须重写为通用 ASAN 方法，不复制 PCR02 源正文。 |
| Team standard | `domains/embedded/standards/**` | `forbidden` | ASAN 本轮不得进入团队标准目录。 |

## PCR02-local keep

以下内容只能留在 PCR02 项目域：

- `DEBUG=256` / `DEBUG=1` 触发 `DEBUG_ASAN=1` 的项目构建逻辑。
- `TARGET_REL_FOLDER := debug` 的项目输出路径假设。
- `make -j8 DEBUG=256`、`make install`、模块级对象构建等 PCR02 make 命令。
- `prog_pcr02`、`/customer/bin`、`/customer/lib`、`release/bin/prog_pcr02` 等二进制和部署路径。
- `libs/3rdparty/libasan`、`libasan.so.6` 和手动部署 `libasan` 的项目布局。
- 固件容量、strip 行为、动态链接器路径和项目构建产物关系。

## Team-level candidate-only

以下内容可作为未来团队级 ASAN runbook 的候选，但必须重新写成通用方法：

- ASAN 编译标志期望：`-fsanitize=address`、`-fno-omit-frame-pointer`。
- 使用 `readelf -d <target-binary>` 检查 `libasan` 依赖。
- 首发 ASAN 错误优先、BuildID 匹配、栈帧提取、最小调用链和最小修复复现闭环。
- 嵌入式 `ASAN_OPTIONS` 取舍：首错即停、关闭 leak focus、日志落盘、符号化。
- 避免混用 release/debug 包，串口日志可能截断时优先落盘。

## Evidence

本轮只读证据：

| 证据 | 结果 |
| --- | --- |
| source hash | `d65cf6796eac2c306b6bd0fa101450a1307d5c49ba7b7640e6a329d4263d8e88` |
| source size | `4736` |
| `build/build.mk` | `DEBUG_ASAN`、`TARGET_REL_FOLDER`、strip 条件存在 |
| `build/compile.mk` | ASAN 编译 flags 注入存在 |
| Knowledge Hub search | 未发现正式 ASAN registry id 或目标路径占用 |
| registered external source overlap | `embedded-knowledge/docs/runbooks/asan-debug-guide.md` 存在同名 ASAN 文档，但包含 PCR02 路径和命令，不能直接视为团队通用标准 |

## External source overlap

`domains/projects/pcr02/current/runbooks/project-build-and-deploy-guide.md` 中的 `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/asan-debug-guide.md` 指向旧团队知识源，而不是 Knowledge Hub 内的 active ASAN runbook。

只读核对显示旧知识源中存在 `docs/runbooks/asan-debug-guide.md`，但该文档同样包含 `DEBUG=256`、`prog_pcr02`、`/customer/bin`、`release/bin/prog_pcr02` 等 PCR02 相关内容。因此它只能作为外部重叠来源或 team-level rewrite 候选输入，不能作为无需 review 的团队 active 标准。

## Owner gate

Owner 需要补齐：

- `owner_decision`：`split-approved`、`active-project-local`、`reference-only`、`team-candidate-only`、`rejected` 或 `no-migration`。
- `reviewed_by`、`reviewed_at`、`review_after`。
- PCR02 当前适用 branch、SDK 或项目阶段。
- 目标 binary 和实际构建产物路径。
- `DEBUG=256` / `DEBUG=1`、`TARGET_REL_FOLDER := debug`、`prog_pcr02`、`/customer/lib`、`libs/3rdparty/libasan` 是否仍适用。
- 是否需要单独创建团队级 ASAN runbook candidate。
- `project-build-and-deploy-guide.md` 中旧 ASAN 路径引用是否应改为 Knowledge Hub registry 引用或继续指向外部旧知识源。

## Must not

- 不复制完整源 runbook 到团队级路径。
- 不提升到 `domains/embedded/standards`。
- 不把 `DEBUG=256`、`prog_pcr02`、`/customer/*`、`libs/3rdparty/libasan` 当作跨项目默认。
- 不把源文档 frontmatter 的 `status: active` 当作 Knowledge Hub active 状态。
- 不修改源项目 docs。
- 不写入 `~/.codex/memories`。

## 下一步

1. 等待 owner 填写 `pcr02-owner-decision-worksheet-003`。
2. 若 owner 批准 PCR02-local runbook，再按模板创建 `domains/projects/pcr02/current/runbooks/asan-debug-guide.md`，并补 registry 条目。
3. 若 owner 需要团队级 runbook，另起 candidate-only 草案并单独 review，不复用 PCR02 源正文。
4. 处理或确认 `project-build-and-deploy-guide.md` 的旧 ASAN 引用风险和 `embedded-knowledge` 同名文档的重写边界。

## Verification plan

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "ASAN"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 ASAN"
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "libasan"
rtk sha256sum /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/asan-debug-guide.md
rtk wc -c /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs/runbooks/asan-debug-guide.md
```

## Non-actions

- No source project file was edited.
- No ASAN runbook body was copied into `domains/`.
- No team-level ASAN runbook was created.
- No PCR02 project-specific material was promoted to `domains/embedded/standards/`.
- No memory was written.

## Review

- owner：`leiwenjun`
- review_after：`2026-09-17`
- validation_refs：`tools/knowledge-check.sh --dry-run`
