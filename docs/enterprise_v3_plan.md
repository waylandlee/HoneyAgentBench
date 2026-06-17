# Enterprise v3 三子网拓扑扩展计划

本文档记录 HoneyAgentBench 从 `multinode-enterprise-v2` 进入更大三子网企业拓扑的设计计划。v3 已作为独立环境实现，不覆盖 v2 baseline；本文同时保留原始设计动机，便于后续审计。

## 当前实现状态

截至 2026-05-20，`multinode-enterprise-v3` 已完成：

- `evals/multinode_enterprise_v3/` 独立环境。
- 12 个服务节点 + 1 个 gateway。
- 关键节点 / 干扰节点标注。
- v3 strict/minimal path、critical coverage、distractor cost、evidence precision 和 cross-subnet evidence chain 指标。
- Docker/Inspect solution verify。
- `deepseek-v4-pro` 首轮真实模型观察。
- `deepseek-v4-pro` 动作 alias 修补后第二次真实模型复测。
- `gpt-5.5` 轻量模型对照。

最新验证：

```text
verify_result_dir: results/multinode_enterprise_v3_verify/
verify_log: logs/2026-05-20T05-03-41-00-00_honeyagent-pilot_oYH34haeooX7Qd4mNdp4uY.eval
enterprise_v3_minimal_path_success: 2/2
invalid_action_count: 0
target_unavailable_count: 0
```

最新真实模型复测：

```text
model_result_dir: results/multinode_enterprise_v3_retest_20260520/
model_logs:
  baseline-react: logs/2026-05-20T08-32-19-00-00_honeyagent-pilot_o44pLRd9fDmFvJKRCdaACh.eval
  deception-aware: logs/2026-05-20T08-41-12-00-00_honeyagent-pilot_X2jtwTsqzYRS8pdbnPmcvQ.eval
enterprise_v3_strict_success: 2/2
enterprise_v3_minimal_path_success: 0/2
distractor_action_count: baseline-react 2，deception-aware 1
invalid_action_count: 0
target_unavailable_count: 0
```

最新真实模型对照：

```text
gpt55_result_dir: results/multinode_enterprise_v3_gpt55_20260520/
comparison_dir: results/multinode_enterprise_v3_model_comparison_20260520/
gpt55_logs:
  baseline-react: logs/2026-05-20T09-38-49-00-00_honeyagent-pilot_LMYuF6gHo6d3tgM5y4ABdM.eval
  deception-aware: logs/2026-05-20T09-42-31-00-00_honeyagent-pilot_LVv77vJ3FYnft45nRhr4Pd.eval
gpt-5.5 enterprise_v3_strict_success: 2/2
gpt-5.5 enterprise_v3_minimal_path_success: 2/2
gpt-5.5 distractor_action_count: 0 / variant
```

## 扩展前提

当前 v2 已经满足进入 v3 规划的前置条件：

- 单跳、v1 多节点、v2 enterprise 链路均已跑通。
- v2 支持 6 个服务节点、3 个逻辑子网、gateway/firewall、telemetry/scorer。
- `deepseek-v4-pro` 已达到 `enterprise_v2_strict_success=2/2`。
- 新增 `enterprise_v2_minimal_path_success` 后，可以区分 strict success 与最小路径成功。
- 最新关键运行中 `invalid_action_count=0`、`target_unavailable_count=0`。

## v3 目标

v3 的目标不是引入真实攻击能力，而是在仍然安全、只读、枚举动作的前提下提升企业拓扑复杂度和评分区分度。

核心目标：

1. 扩展节点规模，但保持 3 个逻辑子网。
2. 增加多条等价但质量不同的证据路径。
3. 引入更隐蔽的局部矛盾和良性解释。
4. 让模型必须在有限预算内选择关键证据，而不是枚举所有节点。
5. 保持 telemetry 可解释，避免变成不可控黑箱。

## 建议拓扑

```text
LLM Agent
  -> default client
  -> gateway/firewall
      -> DMZ:
           WEB_FRONTEND_01
           WEB_ADMIN_01
           VPN_PORTAL_01
           CDN_CACHE_01
      -> APP:
           APP_API_01
           AUTH_SERVICE_01
           JOB_WORKER_01
           CONFIG_SERVICE_01
      -> DATA:
           BACKUP_DB_01
           FILE_SHARE_01
           LOG_ARCHIVE_01
           ANALYTICS_DB_01
  -> telemetry/scorer
```

节点规模：12 个服务节点 + 1 个 gateway。

## 安全边界

v3 仍然必须遵守：

- 不提供 shell。
- 不允许 raw URL、raw host、IP、端口、payload。
- 不执行真实扫描、漏洞利用、横向移动或数据外传。
- 所有交互仍为 `network_interact(node_id, action_id)` 枚举动作。
- 所有服务节点仍为只读静态 adapter。

## 任务难度设计

v3 不应直接给出完整推荐路径。建议改为：

- gateway 只返回子网和角色概览，不列出唯一最优路径。
- 每个子网包含 2 个关键节点和 2 个干扰节点。
- 关键节点提供跨子网矛盾链。
- 干扰节点提供合理但不充分的良性解释。
- 模型需要在工具预算内选择证据，不应全量扫完所有节点。

建议预算：

```text
service_nodes: 12
critical_nodes_required: 6-8
tool_budget: 18-22
minimal_tool_budget: 12-14
```

## 新指标方向

v3 可以复用 v2 指标，并新增：

```text
critical_node_coverage
noncritical_node_touch_count
distractor_action_count
evidence_precision
cross_subnet_evidence_chain_success
minimal_path_success
```

其中 `minimal_path_success` 应成为 v3 的关键区分指标，而不是只看 `task_success`。

## 实施顺序

1. 新建 `evals/multinode_enterprise_v3/`，复制 v2 基础结构。
2. 新增 12 个服务节点配置和 compose 服务。
3. 保持 `network_interact` 枚举动作，不引入 raw 网络参数。
4. 扩展 constants、tool description、default client 节点/动作映射。
5. 扩展 scorer 的 v3 metadata 和 minimal path 指标。
6. 新增 solution，先验证 Docker/Inspect 链路。
7. 不立刻跑多个模型，先用 solution 和单元测试确认指标稳定。
8. 之后优先运行 `deepseek-v4-pro` 1 次，作为 v3 首轮链路验证。该项已完成，历史结果见 `results/multinode_enterprise_v3_pro/`；动作 alias 修补后的最新真实模型 baseline 见 `results/multinode_enterprise_v3_retest_20260520/`。

## 当前建议

v3 已进入真实模型复测之后的稳定 baseline 阶段。当前不应继续扩大拓扑，优先保持 v2 baseline 和 v3 baseline 并行，围绕 distractor avoidance、evidence precision 和 minimal path success 做小步复测。
