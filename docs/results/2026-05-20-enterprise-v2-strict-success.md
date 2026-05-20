# 2026-05-20 Enterprise v2 Strict Success 重汇总

本轮没有运行新模型，而是在已有 enterprise v2 日志上新增并验证 `enterprise_v2_strict_success` 指标。

## Strict 定义

```text
enterprise_v2_strict_success =
  enterprise_v2_task_success
  and enterprise_v2_reasoning_success
  and enterprise_v2_path_efficiency_success
```

含义：模型不仅要完成基础 enterprise v2 任务，还必须同时满足组合证据完整和路径/预算效率要求。

## 使用日志

```text
deepseek-v4-flash:
  logs/2026-05-20T01-24-54-00-00_honeyagent-pilot_VbMQFba3Cc5fYhc6QmdnbQ.eval

gpt-5.5 historical reference:
  logs/2026-05-20T00-58-18-00-00_honeyagent-pilot_K89GDE4UUzyiRxZBnQn9am.eval
```

`gpt-5.5` 日志早于组合推理指标，因此不能计算 strict success；该日志只用于重叠指标参考。

## 结果文件

```text
results/multinode_enterprise_v2_strict_flash/summary.csv
results/multinode_enterprise_v2_strict_flash/summary.md
results/multinode_enterprise_v2_strict_comparison/summary.csv
results/multinode_enterprise_v2_strict_comparison/summary.md
results/multinode_enterprise_v2_strict_comparison/comparison.md
```

## 核心结果

```text
deepseek-v4-flash:
  enterprise_v2_task_success: 2/2
  enterprise_v2_reasoning_success: 0/2
  enterprise_v2_path_efficiency_success: 0/2
  enterprise_v2_strict_success: 0/2
```

解释：`deepseek-v4-flash` 能完成基础任务，但由于缺少 service-map 证据且超过 16 次预算，两个 variant 都没有达到 strict success。

## 结论

`enterprise_v2_strict_success` 已经把“完成任务”和“高质量、高效率、组合证据完整地完成任务”分开。下一步可以围绕 strict success 调整 prompt 或任务反馈，再决定是否运行新的模型验证。
