# 项目 Tools 总入口

本目录只保留当前项目强绑定的工具适配层。通用调试、归档、发布和 Codex skill 统一维护在团队知识库：

```text
~/embedded/knowledge
```

建议设置：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
```

## 目录说明

1. `tools/debug/`
- 当前项目对团队公共 debug 工具的轻量封装。
- 默认使用 `PROJECT_EXE=prog_pcr02`、`PROJECT_APP_DIR=out/arm/app`、`PROJECT_SYSROOT=out/arm/target`。

2. `tools/memory/`
- 记忆整理自动化入口，封装 `~/codex/scripts/curate-memory.sh`。
- 支持自动生成候选、自动打标 `keep/rewrite/drop`、自动产出优化后的 final 草稿。

3. `tools/diag/`
- `diag` 自动化测试入口与 AI 可消费矩阵模板。
- `diag-auto-run.sh` 统一执行 `precheck + strict(local) + env(remote)`，输出 JSON 摘要。
- 默认门禁：`env` 阶段若 `discovered=0` 会标记整体失败，防止 remote 链路失效时“假通过”；可用 `--allow-empty-env-discovery` 放宽。
- `diag-case-matrix.csv` 提供 `modules/hdi`、`modules/api`、`modules/app` 的分层用例矩阵模板。
- precheck 默认包含 `tools/diag/checks/check_diag_layer_deps.py`、`tools/diag/checks/check_diag_naming.py`、`tools/diag/checks/check_diag_command_quality.py`、`tools/diag/checks/check_diag_metadata.py`。
- `diag-interface-coverage.csv` + `check_diag_interface_coverage.py` 用于审计 `hdi_/api_/app_` 模块测试手段覆盖（排除 `ssplat_/ss_`）。
- `check_diag_case_matrix_sync.py` 用于校验 coverage 基线与 case 矩阵一致，防止“有命令但未纳入回归矩阵”。

## 使用示例

```bash
rtk bash tools/debug/project-knowledge-debug.sh env
rtk bash tools/debug/project-knowledge-debug.sh runtime-baseline --duration 30 --out-dir /tmp/pcr02-runtime
rtk bash tools/debug/project-knowledge-debug.sh media-snapshot --dry-run
rtk bash tools/debug/project-knowledge-debug.sh audit-binary --out /tmp/pcr02-binary-deps.txt --allow-missing
rtk bash tools/memory/memory-curator-auto.sh run --project llm_tools --exclude-keywords "crash-debug,core 排障,BusyBox"
rtk bash tools/diag/diag-auto-run.sh --out-dir /tmp/pcr02-diag-auto
rtk bash tools/diag/diag-auto-run.sh --with-build --out-dir /tmp/pcr02-diag-auto-build
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py --strict
```

调用者可以用 `--proc`、`--bin`、`--sysroot` 覆盖默认值；`--name value` 与 `--name=value` 两种形式都会被规范化，未显式传入时才注入 PCR02 默认参数。

## 边界

- 不在本项目复制 `$EMBEDDED_KNOWLEDGE_HOME/tools/debug/*.sh` 的实现。
- 若公共工具需要增强，应修改 `~/embedded/knowledge`，本项目只调整项目默认参数或调用方式。
- wrapper 调用公共脚本前会检查知识库目录和目标脚本，缺失时直接报出明确路径。
- 自动化草稿默认不直接写入正式 memory，建议人工复核后再落库。
