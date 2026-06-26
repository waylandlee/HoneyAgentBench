# Live Adapter Validation

Status: PASS

Run ID: `live-adapter-materialized-artifacts-20260626`
Generated evidence events: `data/telemetry/live_realism_events.jsonl`
Generated observations: `data/telemetry/live_adapter_observations.jsonl`

Validated properties:

- Fixed neutral action IDs only; no raw IP, port, URL, or shell command is accepted from the model.
- Docker-backed service actions resolve to smoke reports and sanitized logs.
- Model-facing observation text is checked for configured forbidden ground-truth terms.
- Internal evidence rows keep ground truth and source mode outside model-facing observations.
