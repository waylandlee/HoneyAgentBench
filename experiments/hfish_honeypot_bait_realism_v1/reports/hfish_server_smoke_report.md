# HFish Server Smoke Report v1

Status: PASS

Validated on: 2026-06-26 Asia/Shanghai

## Result

The `chinayin/hfish:2.6` image is usable as the HFish Server/control-plane asset for the realism-v1 Docker lab.

Confirmed:

- Image is locally available and digest-pinned in `configs/image_manifest_v1.lock`.
- Container stays `Up` under the restricted compose profile.
- HFish logs report successful server initialization.
- Container-internal probe to `https://127.0.0.1:4433/web/login` returns an HFish platform HTML page.
- Server can generate a Client node package through the authenticated `/v1/...` control API.
- Server accepts the bootstrapped HFish Client registration, config/service downloads, version checks, and telemetry posts from `node_c_hfish_client`.
- Stored logs are sanitized before use as experiment evidence.

## Evidence

- Pull log: `logs/docker_pull/hfish_server_pull_20260626.log`
- Sanitized smoke log: `logs/docker_pull/hfish_server_smoke_20260626.log`
- Internal endpoint probe: `artifacts/docker_inspect/hfish_server_internal_probe_20260626.txt`
- Port-policy probe: `artifacts/docker_inspect/hfish_server_probe_limited_20260626.txt`
- Client bootstrap summary: `artifacts/docker_inspect/hfish_client_bootstrap_summary_latest.json`
- Server logs after Client bootstrap: `logs/docker_pull/hfish_server_after_client_bootstrap_retry_20260626.log`

## Model-Visibility Policy

HFish Server is not a model-visible node. It is used only as the internal control component for package generation and telemetry normalization. Model-facing observations must refer to neutral `node-c` actions and evidence IDs, not to the HFish admin UI, node IDs, API keys, package URLs, cookies, or client IDs.

## Current Limitation

The `chinayin/hfish:2.6` server image also starts embedded service listeners. For formal experiments, those server-side listeners should remain excluded from the model-facing topology; the measured Node C surface is the separate `node_c_hfish_client` container.

## Interpretation

HFish Server is now acceptable as a non-model-visible control-plane dependency for the benchmark. The separate Client node has its own PASS report and should be the only HFish-derived model-visible target.
