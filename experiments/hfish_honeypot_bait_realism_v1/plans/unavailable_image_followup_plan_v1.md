# Unavailable Image Follow-up Plan v1

Status: ACTION REQUIRED

Created on: 2026-06-26 Asia/Shanghai

## Current Gaps

| Node | Intended role | Current blocker | Required action |
|---|---|---|---|
| Node A | Low-interaction Dionaea-style multi-protocol honeypot | `dinotools/dionaea:latest` failed at Docker Hub auth-token fetch. | Retry once with stable network, then replace with local pinned build if it still fails. |
| Node B remote | Cowrie SSH/Telnet interaction surface | `cowrie/cowrie:latest` timed out twice and no digest is available. | Prefer preloading/mirroring the official image; otherwise build a local pinned Cowrie image. |
| Node C | HFish model-visible client/target | `chinayin/hfish:2.6-client` timed out and no digest is available. | Retry pull with longer timeout or determine whether the all-in-one `chinayin/hfish:2.6` image can safely represent the target node. |

## Conservative Path

1. Keep Node D Gitea/Postgres and Node B Juice Shop as validated real-service assets.
2. Treat HFish Server as an internally validated control-plane/all-in-one candidate, not yet a formal Node C target.
3. Do not run DeepSeek seeded experiments until every model-visible node has either a digest-pinned image or a local build provenance record.
4. For formal v0.2 assets, avoid `latest` tags; convert every successful image to digest-pinned references in compose or an override file.

## Replacement Criteria

An image can enter the formal benchmark only if all are true:

- Pull or local build completes reproducibly.
- Digest or local build commit is recorded.
- Container starts under a documented restricted policy.
- Model-visible observations do not leak labels such as honeypot, bait, HFish, Cowrie, Dionaea, or real service.
- Logs are sanitized before becoming committed artifacts.

## Next Engineering Move

Implement an image acquisition script that supports three modes per service:

```text
pull: docker pull the upstream image with timeout and digest recording
mirror: pull from a configured internal/local registry mirror
build: build a local pinned image from checked-in Dockerfile/context
```

This will turn the current ad hoc pull evidence into a repeatable M2 asset gate.
