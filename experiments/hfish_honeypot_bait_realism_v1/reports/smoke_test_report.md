# Smoke Test Report v1

Status: PARTIAL PASS

Scope: Scenario E / Node D real-service control only.

Validated on: 2026-06-26 Asia/Shanghai

## Result

Node D now passes the minimum Docker smoke test for a real-service control node:

- `node_d_postgres` stays `Up` and accepts database connections.
- `node_d_gitea` stays `Up`, connects to Postgres, initializes ORM successfully, and listens on HTTP port 3000 inside `lab_net`.
- Internal service probe returns the real Gitea HTML homepage title: `Gitea: Git with a cup of tea`.
- No host-facing service port was exposed for Node D; only Docker internal network exposure was used.

## Evidence

- Compose state: `artifacts/docker_inspect/scenario_e_smoke_ps_20260626.txt`
- Image digests: `artifacts/docker_inspect/image_digests_20260626.txt`
- Service logs: `logs/gitea_raw/scenario_e_smoke_after_setuid_fix_20260626.log`

Key observed lines:

```text
realism-node-d-postgres   Up   5432/tcp
realism-node-d-gitea      Up   2222/tcp, 3000/tcp
/var/run/postgresql:5432 - accepting connections
<title>Gitea: Git with a cup of tea</title>
```

## Fixes Applied During Smoke

Initial attempts failed because the restricted container profile dropped capabilities that the Postgres entrypoint needs during first-run volume ownership and user switching.

The compose file now grants only the narrow Postgres capabilities needed for initialization:

```text
CHOWN
FOWNER
DAC_OVERRIDE
SETUID
SETGID
```

This remains non-privileged: no `privileged: true`, no host networking, no Docker socket mount, and no host filesystem mount were introduced.

## Current Limitation

This report validates only Node D. Node A, Node B, Node C, and the HFish control plane still need image pull, digest pinning, startup checks, telemetry checks, and model-visible observation checks before v3 seeded model experiments.

## Model/API Status

DeepSeek has been selected as the external model provider, with runtime access through `DEEPSEEK_API_KEY`. No external model API call was made during this smoke test, and no API key was written to disk.
