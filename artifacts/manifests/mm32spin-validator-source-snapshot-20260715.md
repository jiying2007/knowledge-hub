# MM32SPIN Validator 源码快照清单（2026-07-15）

## 结论

本清单为处于 unborn Git 状态、没有 `HEAD` 的 `mm32spin-validator` 工作区建立一次 hash-bound 来源快照。它固定 2026-07-15 扫描到的 46 个受控范围文件，供本地发布 provenance 审计和后续差异核对使用；它不是 Git commit、release tag、源码归档包或可复现构建声明。

机器可读正文位于 `artifacts/manifests/mm32spin-validator-source-snapshot-20260715.jsonl`：

- Snapshot ID：`mm32spin-validator-source-snapshot-20260715`。
- 记录数：47，其中 1 条快照元数据、46 条文件记录。
- SHA256：`4cc8860e18ae19c442ff937f933efd24313868ddec6f226d53f578137b644cf6`。
- 来源状态：`unborn-git-repository-no-HEAD`。
- 清单范围：项目可枚举文件；按项目 `.gitignore` 排除被忽略的生成目录。

## 可用范围

- 按相对路径、文件大小和 SHA256 核对某个文件是否与本次快照一致。
- 为 `mm32spin-validator v0.1.0` 的来源缺口提供“审计时可见内容”证据。
- 在未来建立正式 commit/tag 后，作为一次性差异基线使用。

## 不可推出的结论

- 不能证明 46 个文件已提交、已 review、已发布或可从远端恢复。
- 不能证明发布制品由这些文件可复现构建，也不能替代 build、artifact、device、release 或 rollback evidence。
- 不能把快照生成时的文件状态自动视为当前状态；需要时必须重新捕获并比较新清单。
- 不能关闭 owner gate，不能将 evidence contract 提升为 `ready`，也不授权写入源项目。

## 后续关闭条件

要关闭来源 provenance 缺口，至少需要真实的源项目 commit、与发布版本绑定的 tag 或等价不可变引用，并补充可复现构建、制品校验、留存位置和回滚验证。任何缺失项都必须保留为明确的 `pending`，不得以推断补齐。
