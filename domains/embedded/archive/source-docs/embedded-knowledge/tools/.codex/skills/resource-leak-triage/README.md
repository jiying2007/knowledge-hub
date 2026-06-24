# resource-leak-triage

## 触发词

- FD 泄漏
- 线程泄漏
- 内存上涨
- buffer 泄漏
- 长跑卡死

## 工作流

1. 采集基线。
2. 分类趋势证据。
3. 收敛资源所有权。
4. 输出长跑验证方式。

## 验证

```bash
rtk bash scripts/check-all.sh
```
