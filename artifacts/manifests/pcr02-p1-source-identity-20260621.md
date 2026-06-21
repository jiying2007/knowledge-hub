# PCR02 P1 source identity 2026-06-21

## 结论

本轮为 PCR02 Level 2 中仍缺逐文件身份的 P1 source 补充只读 identity 清单：`pcr02-project-agent-config`、`pcr02-project-tools` 和 `pcr02-project-root-artifacts`。

该清单只登记 `source_path`、`uri`、`size`、`sha256`、分类、引用模式和禁止事项；不复制正文、不执行脚本、不展开制品、不修改源项目、不生成 owner decision、不关闭 owner gate、不写 memory。

## 范围

| Source ID | Source root | 登记文件数 | 边界 |
|---|---|---:|---|
| `pcr02-project-agent-config` | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` | 10 | 只覆盖 `.vscode` 与 `.kilo` 顶层配置、脚本和 package 声明；排除 `.kilo/node_modules/`。 |
| `pcr02-project-tools` | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools` | 18 | 只覆盖 README/AGENTS、debug、diag、CSV、runtime diagnostic、memory report-only automation；排除 `__pycache__` 和 `.pyc`。 |
| `pcr02-project-root-artifacts` | `/home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo` | 16 | 只覆盖当前 root loose files；不递归进入 docs/tools/knowledge/app_product_test/scratch/module agent/config 子树。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| 不复制 source 正文 | enforced-by-identity |
| 不执行源项目脚本、setup、build 或测试 | enforced-by-identity |
| `.kilo/node_modules/`、`__pycache__`、`.pyc` 不进入身份清单 | excluded-generated-or-third-party |
| `.log/.txt/.patch/.bin/.sh/.py` 只做 artifact/tool/reference 身份，不进入 active facts | enforced-by-boundary |
| owner-gated 内容不 active、不关闭 gate | owner-review-required |
| PCR02 project-specific 内容不提升到 `domains/embedded/standards/` | enforced-by-boundary |

## 与既有边界的关系

- `pcr02-tools-boundary-20260620`、`pcr02-agent-config-boundary-20260620` 和 `pcr02-root-artifacts-boundary-20260620` 继续作为分类边界。
- 本清单只补可恢复身份：文件路径、大小、hash、引用模式和 must_not。
- `pcr02-product-test` 已有独立 identity，不在本清单重复登记。
- `pcr02-project-knowledge` 和 `pcr02-project-scratch` 暂不全量 identity；前者文件量大且含 secret-like/config/skill asset，后者价值主要是 archive-only，后续按真实缺口再处理。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `Level 2 source identity review` | 0 | 建议 P1 优先补 agent-config、tools、root-artifacts identity；不建议 product-test 重复或 knowledge 全量身份化 | `pcr02-level2-source-identity-review` | Subagent evidence | `pcr02-p1-source-identity-20260621` |
| `rtk python3 -c '... pathlib/hashlib ...'` | 0 | 只读计算 agent-config 与 root loose files 的 `size` / `sha256`；未读取正文进入 Knowledge Hub | source filesystem metadata | Source identity | `pcr02-p1-source-identity-20260621` |
| `rtk python3 -c '... tools rglob excluding __pycache__ ...'` | 0 | 只读计算 tools 18 个非 pyc 文件的 `size` / `sha256` | source filesystem metadata | Source identity | `pcr02-p1-source-identity-20260621` |

## 下一步

- 若 owner 后续要求处理 `pcr02-project-knowledge`，优先做 secret/config/tool/skill-asset 子集身份，不直接全量复制或全量正文迁移。
- 若 owner 后续要求处理 scratch，只登记 archive-only 身份，不抽取 active facts。
- owner decision 未提供前，final gate 仍应停在 `needs-owner-review`，且唯一 blocker 应为 `owner-gates-open`。
