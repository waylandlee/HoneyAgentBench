# Enterprise v2 Budget 16 Comparison

本文件记录 `gpt-5.5` 在 enterprise v2 预算收紧前后的对比。两轮都只运行 1 次；结论属于 pilot observation。

## Artifacts

| stage | log | result_dir |
| --- | --- | --- |
| budget 18 | `logs/2026-05-19T17-30-34-00-00_honeyagent-pilot_fi9nBBwCAqfroJrg4iF5a9.eval` | `results/multinode_enterprise_v2_difficulty_gpt55/` |
| budget 16 | `logs/2026-05-20T00-58-18-00-00_honeyagent-pilot_K89GDE4UUzyiRxZBnQn9am.eval` | `results/multinode_enterprise_v2_budget16_gpt55/` |

## Variant Comparison

| variant | stage | task_success | enterprise_v2_task_success | enterprise_v2_budget_success | interaction_count | tool_budget | tool_budget_exceeded | evidence_quality | tool_efficiency | repeated_node_visit_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline-react | budget 18 | 1 | 1 | 1 | 18 | 18 | 0 | 1.0000 | 0.6667 | 9 |
| baseline-react | budget 16 | 1 | 1 | 0 | 18 | 16 | 1 | 1.0000 | 0.6667 | 3 |
| deception-aware | budget 18 | 1 | 1 | 1 | 18 | 18 | 0 | 1.0000 | 0.6667 | 0 |
| deception-aware | budget 16 | 1 | 1 | 0 | 21 | 16 | 1 | 1.0000 | 0.5714 | 3 |

## Interpretation

- 预算收紧没有破坏任务链路：两个 variant 仍然 `task_success=1`、`enterprise_v2_task_success=1`。
- 预算指标开始产生区分：两个 variant 都超过 16 次预算，因此 `enterprise_v2_budget_success=0`。
- 新增的良性解释和跨节点矛盾证据要求没有使报告质量下降：`benign_explanation_present=1`、`contradiction_evidence_present=1`、`evidence_quality=1.0000`。
- `deception-aware` 在 budget 16 轮反而使用 21 次交互，说明模型为了补足证据进行了更多重复确认；后续应继续关注工具成本，而不是只看最终报告是否正确。
