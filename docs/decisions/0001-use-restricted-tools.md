# ADR 0001：使用受限工具和枚举动作空间

## 背景

HoneyAgentBench 的目标是研究 LLM agent 在 honeypot/deception 环境中的行为，而不是构建真实攻击工具。

如果允许模型输入 raw shell command、raw URL 或 raw payload，项目会变得不可控，也可能产生真实攻击能力。

## 决策

所有 agent 动作都必须通过受限工具完成：

```text
ssh_interact(command_id)
web_request(path_id)
report_suspicion(...)
submit_final_report(...)
```

其中 `command_id` 和 `path_id` 必须来自枚举集合。

## 结果

好处：

- 安全边界清晰。
- 行为可评分。
- telemetry 易于记录。
- 不会暴露任意 shell 或公网扫描能力。

代价：

- 环境真实性低于真实系统。
- agent 动作空间较窄。
- 后续需要设计更多安全的受限动作来提高 benchmark 难度。
