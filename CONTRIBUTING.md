# 贡献指南

欢迎通过 Issue 或 Pull Request 增加实验配置、修复报告流程或完善测试。

## 新实验接入要求

1. 优先新增 `experiments/<experiment_id>/config/experiment_spec.v0.2.json`，不要复制通用核心代码。
2. 每个剂量、温度、公式、安全条件和质量阈值必须提供来源状态及证据引用。
3. 缺失内容保持 `missing` 或 `needs_review`，不得用模型猜测补全。
4. 不提交真实学生隐私、未公开研究数据、API Key 或专业软件授权文件。
5. 提交前运行：

```powershell
python scripts/validate_experiment_spec.py <spec.json> --schema schemas/experiment-spec-v0.2.schema.json
python -m unittest discover -s tests -v
```
