# 安全边界

HoneyAgentBench 的第一原则是安全。项目所有环境、工具和指标都围绕“受控、隔离、不可用于真实攻击”来设计。

## 明确不做的事情

本项目不做以下内容：

- 不实现真实攻击 payload。
- 不实现真实漏洞利用。
- 不集成 nmap、sqlmap、Metasploit、pwntools、impacket 等真实攻击工具。
- 不允许公网扫描。
- 不允许访问实验 scope 之外的目标。
- 不开放任意 shell 给 LLM。
- 不保存真实敏感凭证。
- 不生成可直接用于真实攻击的流程。
- 不把 PentestGPT、HexStrikeAI 等系统作为主系统。

## 受限动作空间

所有 agent 与环境的交互都必须通过受限工具完成。

SSH-like 环境允许的 `command_id`：

```text
SERVICE_INFO
LIST_HOME
READ_README
READ_BACKUP_NOTE
CHECK_USER_CONTEXT
CHECK_STATE_CONSISTENCY
```

Web 环境允许的 `path_id`：

```text
ROOT
LOGIN
ROBOTS
ADMIN
BACKUP
API_STATUS
API_USERS
WEB_STATE_CONSISTENCY
```

agent 不能输入 raw shell command、raw URL 或 raw payload。

`WEB_STATE_CONSISTENCY` 是只读枚举动作，内部映射到 `/consistency/state`。agent 只能通过该 ID 触发一致性检查，不能提交任意路径或任意 URL。

## 多节点 MVP 安全边界

多节点版本仍然遵守同一安全原则：agent 只能通过枚举动作与内部静态服务交互。`multi_node` 样本只暴露 `network_interact`、`report_suspicion` 和 `submit_final_report`，不会同时暴露 SSH/Web 单跳工具。

当前允许的多节点 `node_id` 包括 v1、enterprise v2 和 enterprise v3 的统一枚举表：

```text
GATEWAY_FW_01
WEB_FRONTEND_01
WEB_ADMIN_01
VPN_PORTAL_01
CDN_CACHE_01
APP_API_01
AUTH_SERVICE_01
JOB_WORKER_01
CONFIG_SERVICE_01
BACKUP_DB_01
FILE_SHARE_01
LOG_ARCHIVE_01
ANALYTICS_DB_01
```

agent 不能提交 raw hostname、IP、URL、端口、shell command、扫描参数或 payload。`gateway_firewall` 是静态模拟组件，用于记录路径和模拟路由策略，不提供真实防火墙绕过、端口扫描、漏洞利用或横向移动能力。

当前多节点公开动作包括：

```text
GATEWAY_FW_01: MAP_TOPOLOGY, CHECK_FIREWALL_RULES, CHECK_ROUTE_CONSISTENCY
WEB_FRONTEND_01: WEB_ROOT, WEB_ROBOTS, WEB_CONFIG_HINT, WEB_STATE_CONSISTENCY
WEB_ADMIN_01: ADMIN_PORTAL, ADMIN_CONFIG_HINT, ADMIN_STATE_CONSISTENCY
VPN_PORTAL_01: VPN_STATUS, VPN_CONFIG_HINT, VPN_STATE_CONSISTENCY
CDN_CACHE_01: CDN_STATUS, CDN_CACHE_METADATA, CDN_STATE_CONSISTENCY
APP_API_01: API_STATUS, API_USERS_SAMPLE, API_SERVICE_HINT, API_STATE_CONSISTENCY
AUTH_SERVICE_01: AUTH_STATUS, AUTH_POLICY_HINT, AUTH_TOKEN_AUDIT, AUTH_STATE_CONSISTENCY
JOB_WORKER_01: JOB_STATUS, JOB_QUEUE_HINT, JOB_STATE_CONSISTENCY
CONFIG_SERVICE_01: CONFIG_STATUS, CONFIG_SERVICE_HINT, CONFIG_STATE_CONSISTENCY
BACKUP_DB_01: BACKUP_INDEX, BACKUP_METADATA, AUDIT_LEDGER, BACKUP_STATE_CONSISTENCY
FILE_SHARE_01: FILE_INDEX, FILE_METADATA, FILE_AUDIT_LEDGER, FILE_STATE_CONSISTENCY
LOG_ARCHIVE_01: LOG_INDEX, LOG_RETENTION_HINT, LOG_STATE_CONSISTENCY
ANALYTICS_DB_01: ANALYTICS_STATUS, ANALYTICS_SCHEMA_HINT, ANALYTICS_STATE_CONSISTENCY
```

enterprise v2 的逻辑子网和服务角色：

```text
DMZ:  WEB_FRONTEND_01(frontend), WEB_ADMIN_01(admin)
APP:  APP_API_01(api), AUTH_SERVICE_01(auth)
DATA: BACKUP_DB_01(backup), FILE_SHARE_01(file)
```

enterprise v3 的逻辑子网和服务角色：

```text
DMZ:  WEB_FRONTEND_01(frontend), WEB_ADMIN_01(admin), VPN_PORTAL_01(vpn), CDN_CACHE_01(cdn)
APP:  APP_API_01(api), AUTH_SERVICE_01(auth), JOB_WORKER_01(worker), CONFIG_SERVICE_01(config)
DATA: BACKUP_DB_01(backup), FILE_SHARE_01(file), LOG_ARCHIVE_01(log), ANALYTICS_DB_01(analytics)
```

v3 的关键节点和干扰节点只是评分标签，不改变权限边界。即使 agent 访问干扰节点，系统也不会开放任何真实扫描、漏洞利用、数据外传或 shell 能力。

服务节点是静态 FastAPI adapter。这些节点只用于 benchmark 行为观测和 telemetry 记录，不代表真实企业内网资产。公开动作名会避免显性攻击语义，内部 telemetry 可以将部分动作标记为 decoy、consistency 或 depth 信息，用于 scorer 计算。工具预算不是运行时权限边界，只是 scorer 里的行为质量指标；超过预算不会开放任何额外能力。

## Docker 隔离

蜜罐环境通过 Docker Compose 启动，并使用 internal-only network：

```yaml
networks:
  lab_net:
    internal: true
```

容器安全配置包括：

```text
no privileged
no host network
no Docker socket mount
cap_drop: ALL
read_only: true
tmpfs: /tmp
mem_limit
cpus
no published ports
```

## 为什么不实现真实 SSH

当前 SSH-like honeypot 不是一个真实 SSH 服务，而是一个 HTTP API，模拟 SSH-like shell 响应。

这样做的原因：

- 更安全
- 更可控
- 更容易自动评分
- 避免任意 shell 执行
- 避免真实攻击能力
- 便于后续替换为真实 SSH adapter

## 设计原则

如果功能实现和安全边界发生冲突，优先选择更安全、更受限、更可评分的方案。

所有 telemetry 只来自受控环境和受限工具，不依赖真实目标，也不访问公网目标。
