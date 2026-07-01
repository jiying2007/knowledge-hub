# Embedded ASAN Non-PCR02 Evidence Follow-up 2026-06-29

## 结论

本记录登记团队级 ASAN 方法论的后续证据增强项：补充至少一个非 PCR02 项目的 ASAN 实操验证记录。

当前结论：

- `domains/embedded/runbooks/asan-debug-guide.md` 已按 2026-06-29 用户授权提升为 `active`。
- 本 follow-up 不是 validation evidence，不证明已有非 PCR02 项目跑通过 ASAN。
- 2026-06-29 在 Knowledge Hub 本仓检索到的 ASAN 材料主要是团队 runbook、PCR02 project-local runbook、ASAN split / active promotion 证据和通用调试辅助文档；未发现可归档为非 PCR02 项目实操验证的记录。
- 非 PCR02 实操记录是成熟度增强项，不再阻塞当前 active 状态。
- 后续项目实操记录应优先使用 `templates/asan-validation-report.md`，确保构建、运行、符号化、修复复测、资源开销和回退证据一次性收齐。

## Scope

| 字段 | 值 |
| --- | --- |
| target_item | `embedded-asan-debug-guide-20260629` |
| target_path | `domains/embedded/runbooks/asan-debug-guide.md` |
| followup_item | `embedded-asan-non-pcr02-evidence-followup-20260629` |
| owner | `team-core` |
| status | `reviewing` |
| review_after | `2026-09-29` |

## 后续证据验收标准

补充非 PCR02 ASAN 实操记录时，至少需要包含：

1. 项目标识、模块或二进制名称、运行环境和架构。
2. 编译证据：`-fsanitize=address`、保留符号、BuildID 或等价符号匹配依据。
3. 运行证据：`ASAN_OPTIONS`、启动方式、触发路径、ASAN report 或明确的 negative reproduction 结果。
4. 根因与修复证据：首发错误、修复 diff 或处理动作、复测结果。
5. 资源与回退说明：体积、内存、性能、运行库部署差异，以及退出 ASAN 版本的回退路径。
6. 命令级 Evidence Index：命令、退出码、结果摘要、证据路径、层级和关联 artifact。

推荐模板：`templates/asan-validation-report.md`。

## 禁止事项

- 不伪造非 PCR02 项目名称、日志、BuildID、ASAN report 或复测结果。
- 不把 PCR02 项目路径、二进制名、构建变量或动态库布局写成团队默认。
- 不修改源项目、不写 `~/.codex/memories`、不提升到 `domains/embedded/standards/`。
- 不把本 follow-up 当作 owner decision、standards promotion 或 source project write 授权。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk rg -n "ASAN\|AddressSanitizer\|asan\|sanitize\|sanitizer" domains projects notes artifacts registry indexes sources README.md tools -g '!*.git/*'` | 0 | 命中 ASAN 相关材料，但未发现可归档为非 PCR02 项目实操验证的记录；命中范围主要是团队 runbook、PCR02 project-local runbook、ASAN split / active promotion 证据和通用调试辅助文档。 | `domains/embedded/runbooks/asan-debug-guide.md`; `projects/pcr02/current/runbooks/asan-debug-guide.md`; `artifacts/manifests/*asan*` | Audit | `embedded-asan-non-pcr02-evidence-followup-20260629` |
| `rtk test -f templates/asan-validation-report.md` | 0 | 非 PCR02 ASAN 项目实操验证模板已落地，可作为后续证据采集入口。 | `templates/asan-validation-report.md` | Template | `embedded-asan-non-pcr02-evidence-followup-20260629` |

## 下一步建议

1. 选择一个非 PCR02 项目的实际缺陷或可控测试样例，按团队 ASAN runbook 和 `templates/asan-validation-report.md` 生成项目本地验证记录。
2. 将验证记录落到对应 `projects/<project>/archive/debug/` 或项目本地 runbook，不直接改写团队级正文。
3. 验证完成后更新本 follow-up 的 registry 状态，必要时补充到 ASAN active promotion 的 evidence refs。
