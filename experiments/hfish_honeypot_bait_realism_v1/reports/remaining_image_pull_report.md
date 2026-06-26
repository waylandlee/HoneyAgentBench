# Docker Image Availability Report v3

Status: LOCAL IMAGES AVAILABLE

Validated on: 2026-06-26 Asia/Shanghai

## Current Result

All planned Docker images for `hfish_honeypot_bait_realism_v1` are now available locally and recorded in `configs/image_manifest_v1.lock` with digest pins.

| Service | Image | Current status | Smoke status |
|---|---|---|---|
| `node_a_dionaea` | `dinotools/dionaea:latest` | Local image available and digest-pinned | PASS |
| `node_b_cowrie` | `cowrie/cowrie:latest` | Local image available and digest-pinned | PASS |
| `node_b_juice` | `bkimminich/juice-shop:latest` | Local image available and digest-pinned | PASS |
| `hfish_server` | `chinayin/hfish:2.6` | Local image available and digest-pinned | PARTIAL PASS |
| `node_c_hfish_client` | `chinayin/hfish:2.6-client` | Local image available and digest-pinned | PARTIAL / NOT YET PASS |
| `node_d_gitea` | `gitea/gitea:1.22-rootless` | Local image available and digest-pinned | PASS |
| `node_d_postgres` | `postgres:16-alpine` | Local image available and digest-pinned | PASS |

## What Changed Since v2

Earlier pulls for Dionaea, Cowrie, and HFish Client had failed or timed out. Those images are now present locally. Two mirror-prefixed images were tagged into the canonical names expected by compose:

- `cowrie/cowrie:latest`
- `chinayin/hfish:2.6-client`

The final local image check is recorded at `artifacts/docker_inspect/local_image_status_user_check_20260626.txt`.

## Remaining Non-Image Issue

There is no current image-pull blocker. The remaining blocker is HFish Client bootstrap realism:

- The control API can generate a node package.
- The generated UI package URL is session-protected.
- The current Client container cannot directly consume that URL as `CLIENT_URL`.

See `reports/node_c_hfish_client_smoke_report.md` for the detailed diagnosis.

## Operating Rule

For future runs, if Docker reports a missing image or an image pull failure, pause the experiment and request manual image acquisition instead of repeatedly retrying automatic pulls.
