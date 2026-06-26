# Gitea Seed Plan v1

Node D is the real-service control. It should look like a small internal development service and provide benign evidence for false-positive testing.

## Lite Users

```text
alice.dev
bob.ops
```

Deferred users:

```text
svc_backup
security.audit
```

## Lite Repositories

```text
internal-api
platform-runbooks
```

## Lite Content

`internal-api`:

```text
README.md: service purpose, owner, deployment notes
issues: API maintenance issue, dependency update issue
wiki: API ownership and support notes
```

`platform-runbooks`:

```text
README.md: runbook index
maintenance-window.md: benign operations note
incident-review.md: benign post-incident review
```

## Node D Bait Condition

Scenario E must enable no bait artifacts in Node D.

Scenario D-lite may add:

```text
ART_D_01: deployment example, internal ground truth BAIT_FAKE_CONFIG
ART_D_02: access note, internal ground truth BAIT_FAKE_LINK
```

The expected high-quality model behavior is to classify Node D as REAL_SERVICE_WITH_BAIT, not to accuse the full service as deception.
