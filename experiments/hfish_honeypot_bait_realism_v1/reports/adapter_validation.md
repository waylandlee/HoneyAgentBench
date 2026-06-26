# Adapter Validation

Status: PASS

Validated offline adapter contract:

- Neutral model-visible action IDs resolve to structured observations.
- Each successful observation contains an evidence_id.
- No raw IP, port, URL, shell command, or external probe is accepted by this prototype.
- This validation did not start Docker services or call external model APIs.

Generated adapter events: `data\telemetry\offline_adapter_events.jsonl`
