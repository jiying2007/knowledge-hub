# asan-crash-triage

用于 ASAN 崩溃日志的快速离线分诊，强调低 token 输出。

## 重点能力

1. 识别 ASAN 错误类型
2. 提取首个关键栈帧
3. 地址离线符号化
4. 输出最小修复与验证动作

## 配套脚本

- `tools/debug/asan-log-symbolize.sh`
