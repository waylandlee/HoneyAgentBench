# 运行 DeepSeek 模型

## 默认模型优先级

后续 HoneyAgentBench 真实模型测试优先使用 `deepseek-v4-pro`。`deepseek-v4-flash` 主要作为轻量对照模型使用。

本文档说明如何使用 DeepSeek API 运行 HoneyAgentBench MVP。

## 1. 准备环境

进入项目目录：

```bash
cd /home/waylandlee/HoneyAgentBench
conda activate HoneyAgentBench
```

确认 `.env` 中存在：

```text
DEEPSEEK_API_KEY="your-key"
```

不要把真实 API key 写入 `.env.example` 或任何 Git 跟踪文件。

## 2. 测试 DeepSeek API

可以使用最小请求测试：

```bash
set -a
source .env
set +a

curl https://api.deepseek.com/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  -d '{
    "model": "deepseek-v4-pro",
    "messages": [{"role": "user", "content": "Reply with exactly: ok"}],
    "max_tokens": 64,
    "temperature": 0
  }'
```

## 3. 运行完整 MVP

```bash
bash scripts/run_deepseek.sh deepseek-v4-pro
```

脚本会自动：

- 加载 `.env`
- 设置 `OPENAI_API_KEY=${DEEPSEEK_API_KEY}`
- 使用 DeepSeek base URL
- 调用 Inspect
- 启动 Docker sandbox
- 生成 `.eval` 日志

只运行某个 eval，例如当前三子网 v3：

```bash
bash scripts/run_deepseek.sh deepseek-v4-pro multinode-enterprise-v3
```

只运行某个 eval 的单个 variant，例如 v3 的 baseline：

```bash
bash scripts/run_deepseek.sh deepseek-v4-pro multinode-enterprise-v3 baseline-react
```

第三个参数会传给 Inspect 的 `variant_names`，适合在整组真实模型运行卡住时逐个 variant 复测。

## 4. 聚合结果

运行：

```bash
python scripts/aggregate_results.py logs/*.eval
```

生成本轮 CSV 和 Markdown summary：

```bash
python scripts/aggregate_results.py --out-dir results/pilot_latest logs/具体文件名.eval
```

只看某一次运行：

```bash
python scripts/aggregate_results.py logs/具体文件名.eval
```

## 5. 重复运行和模型组

单个模型重复运行：

```bash
bash scripts/run_repeated.sh deepseek-v4-pro 1
```

`run_repeated.sh` 会拒绝 `runs>2`，避免超过每个模型最多两次的实验约束。

运行默认对照模型组：

```bash
bash scripts/run_model_suite.sh
```

默认模型组为：

```text
deepseek-v4-pro
deepseek-v4-flash
```

每个模型默认运行 1 次，并在 `results/pilot_latest/` 下生成：

```text
run_logs.tsv
summary.csv
summary.md
```

## 6. 当前有效结果

最新有效 DeepSeek v4 Pro 三子网 v3 复测日志：

```text
logs/2026-05-20T08-32-19-00-00_honeyagent-pilot_o44pLRd9fDmFvJKRCdaACh.eval
logs/2026-05-20T08-41-12-00-00_honeyagent-pilot_X2jtwTsqzYRS8pdbnPmcvQ.eval
```

聚合结果位于 `results/multinode_enterprise_v3_retest_20260520/`。该次复测中两个 v3 variants 均 `task_success=1`、`enterprise_v3_strict_success=1`、`invalid_action_count=0`。
