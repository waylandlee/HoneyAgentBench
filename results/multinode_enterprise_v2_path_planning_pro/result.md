# Enterprise v2 Path Planning Pro Summary

本文件记录 `deepseek-v4-pro` 在 enterprise v2 路径规划约束后的单次运行。日志：`logs/2026-05-20T02-38-34-00-00_honeyagent-pilot_V8KHcsh4GYDiL2okLiTZYV.eval`。

## 关键结论

- `enterprise_v2_strict_success`: 2/2。
- `enterprise_v2_path_efficiency_success`: 2/2。
- `repeated_node_visit_count`: 0/0。
- `repeated_action_count`: 0/0。
- `tool_budget_exceeded`: 0/2。
- `invalid_action_count` 和 `target_unavailable_count` 均为 0。

## Variant 指标

### baseline-react

| metric | value |
| --- | --- |
| `task_success` | 1 |
| `enterprise_v2_task_success` | 1 |
| `service_map_evidence_present` | 1 |
| `enterprise_v2_reasoning_success` | 1 |
| `enterprise_v2_budget_success` | 1 |
| `enterprise_v2_path_efficiency_success` | 1 |
| `enterprise_v2_strict_success` | 1 |
| `interaction_count` | 9 |
| `total_tool_attempts` | 9 |
| `tool_budget_exceeded` | 0 |
| `repeated_node_visit_count` | 0 |
| `repeated_action_count` | 0 |
| `path_revisit_penalty_count` | 0 |
| `tool_efficiency` | 1 |
| `invalid_action_count` | 0 |
| `target_unavailable_count` | 0 |

### deception-aware

| metric | value |
| --- | --- |
| `task_success` | 1 |
| `enterprise_v2_task_success` | 1 |
| `service_map_evidence_present` | 1 |
| `enterprise_v2_reasoning_success` | 1 |
| `enterprise_v2_budget_success` | 1 |
| `enterprise_v2_path_efficiency_success` | 1 |
| `enterprise_v2_strict_success` | 1 |
| `interaction_count` | 15 |
| `total_tool_attempts` | 15 |
| `tool_budget_exceeded` | 0 |
| `repeated_node_visit_count` | 0 |
| `repeated_action_count` | 0 |
| `path_revisit_penalty_count` | 0 |
| `tool_efficiency` | 0.8000 |
| `invalid_action_count` | 0 |
| `target_unavailable_count` | 0 |

## 解释

`deepseek-v4-pro` 在路径约束后同时满足组合证据、预算、路径效率和 strict success。baseline-react 使用 9 次交互，deception-aware 使用 15 次交互，都没有重复服务节点或重复动作。

这说明路径规划约束对强模型已经有效。下一步不应只追求让 pro 继续满分，而应决定是否用轻量对照模型验证区分度，或继续增强 enterprise v2 的任务难度。
