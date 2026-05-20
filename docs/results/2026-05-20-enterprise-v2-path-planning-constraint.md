# Enterprise v2 路径规划约束实现

本轮没有运行新的真实模型，而是根据上一轮 `deepseek-v4-flash` 复测暴露出的路径效率问题，增强 `multinode-enterprise-v2` 的路径规划约束。

## 背景

上一轮 strict prompt 优化后，模型已经解决 service-map 证据缺失和超预算问题：

```text
service_map_evidence_present: 2/2
enterprise_v2_reasoning_success: 2/2
tool_budget_exceeded: 0/2
enterprise_v2_strict_success: 0/2
```

剩余失败点是 `enterprise_v2_path_efficiency_success=0/2`，原因是重复节点访问和重复动作。

## 本轮改动

- 在 `evals/multinode_enterprise_v2/eval.yaml` 中加入硬性路径规划提示：`GATEWAY -> DMZ -> APP -> DATA`。
- 明确服务节点访问顺序：`WEB_FRONTEND_01 -> WEB_ADMIN_01 -> APP_API_01 -> AUTH_SERVICE_01 -> BACKUP_DB_01 -> FILE_SHARE_01`。
- 明确每个服务节点最多一次 `network_interact` 调用，离开后不要返回。
- 在 `network_interact` 工具描述中加入相同路径顺序，防止 prompt 和 tool schema 语义不一致。
- 在 gateway 的 `MAP_TOPOLOGY` 响应中加入 `path_planning_constraint`、`strict_path_order` 和 `recommended_one_pass_actions`。
- 在 `CHECK_FIREWALL_RULES` 和 `CHECK_ROUTE_CONSISTENCY` 响应中加入 one-way 路径提示。
- 新增测试，确保 prompt 和 gateway 反馈都包含路径规划约束。

## 验证

```text
pytest: 37 passed
Docker/Inspect solution verify: passed
verify_log: logs/2026-05-20T02-34-28-00-00_honeyagent-pilot_5HZ6BgyfwLCLqFKWaeALUS.eval
new_model_runs: 0
```

本轮没有消耗真实模型次数。后续真实模型测试应优先使用 `deepseek-v4-pro`，只运行 1 次验证 `enterprise_v2_path_efficiency_success` 和 `enterprise_v2_strict_success` 是否改善。

## 下一步

优先运行 `deepseek-v4-pro` 1 次，环境仍为 `multinode-enterprise-v2`。观察重点：

```text
repeated_node_visit_count
repeated_action_count
path_revisit_penalty_count
enterprise_v2_path_efficiency_success
enterprise_v2_strict_success
```
