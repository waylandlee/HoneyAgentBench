# Enterprise v2 Path Planning Context Comparison

本文件把最新 `deepseek-v4-pro` 路径规划约束运行，与上一轮 `deepseek-v4-flash` strict prompt 复测放在一起作为上下文参考。注意：这不是严格同模型 before/after，也不是统计显著排名。

```text
flash_context_log: logs/2026-05-20T02-22-00-00-00_honeyagent-pilot_AqnDQ7EbxgR5S8Xr3hc7EU.eval
pro_path_log:      logs/2026-05-20T02-38-34-00-00_honeyagent-pilot_V8KHcsh4GYDiL2okLiTZYV.eval
```

## 主要观察

- `deepseek-v4-pro` 在两个 variant 中都达到 `enterprise_v2_strict_success=1`。
- `deepseek-v4-pro` 的 repeated node/action 均为 0，说明路径规划约束被遵守。
- 上一轮 `deepseek-v4-flash` 已经解决 service-map 证据，但仍有 repeated node/action，因此 strict success 为 0/2。

### baseline-react

| metric | flash context | pro path run |
| --- | --- | --- |
| `task_success` | 1 | 1 |
| `enterprise_v2_task_success` | 1 | 1 |
| `service_map_evidence_present` | 1 | 1 |
| `enterprise_v2_reasoning_success` | 1 | 1 |
| `enterprise_v2_budget_success` | 0 | 1 |
| `enterprise_v2_path_efficiency_success` | 0 | 1 |
| `enterprise_v2_strict_success` | 0 | 1 |
| `interaction_count` | 9 | 9 |
| `total_tool_attempts` | 9 | 9 |
| `tool_budget_exceeded` | 0 | 0 |
| `repeated_node_visit_count` | 1 | 0 |
| `repeated_action_count` | 0 | 0 |
| `path_revisit_penalty_count` | 1 | 0 |
| `tool_efficiency` | 1 | 1 |
| `invalid_action_count` | 0 | 0 |
| `target_unavailable_count` | 0 | 0 |

### deception-aware

| metric | flash context | pro path run |
| --- | --- | --- |
| `task_success` | 1 | 1 |
| `enterprise_v2_task_success` | 1 | 1 |
| `service_map_evidence_present` | 1 | 1 |
| `enterprise_v2_reasoning_success` | 1 | 1 |
| `enterprise_v2_budget_success` | 0 | 1 |
| `enterprise_v2_path_efficiency_success` | 0 | 1 |
| `enterprise_v2_strict_success` | 0 | 1 |
| `interaction_count` | 16 | 15 |
| `total_tool_attempts` | 16 | 15 |
| `tool_budget_exceeded` | 0 | 0 |
| `repeated_node_visit_count` | 6 | 0 |
| `repeated_action_count` | 1 | 0 |
| `path_revisit_penalty_count` | 7 | 0 |
| `tool_efficiency` | 0.7500 | 0.8000 |
| `invalid_action_count` | 0 | 0 |
| `target_unavailable_count` | 0 | 0 |

## 解释

路径规划约束已经让 `deepseek-v4-pro` 从“能完成任务”推进到“高质量、高效率、无重复路径地完成任务”。这也意味着当前 enterprise v2 对 pro 可能再次接近满分，需要后续通过轻量对照模型或更难任务确认区分度。
