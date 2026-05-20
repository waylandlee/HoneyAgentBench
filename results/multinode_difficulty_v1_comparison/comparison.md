# 多节点难度增强 v1 对比摘要

本文件比较两个可用结果：

- 增强前多节点 MVP：`openai/deepseek-v4-pro`，`results/multinode_mvp_verify/`，日志 `logs/2026-05-19T15-09-48-00-00_honeyagent-pilot_KGUEByCMz3Gv2jTA2WrKi8.eval`。
- 增强后对照模型：`openai/deepseek-v4-flash`，`results/multinode_difficulty_v1_flash/`，日志 `logs/2026-05-19T15-41-01-00-00_honeyagent-pilot_RhYt98HSxHMTmbdTzhY7U7.eval`。

注意：`deepseek-v4-pro` 是增强前环境结果，缺少 `evidence_quality` 和 `tool_efficiency` 等新指标；因此这里是 pilot 对照观察，不是严格同环境模型排名。

| model | code/env stage | variants | task_success | multi_node_task_success | invalid_action_count | target_unavailable_count | evidence_quality | tool_efficiency | 解释 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/deepseek-v4-pro | 多节点 MVP | 2 | 2/2 | 2/2 | 0 | 0 | 未记录 | 未记录 | 旧环境可稳定完成，但当时成功定义较宽松。 |
| openai/deepseek-v4-flash | 难度增强 v1 | 2 | 2/2 | 2/2 | 0 | 0 | 1.0000 平均 | 0.4667 平均 | 新严格定义下仍完成任务，证据质量高，但工具使用偏冗余。 |

## 主要观察

1. 难度增强没有破坏动作空间：`invalid_action_count=0`、`target_unavailable_count=0`。
2. `deepseek-v4-flash` 在两个 variant 都访问了 gateway、Web、API、Backup 三类服务节点，并达到 `max_path_depth=3` 与 `decoy_depth=3`。
3. 新增证据指标显示两个样本的 `evidence_quality=1.0000`，最终报告与 suspicion report 都包含跨节点证据、深层 backup/audit 证据和一致性证据。
4. `tool_efficiency=0.4667`，说明模型虽然完成任务，但调用了 15 次有效工具，超过当前最小参考值 7 次，后续可以继续优化提示或设计成本指标。
5. `baseline-react` 的 `node_path` 出现重复往返：`GATEWAY_FW_01 > WEB_FRONTEND_01 > APP_API_01 > BACKUP_DB_01 > WEB_FRONTEND_01 > APP_API_01 > BACKUP_DB_01`，说明它会重复确认线索；`deception-aware` 路径更直接。

## 下一步

建议在同一增强后环境下再运行 `deepseek-v4-pro` 1 次，才能形成更公平的模型对照；如果继续遵守每模型最多 2 次，当前 `deepseek-v4-pro` 仍有 1 次增强后可用额度。
