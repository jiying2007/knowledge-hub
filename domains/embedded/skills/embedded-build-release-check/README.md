# embedded-build-release-check

## 触发词

- 发布前检查
- 构建可复现
- release manifest
- 产物 hash 校验

## 工作流

1. 检查源码和工具链状态。
2. 生成并校验 manifest。
3. 审计二进制依赖。
4. 输出阻塞项和缺失验证。

## 验证

```bash
rtk bash scripts/check-all.sh
```
