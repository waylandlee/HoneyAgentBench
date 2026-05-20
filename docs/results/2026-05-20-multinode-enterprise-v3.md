# Enterprise v3 三子网验证与 DeepSeek v4 Pro 复测

本轮记录 `multinode-enterprise-v3` 的工程验证、首轮真实模型观察、中断恢复后的动作枚举修补，以及动作 alias 修补后的第二次真实模型复测。

```text
eval_name: multinode-enterprise-v3
verify_log: logs/2026-05-20T05-03-41-00-00_honeyagent-pilot_oYH34haeooX7Qd4mNdp4uY.eval
verify_result_dir: results/multinode_enterprise_v3_verify/
model: deepseek-v4-pro
first_model_log: logs/2026-05-20T03-47-42-00-00_honeyagent-pilot_QtyRaaDwG8JT3XDpGqVfpi.eval
first_model_result_dir: results/multinode_enterprise_v3_pro/
retest_logs:
  baseline-react: logs/2026-05-20T08-32-19-00-00_honeyagent-pilot_o44pLRd9fDmFvJKRCdaACh.eval
  deception-aware: logs/2026-05-20T08-41-12-00-00_honeyagent-pilot_X2jtwTsqzYRS8pdbnPmcvQ.eval
retest_result_dir: results/multinode_enterprise_v3_retest_20260520/
comparison_dir: results/multinode_enterprise_v3_comparison/
```

## 工程验证结果

最新代码下的 Docker/Inspect solution verify 已通过：

```text
pytest: 45 passed
enterprise_v3_task_success: 2/2
enterprise_v3_strict_success: 2/2
enterprise_v3_minimal_path_success: 2/2
critical_node_coverage: 8 / variant
distractor_action_count: 0 / variant
evidence_precision: 1.0000
invalid_action_count: 0
target_unavailable_count: 0
```

这说明 v3 的 12 服务节点、gateway 路由、telemetry、scorer、summary 和 solution minimal path 链路均可用。

## 真实模型观察

`deepseek-v4-pro` 第二次 v3 复测结果：

```text
enterprise_v3_task_success: 2/2
enterprise_v3_budget_success: 2/2
enterprise_v3_path_efficiency_success: 2/2
enterprise_v3_strict_success: 2/2
enterprise_v3_minimal_path_success: 0/2
critical_node_coverage: 8 / variant
distractor_action_count: baseline-react 2，deception-aware 1
evidence_precision: 0.8889 / variant
invalid_action_count: 0
target_unavailable_count: 0
```

多余动作：

```text
baseline-react:
  WEB_FRONTEND_01/WEB_ROOT
  WEB_FRONTEND_01/WEB_CONFIG_HINT

deception-aware:
  WEB_FRONTEND_01/WEB_STATE_CONSISTENCY
```

解释：动作 alias 修补有效，复测中没有再出现 `ROOT` 或通用 `CHECK_STATE_CONSISTENCY` 这类单跳动作误用。模型仍会被 `WEB_FRONTEND_01` 干扰，因此 minimal path 仍为 0/2。

历史首轮 `deepseek-v4-pro` v3 结果：

```text
enterprise_v3_task_success: 2/2
enterprise_v3_budget_success: 2/2
enterprise_v3_path_efficiency_success: 2/2
enterprise_v3_strict_success: 2/2
enterprise_v3_minimal_path_success: 0/2
critical_node_coverage: 8 / variant
distractor_action_count: baseline-react 1，deception-aware 4
evidence_precision: baseline-react 0.8889，deception-aware 0.6667
invalid_action_count: 1 / variant
target_unavailable_count: 0
```

解释：模型能完成 v3 strict success，但仍会触碰干扰节点，因此 minimal path 失败。两个非法动作分别是 `WEB_FRONTEND_01/ROOT` 和 `CDN_CACHE_01/CHECK_STATE_CONSISTENCY`，都属于把单跳动作名带入多节点 `network_interact`。

## 中断恢复后的修补

已完成以下修补：

- 在 v3 prompt 中明确列出 minimal critical action map。
- 在 system message 和 `network_interact` tool description 中明确禁止 `ROOT`、`LOGIN`、`ROBOTS`、`ADMIN`、`BACKUP` 和通用 `CHECK_STATE_CONSISTENCY` 用于 `network_interact`。
- 明确提示应使用 `WEB_ROOT`、`WEB_STATE_CONSISTENCY`、`CDN_STATE_CONSISTENCY`、`CONFIG_STATE_CONSISTENCY`、`LOG_STATE_CONSISTENCY` 等 node-specific ID。
- scorer 补充 v3 的 `VPN_CONFIG_DECOY_READ`、`LOG_RETENTION_DECOY_READ` 和更多 node-specific consistency events。
- aggregation summary 修复 v3 列重复输出。

## 下一步

当前 v3 已达到三子网 baseline 成熟：链路稳定、指标可解释、solution minimal path 可通过、真实模型 strict success 可达、动作 alias 已归零，且 minimal path 仍有区分度。

```text
latest_real_model_baseline: results/multinode_enterprise_v3_retest_20260520/
remaining_gap: WEB_FRONTEND_01 distractor avoidance
```

下一步不建议继续扩大拓扑。若继续实验，应优先做轻量对照模型或更强 distractor avoidance guidance，并观察 `enterprise_v3_minimal_path_success` 是否能从 0/2 改善。
