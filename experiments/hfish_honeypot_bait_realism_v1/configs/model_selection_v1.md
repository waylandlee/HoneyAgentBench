# Model Selection v1

- experiment: hfish_honeypot_bait_realism_v1
- selected_external_model: deepseek-v4-pro
- provider: DeepSeek OpenAI-compatible API
- credential_env_var: DEEPSEEK_API_KEY
- base_url_env_var: DEEPSEEK_BASE_URL
- default_base_url: https://api.deepseek.com
- date_selected: 2026-06-26

## Secret Handling

The actual API key must not be written into this file, plans, reports, logs, manifests, or committed artifacts.

Runtime should read the key from:

```text
DEEPSEEK_API_KEY
```

The key may be placed in the local project `.env` file because `.env` is gitignored, or exported in the shell before running the experiment.

## Data Boundary

Using this model sends benchmark prompts, observations, and model-visible experiment content to the external DeepSeek API.

For the realism extension, do not start external model runs until M0-M4 assets are ready:

```text
M0: plan and metric definitions
M1: node/service/bait/scenario catalogs
M2: Docker compose and image manifest
M3: offline telemetry/scorer validation
M4: adapter and telemetry normalizer validation
```

First model run should be a small pilot:

```text
model: deepseek-v4-pro
scenarios: Scenario E, Scenario A-lite, Scenario B-lite, Scenario D-lite
seeds: 1 per scenario
purpose: verify chain, telemetry, evidence grounding, and failure taxonomy
```

## Recommended Run Policy

```text
1. Run local/offline checks first.
2. Run Docker smoke tests without LLM.
3. Run one DeepSeek pilot only after adapter/scorer validation.
4. Record every run in reports/pilot_report.md and summary.csv.
5. Never include API keys in logs or result manifests.
```
