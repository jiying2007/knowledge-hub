# GD32L235 Firmware

- 项目 ID：`gd32l235`
- 所属组：`mcu`
- 事实边界：以 `registry/repositories.json` 中 `repo_id=gd32l235` 的 Git remote key 为准。
- 当前知识：`projects/gd32l235/current/`
- 当前低功耗协同契约候选：[GD32L235 与 PCR02 SoC 低功耗协同当前契约候选](current/soc-low-power-contract.md)（`reviewing`，不替代源码）
- 决策：`projects/gd32l235/decisions/`
- 验证：`projects/gd32l235/validation/`
- 归档：`projects/gd32l235/archive/`

## 文件命名约定

- `current/` 使用稳定语义名称，不添加日期，例如 `soc-low-power-contract.md`。
- `archive/` 下的长期 Markdown 使用 `archive/<分类>/YYYY-MM-DD-<ascii-kebab-topic>.md`，日期表示事件、决策、会话或捕获日期。
- registry `id` 可继续使用紧凑的 `YYYYMMDD` 后缀；文件路径与 `id` 无需采用相同日期分隔形式。
- `.txt` 派生全文、二进制和外部资料引用按 artifact/source 规则命名，不因本约定改写原始身份。
- 重命名归档时必须同步正文 `path`、registry、validation/evidence refs、核心索引和既有 capture 事件的 evidence path；不得只移动文件。

<!-- knowledge-hub-project-readiness:start -->
## 成熟度工作台

以下入口是单一 `reviewing` evidence contract 与统一 dashboard；不代表 owner 签收或发布就绪。

- [项目 evidence contract](validation/project-readiness.md)
- [统一 readiness dashboard](../../indexes/project-readiness.md)
<!-- knowledge-hub-project-readiness:end -->
