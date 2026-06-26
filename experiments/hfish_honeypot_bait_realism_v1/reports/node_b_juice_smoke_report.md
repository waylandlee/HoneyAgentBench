# Node B Juice Shop Smoke Report v1

Status: PASS

Validated on: 2026-06-26 Asia/Shanghai

## Result

`node_b_juice` passes the minimum Docker smoke test for a realistic vulnerable web application node:

- Container stays `Up` on Docker internal `lab_net`.
- Juice Shop logs report `Server listening on port 3000`.
- Internal HTTP probe returns `status=200`.
- The returned HTML contains `<title>OWASP Juice Shop</title>`.

## Policy Adjustment

The first smoke run failed under `read_only: true` because Juice Shop writes SQLite state and FTP challenge files at startup:

```text
Error: EROFS: read-only file system, copyfile '/juice-shop/data/static/legal.md' -> '/juice-shop/ftp/legal.md'
SQLITE_CANTOPEN: unable to open database file
```

The compose policy was adjusted to `read_only: false` for this service only. It still keeps the important sandbox properties: dropped Linux capabilities, `no-new-privileges`, Docker internal network exposure, no host networking, and no host filesystem mount.

## Evidence

- Logs: `logs/gitea_raw/node_b_juice_smoke_after_policy_20260626.log`
- HTTP probe: `artifacts/docker_inspect/node_b_juice_http_probe_after_policy_20260626.txt`
- Compose render: `artifacts/docker_inspect/compose_config_after_juice_policy_20260626.txt`

## Interpretation

This confirms an important realism rule for the benchmark: high-interaction or real application services cannot be forced into a uniform read-only profile. The safer policy is service-aware isolation: keep network and privilege boundaries strict, but allow container-internal writes when the real application requires them.
