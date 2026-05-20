# ADR 0002：第一阶段先使用静态蜜罐

## 背景

项目最终希望研究 LLM agent 在 deception environment 中的行为，包括动态响应、一致性陷阱和状态变化。

但第一阶段需要先验证：

- Inspect 是否适合作为底座。
- Docker sandbox 是否稳定。
- restricted tools 是否可用。
- telemetry 和 scorer 是否能正常工作。
- agent 是否能多轮交互并提交报告。

## 决策

第一阶段先实现：

- SSH-like static honeypot
- Web static honeypot

暂不实现复杂 dynamic honeypot。

## 结果

好处：

- 开发速度快。
- 安全性高。
- 可控性强。
- 便于验证 scorer 和 telemetry。

代价：

- 环境较简单。
- 模型容易识别 decoy。
- baseline 和 deception-aware 的差异可能不明显。

## 后续

当静态 MVP 稳定后，再加入：

- dynamic SSH honeypot
- dynamic Web honeypot
- state inconsistency trap
- fake session state
- API schema inconsistency
- prompt injection decoy
