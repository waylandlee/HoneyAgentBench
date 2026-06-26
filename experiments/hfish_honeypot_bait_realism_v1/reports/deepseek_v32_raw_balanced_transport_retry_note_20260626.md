# DeepSeek v3.2 Raw-Balanced Transport Retry Note

Status: RESOLVED

During the first `raw_balanced` external run attempt, the DeepSeek HTTP response stream ended with `http.client.IncompleteRead(0 bytes read)`. The partial run directory contained only `prompts.jsonl`; no model responses or score outputs were present.

The v3.2 runner was then updated to:

- catch `http.client.IncompleteRead` as a transport-level API failure,
- write `responses.jsonl` incrementally after each scenario response,
- write `repaired_reports.jsonl` incrementally after each final report,
- write `repair_responses.jsonl` incrementally when repair is used.

The `raw_balanced` run was then rerun with the same fixed run id and completed successfully.
