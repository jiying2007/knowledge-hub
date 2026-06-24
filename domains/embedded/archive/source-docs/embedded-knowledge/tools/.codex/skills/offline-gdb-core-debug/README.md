# offline-gdb-core-debug

跨模块通用的离线 core 调试技能，目标是低 token 输出可执行结论。

## 能力

- 快速识别崩溃线程、信号、函数与源码行号
- 结构化提炼 locals/registers/backtrace 证据
- 给出最小修复与验证命令

## 用法

1. 准备二进制与 core：
   - `out/arm/app/prog_*.debug.full`
   - `out/arm/app/core-*`
2. 先执行 Fast Pass（限制回溯深度）。
3. 证据不足再升级 Deep Pass。

## 设计目标

- 高质量：结论有证据锚点
- 高效率：默认最小信息集
- 省 token：禁止无界回溯输出
