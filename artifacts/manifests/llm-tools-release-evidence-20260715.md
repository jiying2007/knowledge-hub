# LLM Tools 本地发布证据清单（2026-07-15）

## 结论

本清单为 `ota-packager`、`sigmastar-flasher` 和 `mm32spin-validator` 的本地发布目录建立可检索的证据入口。2026-07-15 的只读审计确认，三个目录内的制品校验和均与各自发布记录一致；该结果只证明本地目录完整性，不证明远端留存、现场采用、可回滚性或 release gate 已关闭。

机器可读正文位于 `artifacts/manifests/llm-tools-release-evidence-20260715.jsonl`：

- 行数：3。
- SHA256：`a6a01ca178b825ad81aa20808474aee2f926634ada49903e0f0bc5444f1803a9`。
- 检查日期：2026-07-15。

## 证据摘要

| 工具 | 版本 | 本地制品 | 校验结果 | 来源边界 | 仍缺证据 |
| --- | --- | ---: | --- | --- | --- |
| `ota-packager` | `1.0.0` | 7 | 7/7 通过 | 发布记录中的 source commit 前缀与当前精确 commit 对齐；`v1.0.0` 指向父提交，记录另含后续 Linux CLI 提交 | 远端留存、回滚演练、真实采用 |
| `sigmastar-flasher` | `1.0.0` | 10 | 10/10 通过 | 发布记录中的 source commit 前缀与当前精确 commit 对齐；`v1.0.0` 指向父提交，记录另含后续 Linux CLI 提交 | 远端留存、回滚演练、真实采用 |
| `mm32spin-validator` | `0.1.0` | 4 | 4/4 通过 | 发布时子项目无 commit/tag，当前只建立 46 文件 hash-bound snapshot，无法证明发布制品与当前源码等价 | 可提交来源、tag、远端留存、回滚演练、真实采用 |

## 使用边界

- JSONL 是逐工具证据正文；本 Markdown 仅提供中文摘要和治理边界，不复制制品内容。
- `checksum_status=pass` 只表示本地文件与已记录 checksum 一致，不等价于签名可信、安装可用或生产发布成功。
- `artifact_status` 不关闭 owner、validation、release、rollback 或 adoption gate。
- `mm32spin-validator` 的来源缺口必须以真实 commit/tag 或可验证发布 provenance 补齐，不能由本快照或 owner 决策替代。
- 未验证项继续保持 `pending`，不得据此提升任何 evidence contract 为 `ready` 或项目状态为 `active`。
