# artifact-provenance-audit

## 触发词

- 制品来源追溯
- artifact manifest
- 模型/固件归档
- 发布包 hash 审计

## 工作流

1. 检查来源字段。
2. 生成并校验 manifest。
3. 扫描敏感信息和大文件边界。
4. 输出入库/归档建议。

## 验证

```bash
rtk bash scripts/check-all.sh
```
