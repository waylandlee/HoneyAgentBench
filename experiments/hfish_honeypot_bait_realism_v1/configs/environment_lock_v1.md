# Environment Lock v1

Status: LOCKED_FOR_V3_2_MODEL_ABILITY

Date: 2026-06-26 Asia/Shanghai

## Purpose

This lock freezes the Docker topology while v3.2 tests model reasoning ability. The v3.2 change is limited to the model-visible observation layer and prompt framing. It does not add nodes, replace images, change ports, alter service policies, or pull images.

## Frozen Topology

- NODE_A: Dionaea-style low-depth multi-protocol service surface.
- NODE_B: Cowrie remote-access surface plus OWASP Juice Shop web application surface.
- NODE_C: HFish Client target with remote/web-style service surfaces and separate file-note observations.
- NODE_D: Gitea real collaboration service backed by Postgres, with seeded repositories and selected suspicious-looking files inside normal runbook content.
- CONTROL_PLANE: HFish Server remains non-model-visible and is used only by adapter/human verification.

## Frozen Compose And Image Assets

- Compose baseline: `configs/compose.realism-v1.yaml`.
- Digest-pinned compose override: `configs/compose.realism-v1.pinned.yaml`.
- HFish client bootstrap override: `configs/compose.realism-v1.hfish-client-bootstrap.yaml`.
- Image lock: `configs/image_manifest_v1.lock`.

## v3.2 Allowed Changes

- Generate neutral model-facing observations from existing `data/telemetry/live_adapter_observations.jsonl`.
- Generate raw-style fixed-action observations from existing smoke/seed evidence already summarized in live telemetry.
- Generate balanced evidence views that cap evidence volume per scenario/node/evidence role.
- Generate v3.2 dry-run prompts.
- Extend scorer reports with model-ability metrics.

## v3.2 Forbidden Changes

- No Docker topology changes.
- No new nodes or scenarios.
- No image pulls or automatic retries.
- No changes to v3.0 or v3.1 frozen prompts/responses.
- No external model/API call for v3.2 unless the user explicitly authorizes sending the new neutral/raw observations.

## Image Pull Policy

If any future step reports a missing image or an image pull failure, stop immediately and wait for manual download/tagging. Do not auto-pull or silently substitute images.

## Rationale

The project goal is now to measure the model itself rather than the deployment machinery. Keeping Docker fixed preserves a single independent variable: the observation/prompt representation shown to the model.
