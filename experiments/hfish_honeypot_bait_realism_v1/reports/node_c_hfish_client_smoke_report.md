# Node C HFish Client Smoke Report v1

Status: PASS

Validated on: 2026-06-26 Asia/Shanghai

## Result

`node_c_hfish_client` now passes the Docker smoke test as a separate model-visible HFish Client target.

Confirmed:

- The `chinayin/hfish:2.6-client` image is locally available and digest-pinned.
- HFish Server can generate a client package through the authenticated control API.
- `scripts/bootstrap_hfish_client_package.py` downloads the authenticated `client.tgz`, validates it as a gzip tarball, and stores it only under gitignored `runtime/hfish/client.tgz`.
- `configs/compose.realism-v1.hfish-client-bootstrap.yaml` runs the Client from the mounted local tarball instead of exposing a session-protected package URL through `CLIENT_URL`.
- Docker inspect reports `Status=running`, `Running=true`, `Restarting=false`, and `ExitCode=0` for `realism-node-c-target` during the smoke window.
- Client logs show package extraction, service package installation, `LOCAL` and `SCAN` service startup, and successful data posts to HFish Server.
- HFish Server logs show the Client registering from the model-visible node address and posting telemetry successfully.

## Evidence

- Bootstrap script: `scripts/bootstrap_hfish_client_package.py`
- Bootstrap compose override: `configs/compose.realism-v1.hfish-client-bootstrap.yaml`
- Bootstrap summary: `artifacts/docker_inspect/hfish_client_bootstrap_summary_latest.json`
- Client compose state: `artifacts/docker_inspect/node_c_hfish_client_bootstrap_retry_ps_20260626.txt`
- Client inspect state: `artifacts/docker_inspect/node_c_hfish_client_bootstrap_retry_state_20260626.txt`
- Client sanitized logs: `logs/docker_pull/node_c_hfish_client_bootstrap_retry_20260626.log`
- Server sanitized logs after Client bootstrap: `logs/docker_pull/hfish_server_after_client_bootstrap_retry_20260626.log`

Key observed lines:

```text
realism-node-c-target          Up About a minute
Status=running Running=true Restarting=false ExitCode=0
install services package success
service[LOCAL] start
post client data result: {"response_code":0,"verbose_msg":"??"}
```

## Secret Handling

The runtime package and authenticated download details are deliberately not committed:

- `runtime/hfish/client.tgz` is local runtime state and is ignored by `runtime/.gitignore`.
- Cookies, package URLs, node IDs, API keys, client IDs, and default passwords are not written into reports or model-visible observations.
- Stored bootstrap summaries include only package size, tar member names, digest, and redacted URL shape.

## Current Limitation

HFish Client starts and reports successfully, but the `SCAN` module logs packet-capture permission warnings under the current restricted Docker policy. This does not block Client registration or local service telemetry. If later experiments require packet-capture behavior itself, add a separate, explicitly justified policy variant for `NET_RAW`/`NET_ADMIN`, or keep scan capture out of the measured surface.

## Interpretation

Node C can now be promoted from a partial asset to a smoke-tested HFish Client asset for the next benchmark stage. The model must still access it only through neutral adapter actions; HFish Server remains a non-model-visible control component.
