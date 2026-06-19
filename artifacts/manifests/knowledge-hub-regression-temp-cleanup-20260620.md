# Knowledge Hub Regression Temp Cleanup 2026-06-20

## 结论

`tools/knowledge-regression.sh` 已加固低空间和临时目录残留处理：

- 每个 regression fixture 结束后默认立即清理对应 `/tmp/kh-regression-*` 目录。
- 内部异常会被记录为结构化 JSON `fail` 结果，而不是让 final gate 只能看到空 payload 或 traceback。
- 新增低空间预检：`KNOWLEDGE_REGRESSION_MIN_TMP_FREE_BYTES`，默认 `4 MiB`。
- `--keep-temp` 仍可用于人工排查；不传时不保留临时 fixture。

本改动不改变 20 个回归场景的语义，不修改 PCR02 source docs，不关闭 owner gate，不生成 owner decision，不启用自动化，不写 memory。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| RTC-001 | regression 以前到脚本末尾才清理 `/tmp` fixture。 | 根分区接近满载时，多个 fixture 同时存在会放大空间压力。 | 每个 test function 结束后立即清理临时目录。 |
| RTC-002 | `copytree` 或低空间异常会直接打断 Python。 | final gate 只能看到 regression exit 1，payload 缺失或信息不足。 | `run_test()` 捕获异常并写入 JSON failure details。 |
| RTC-003 | 低空间没有预检。 | 失败点随机，维护者难判断是治理失败还是环境失败。 | `copy_repo()` 进入前检查 temp dir free bytes，低于阈值时输出明确异常。 |

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | ---: | --- | --- | --- | --- |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 20 个回归场景通过，`kept_temp=false`。 | `tools/knowledge-regression.sh` | Regression | `knowledge-hub-regression-temp-cleanup-20260620` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 全仓一致性通过，0 errors、0 warnings。 | `tools/knowledge-check.sh` | Knowledge Hub | `knowledge-hub-regression-temp-cleanup-20260620` |
| `rtk bash tools/knowledge-final-gate.sh --json` | 1 expected | 预期仍为 `needs-owner-review`；若 temp 空间低于阈值，regression 会给出结构化 JSON failure。 | `tools/knowledge-final-gate.sh` | Final gate | `knowledge-hub-regression-temp-cleanup-20260620` |

## 维护说明

- 常规验证仍使用 `rtk bash tools/knowledge-regression.sh --json`。
- 若需要保留临时 fixture 排查，显式使用 `--keep-temp`，排查后人工清理 `/tmp/kh-regression-*`。
- 若机器空间长期紧张，应先释放根分区空间；本改动只降低残留和误报成本，不替代磁盘治理。

## 非目标

- 不新增 regression 场景数量。
- 不改变 owner gate open/resolved 判定。
- 不改变 final gate 的终态语义。
- 不清理非本工具创建的临时文件。
