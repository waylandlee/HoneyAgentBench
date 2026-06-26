# Node A Dionaea Smoke Report v1

Status: PASS

Validated on: 2026-06-26 Asia/Shanghai

## Result

`node_a_dionaea` passes the minimum Docker smoke test for the low-interaction honeypot node:

- Container stays `Up` for the smoke window on Docker internal `lab_net`.
- Docker inspect reports `status=running`, `restarting=false`, and `exit=0` during the check.
- The image exposes the expected honeypot service ports internally: `21`, `80`, `445`, `1433`, `3306`, `5060`, and `11211`.
- No host network, host filesystem mount, Docker socket mount, or privileged mode is used.

## Policy Adjustment

The first strict-profile attempt failed because the Dionaea image initializes runtime state under `/opt/dionaea/etc` and `/opt/dionaea/var` during startup. With all capabilities dropped and a read-only root filesystem, the entrypoint cannot prepare the runtime directory tree.

The compose policy was adjusted for this service only:

- `read_only: false`, keeping writes container-internal.
- `dionaea-var` mounted at `/opt/dionaea/var` for honeypot runtime state.
- Narrow `cap_add`: `CHOWN`, `FOWNER`, `DAC_OVERRIDE`, `NET_BIND_SERVICE`, `SETUID`, and `SETGID`.

This is still intentionally constrained: `cap_drop: ALL` remains the baseline, only the above capabilities are added back, `no-new-privileges` remains enabled, and the node remains reachable only through the internal lab network and the neutral adapter.

## Evidence

- Container status: `artifacts/docker_inspect/node_a_dionaea_ps_pass_20260626.txt`
- Runtime probe: `artifacts/docker_inspect/node_a_dionaea_probe_pass_20260626.txt`
- Logs: `logs/docker_pull/node_a_dionaea_smoke_pass_20260626.log`
- Local image status: `artifacts/docker_inspect/local_image_status_user_check_20260626.txt`
- Pinned compose override: `configs/compose.realism-v1.pinned.yaml`

## Interpretation

This validates Node A as a usable low-interaction honeypot asset for the benchmark. It also confirms a practical deployment rule for the experiment: honeypot images often require service-specific runtime write permissions, so the benchmark should evaluate realism under constrained, service-aware Docker policies rather than a single uniform read-only policy.
