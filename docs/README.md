# HoneyAgentBench 文档索引

本目录用于管理 HoneyAgentBench 的项目说明、设计原则、实验计划、运行手册和实验结果。

## 文档列表

- [项目概览](project_overview.md)：说明项目要解决什么问题，以及当前 MVP 的范围。
- [安全边界](safety_boundary.md)：说明本项目明确不做什么，以及为什么必须使用受限动作空间。
- [系统架构](architecture.md)：说明 Inspect、restricted tools、Docker sandbox、honeypot、telemetry 和 scorer 的关系。
- [环境拓扑](topology.md)：说明 SSH/Web 单跳、多节点 MVP、enterprise v2 和 enterprise v3 sandbox 拓扑、容器关系、网络隔离和 telemetry 流向。
- [指标定义](metric_definitions.md)：解释当前 scorer 输出的各项指标。
- [实验计划](experiment_plan.md)：说明单跳实验结论、enterprise v2/v3 验证结果，以及后续区分度增强方向。
- [Enterprise v3 三子网拓扑扩展计划](enterprise_v3_plan.md)：说明从 v2 扩展到更大三子网企业拓扑的设计方案；当前 v3 已落地，作为设计背景保留。
- [实验记录](experiment_log.md)：持续记录每次实验的日志路径、结果目录、核心指标、解释和文档同步情况。
- [当前 Pilot 结果](pilot_results.md)：记录目前已经完成的 DeepSeek MVP、工具裁剪、单跳优化、多节点增强、enterprise v2 和 enterprise v3 结果。
- [Pilot 对照报告](pilot_report.md)：记录 Web consistency、细粒度指标、DeepSeek 对照、单跳优化、多节点 v2 复测和 v3 真实模型复测。
- [模型配置](model_configs.md)：记录模型供应商、模型名和运行方式。这里不保存 API key。
- [开发日志](development_log.md)：记录开发过程中的关键进展、问题和修复。

## 运行手册

- [运行 DeepSeek 模型](runbooks/run_deepseek.md)
- [运行 Docker 验证](runbooks/run_docker_verify.md)

## 设计决策

- [ADR 0001：使用受限工具和枚举动作空间](decisions/0001-use-restricted-tools.md)
- [ADR 0002：第一阶段先使用静态蜜罐](decisions/0002-use-static-honeypot-first.md)

## 实验结果

- [2026-05-19 DeepSeek v4 Pro 单跳实验](results/2026-05-19-deepseek-v4-pro.md)
- [2026-05-19 多节点 MVP 实验](results/2026-05-19-multinode-mvp.md)
- [2026-05-19 多节点难度增强 v1 实验](results/2026-05-19-multinode-difficulty-v1.md)
- [2026-05-20 Enterprise v2 多节点实验](results/2026-05-20-multinode-enterprise-v2.md)
- [2026-05-20 Enterprise v2 难度增强实验](results/2026-05-20-multinode-enterprise-v2-difficulty.md)
- [2026-05-20 Enterprise v2 Budget 16 实验](results/2026-05-20-multinode-enterprise-v2-budget16.md)
- [2026-05-20 Enterprise v2 组合推理增强实验](results/2026-05-20-multinode-enterprise-v2-reasoning-flash.md)
- [2026-05-20 Enterprise v2 Strict Success 重汇总](results/2026-05-20-enterprise-v2-strict-success.md)
- [2026-05-20 Enterprise v2 Strict Prompt 与反馈优化](results/2026-05-20-enterprise-v2-strict-prompt-optimization.md)
- [2026-05-20 Enterprise v2 Strict Prompt 优化后 Flash 复测](results/2026-05-20-enterprise-v2-strict-prompt-flash.md)
- [2026-05-20 Enterprise v2 路径规划约束实现](results/2026-05-20-enterprise-v2-path-planning-constraint.md)
- [2026-05-20 Enterprise v2 路径规划约束后 DeepSeek v4 Pro 复测](results/2026-05-20-enterprise-v2-path-planning-pro.md)
- [2026-05-20 Enterprise v2 Minimal Path 指标增强](results/2026-05-20-enterprise-v2-minimal-path.md)
- [2026-05-20 Enterprise v3 三子网验证与 DeepSeek v4 Pro 复测](results/2026-05-20-multinode-enterprise-v3.md)
