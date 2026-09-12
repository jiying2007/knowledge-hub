# Legacy debt measurement correction — 2026-09-12

## 结论

本轮不声明 legacy debt 已从 11 降低，也不修改 11 / 315 基线。

审查期间一度怀疑 `legacy_attention_count` 会排除配置了 `legacy_module_line_caps` 的模块。fresh hosted pytest 证明该假设不成立：现有 `if / elif` 逻辑中，处于 legacy cap 内、但仍超过通用 800 行预算的 tracked module 仍会进入 `legacy_attention`。因此此前 11 个 oversized legacy module 的基线没有因 legacy cap 被静默低报。

本轮保留的改进是新增显式 `oversized_module_count` / `oversized_modules`：它直接表达所有超过通用 module-size budget 的 Python 模块总量，避免 Terminal Closure 依赖一个名称更偏“attention”的历史字段。`legacy_attention_count` 保持原语义，作为 report-only legacy attention 视图。

## 证据原则

- `registry/legacy-debt-burndown.json` 的 baseline 仍为 11 oversized modules / 315 legacy artifact references。
- Terminal Closure 使用显式 `oversized_module_count` 执行 decrease-only 上界检查。
- legacy cap 只限制历史模块继续增长，不会把 oversized module 从总量中移除。
- 不通过提高 800 行预算、扩大 legacy cap、删除 provenance 或修改计数口径制造下降。
- 真正的 11 → 10 必须来自后续独立结构拆分，并通过 fresh full Engineering / regression / compatibility 证据证明。

## 纠错记录

旧假设：带 legacy cap 的 oversized 模块不进入 `legacy_attention_count`。

Hosted CI 反例：构造一个 cap=20、实际 10 行、通用 module budget=5 的 tracked fixture；它仍进入 `legacy_attention`。因此该旧假设被撤回，不作为后续设计依据。

这份记录只解释计量语义修正，不是第二套状态权威。机器权威仍是 `registry/engineering-budgets.json`、`registry/legacy-debt-burndown.json` 与 live complexity report。
