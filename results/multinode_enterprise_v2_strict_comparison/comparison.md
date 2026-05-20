# Enterprise v2 Strict Success Re-summary

本文件在不重新运行模型的前提下，基于已有 `.eval` 日志重新生成 summary，并加入新的 `enterprise_v2_strict_success` 指标。

## Strict Definition

```text
enterprise_v2_strict_success =
  enterprise_v2_task_success
  and enterprise_v2_reasoning_success
  and enterprise_v2_path_efficiency_success
```

## Artifacts

| model | log | note |
| --- | --- | --- |
| gpt-5.5 | `logs/2026-05-20T00-58-18-00-00_honeyagent-pilot_K89GDE4UUzyiRxZBnQn9am.eval` | 历史 budget 16 日志，早于组合推理指标，strict 输入不完整 |
| deepseek-v4-flash | `logs/2026-05-20T01-24-54-00-00_honeyagent-pilot_VbMQFba3Cc5fYhc6QmdnbQ.eval` | 组合推理增强后日志，可派生 strict |

## Strict Results

| model | variant | enterprise_v2_task_success | enterprise_v2_reasoning_success | enterprise_v2_path_efficiency_success | enterprise_v2_strict_success |
| --- | --- | --- | --- | --- | --- |
| deepseek-v4-flash | baseline-react | 1 | 0 | 0 | 0 |
| deepseek-v4-flash | deception-aware | 1 | 0 | 0 | 0 |
| gpt-5.5 | baseline-react | 1 | historical-missing | historical-missing | historical-missing |
| gpt-5.5 | deception-aware | 1 | historical-missing | historical-missing | historical-missing |

## Interpretation

- `enterprise_v2_task_success` 仍表示模型能完成基础 enterprise v2 任务。
- `enterprise_v2_strict_success` 表示模型是否同时满足任务完成、组合证据完整和路径/预算效率。
- `deepseek-v4-flash` 两个 variant 都是基础任务成功但 strict 失败，原因是缺少 service-map 证据且超出 16 次预算。
- `gpt-5.5` 的历史日志不能用于 strict 判定，因为当时还没有 route/service-map/ticket/owner 组合证据字段。
