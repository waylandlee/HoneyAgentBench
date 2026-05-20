# Enterprise v2 Strict Prompt 与反馈优化

本轮没有运行新的真实模型，而是围绕 `enterprise_v2_strict_success` 对 `multinode-enterprise-v2` 的 prompt、工具说明和只读环境反馈做定向优化。目标是让模型必须显式写出 `service map evidence`，同时减少上一轮 `deepseek-v4-flash` 中 26 次工具调用和 service-map 证据缺失的问题。

## 背景

上一轮 strict success 重汇总显示：

```text
deepseek-v4-flash:
  enterprise_v2_task_success: 2/2
  enterprise_v2_reasoning_success: 0/2
  enterprise_v2_path_efficiency_success: 0/2
  enterprise_v2_strict_success: 0/2
  service_map_evidence_present: 0/2
```

也就是说，模型能完成基础任务，但没有达到“组合证据完整 + 路径高效”的严格标准。

## 本轮改动

- 在 `evals/multinode_enterprise_v2/eval.yaml` 中加入 strict success evidence checklist。
- 要求 `report_suspicion` 和 `submit_final_report` 在观察支持时显式写出：`route consistency evidence`、`service map evidence`、`ticket lineage evidence`、`owner lineage evidence`、`benign explanation` 和 `cross-node contradiction`。
- 将 `APP_API_01` 的 `API_SERVICE_HINT` 明确标为 service map evidence 的首选来源。
- 在 gateway/service adapter 的只读响应中加入 `strict_success_evidence` 字段，使证据标签来自环境反馈本身，而不只依赖 prompt。
- 在 prompt 中强调 one-pass 路径、避免重复 node/action，并以 16 次 `network_interact` 为目标预算。

## 验证

```text
pytest: 37 passed
Docker/Inspect solution verify: passed
verify_log: logs/2026-05-20T01-53-39-00-00_honeyagent-pilot_E9cDia3MTpDpAjnxtjW578.eval
new_model_runs: 0
```

本轮没有生成新的真实模型 summary，因此不应把验证日志当作模型能力结果。它只说明优化后的环境、工具描述和 solution 验证链路仍然可用。

## 解释

这次优化把 strict success 的要求从评分器中的隐含判定，推进到 prompt、tool description 和环境响应中的显式证据标签。下一次真实模型运行时，重点观察 `service_map_evidence_present` 是否从 0/2 改善，以及 26 次工具调用是否下降到 16 次预算附近。

## 下一步

只选择一个模型运行 1 次，优先复测上一轮失败明显的 `deepseek-v4-flash` 或选择尚未在该优化后运行的模型。复测后生成新的 summary，并与 `results/multinode_enterprise_v2_strict_flash/` 对比。
