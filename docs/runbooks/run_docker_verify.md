# 运行 Docker 验证

本文档说明如何验证 HoneyAgentBench 的 Docker sandbox 是否正常。

## 1. 准备环境

```bash
cd /home/waylandlee/HoneyAgentBench
conda activate HoneyAgentBench
```

确认 Docker 可用：

```bash
docker --version
docker compose version
```

## 2. 运行单元测试

```bash
pytest -q
```

预期结果：

```text
13 passed
```

## 3. 运行 solution verification

```bash
bash scripts/run_verify.sh
```

该命令会：

- 构建 Docker 镜像
- 启动 SSH/Web sandbox
- 运行 solution verification
- 调用 scorer
- 生成 Inspect `.eval` 日志

## 4. 手动测试 SSH sandbox

```bash
docker compose -p hab_ssh \
  -f evals/ssh_static_honeypot/sandbox_configs/compose.yaml \
  up -d --build

docker compose -p hab_ssh \
  -f evals/ssh_static_honeypot/sandbox_configs/compose.yaml \
  exec -T default python /workspace/client.py ssh SERVICE_INFO

docker compose -p hab_ssh \
  -f evals/ssh_static_honeypot/sandbox_configs/compose.yaml \
  exec -T default python /workspace/client.py ssh READ_BACKUP_NOTE
```

清理：

```bash
docker compose -p hab_ssh \
  -f evals/ssh_static_honeypot/sandbox_configs/compose.yaml \
  down -v
```

## 5. 手动测试 Web sandbox

```bash
docker compose -p hab_web \
  -f evals/web_static_honeypot/sandbox_configs/compose.yaml \
  up -d --build

docker compose -p hab_web \
  -f evals/web_static_honeypot/sandbox_configs/compose.yaml \
  exec -T default python /workspace/client.py web ROOT

docker compose -p hab_web \
  -f evals/web_static_honeypot/sandbox_configs/compose.yaml \
  exec -T default python /workspace/client.py web ADMIN
```

清理：

```bash
docker compose -p hab_web \
  -f evals/web_static_honeypot/sandbox_configs/compose.yaml \
  down -v
```
