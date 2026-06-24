# PCR02 root artifacts boundary 2026-06-20

## 结论

`pcr02-project-root-artifacts` 已完成当前只读复扫。该 source 是根目录 loose artifact/tool/config 混合边界，不是正文迁移源。当前复扫 root `maxdepth=1` loose files 为 16 个；历史 closeout 记录 adjusted root loose view 为 21 个。两者作为“历史证据 + 当前复扫视图”并存，不能用当前复扫覆盖历史事实，也不能据此生成 owner decision。

## 范围

- Source ID: `pcr02-project-root-artifacts`
- Source root: `~/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo`
- 当前复扫口径：根目录 `maxdepth=1` loose files；排除 `.git`、`docs`、`tools`、`knowledge`、`app_product_test`、`scratch`、`.kilo`、`.vscode` 和模块 AGENTS 子树。
- 当前复扫数量：16。
- 历史 closeout 证据：adjusted root loose view 21、broad no-git view 48。

## 分类清单

| 路径或模式 | 分类 | 决策 | 风险 |
|---|---|---|---|
| `bug_report_logger_prune_overrun.md` | `root-markdown-candidate` | `classify-first` | owner 明确 scope/authority 前不能 active。 |
| `prog_ota.log`、`make.log` | `root-log-artifact` | `archive-only-or-artifact-ref` | 日志只能作为证据；抽取诊断结论需 owner review。 |
| `ubi_error_ota.txt`、`ubi_error_product_test.txt` | `root-text-artifact` | `archive-only-or-artifact-ref` | 可能含路径、设备和调试细节；摘要前需 secret scan。 |
| `sensor.patch`、`display.patch` | `root-patch-artifact` | `artifact-ref` | 只允许沉淀 rationale/decision，不复制 patch 全文。 |
| `tag_push.sh`、`make.sh` | `root-script-tool-ref` | `tool-ref-or-artifact-ref` | 不执行，不复制脚本正文。 |
| `png2rgb565array.py` | `root-python-tool-ref` | `tool-ref-or-artifact-ref` | 只登记用途/接口边界，不复制源码正文。 |
| `device_identity_a.bin` | `root-binary-artifact` | `artifact-ref-only` | 禁止展开，禁止进入文本知识层。 |
| `.gitignore`、`.clang-format`、`.clang-format_c`、`Makefile`、`.codex` | `root-config-or-excluded` | `config-ref-or-excluded-with-reason` | 不应混入 root artifact 正文迁移；`.codex` 只能作为配置边界候选。 |

## 控制规则

| 规则 | 状态 |
|---|---|
| `.log/.txt/.patch/.sh/.py/.bin` 不复制正文 | enforced-by-boundary |
| 脚本和 Python 工具不执行 | enforced-by-boundary |
| `.bin` 只能 artifact-ref | enforced-by-boundary |
| 抽取 active fact 或 patch rationale 前必须 owner review | owner-gated |
| 历史 21 与当前 16 的口径差异不自动解释为源事实 | `source-coverage-evidence-drift` / enforced-by-boundary |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| subagent `PCR02-ROOT-ARTIFACTS-BOUNDARY` | 0 | 只读复扫确认 current root loose files=16，并指出历史 closeout=21 的口径差异 | `pcr02-project-root-artifacts` | Subagent evidence | `pcr02-root-artifacts-boundary-20260620` |
| `rtk bash -lc 'base=...; find "$base" -maxdepth 2 ...'` | 0 | 主线程交叉复核 root 候选路径，确认需排除已单独治理子目录 | `pcr02-project-root-artifacts` | Source scan | `pcr02-root-artifacts-boundary-20260620` |

## 未决项

- owner 需要确认 `.md` 是否可进入 copy-first、reference-first 或继续 owner-gated。
- owner 需要确认 patch、log、txt 是否只保留 artifact-ref，或是否需要提取 rationale/诊断摘要。
- 需要后续复核历史 21 个 adjusted candidates 与当前 16 个 root loose files 的口径差异。
