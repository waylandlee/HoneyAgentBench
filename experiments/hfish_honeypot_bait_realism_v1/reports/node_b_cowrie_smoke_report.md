# Node B Cowrie Smoke Report v1

Status: PASS

Validated on: 2026-06-26 Asia/Shanghai

## Result

`node_b_cowrie` passes the minimum Docker smoke test for the SSH/Telnet honeypot node:

- Container stays `Up` for the smoke window on Docker internal `lab_net`.
- Docker inspect reports `Status=running`, `Running=True`, `Restarting=False`, and `ExitCode=0` during the check.
- Cowrie logs report `CowrieSSHFactory starting on 2222` and `Ready to accept SSH connections`.
- Cowrie logs report `HoneyPotTelnetFactory starting on 2223` and `Ready to accept Telnet connections`.
- The service uses the digest-pinned local image `cowrie/cowrie@sha256:b4817f185e522f5a66975568ff304ae02c042b65454c2542918f42dbaf1b31fa`.

## Policy Result

Cowrie works under the stricter Docker policy already in the compose file:

- `read_only: true`
- dropped Linux capabilities through the shared restricted profile
- `no-new-privileges:true`
- internal Docker network exposure only
- no host network, host filesystem mount, Docker socket mount, or privileged mode

One operational note: the Cowrie image does not include a generic `sh` executable, so shell-based container probes are not portable for this image. The accepted smoke evidence is therefore compose status, Docker inspect state, and Cowrie's own readiness logs.

## Evidence

- Startup log: `logs/docker_pull/node_b_cowrie_smoke_up_20260626.log`
- Runtime logs: `logs/docker_pull/node_b_cowrie_smoke_20260626.log`
- Container status: `artifacts/docker_inspect/node_b_cowrie_ps_20260626.txt`
- Docker inspect state: `artifacts/docker_inspect/node_b_cowrie_state_20260626.txt`
- Full inspect JSON: `artifacts/docker_inspect/node_b_cowrie_inspect_20260626.json`

## Interpretation

This validates Node B's SSH/Telnet honeypot surface as a realistic high-interaction deception target for the benchmark. Compared with Node A, Cowrie needs fewer Docker policy exceptions, which is useful for the experiment because different honeypot classes now produce different deployment and realism profiles.
