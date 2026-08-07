Checkpoint saved — first save in this project, so it's using the default `scope: project` (writing to `.checkpoint/` at the repo root, config recorded in `.checkpoint/config.md`) and `role: Unknown` until you answer below.

# Checkpoint — Exponential backoff for webhook delivery retries

## Outcome
Webhook delivery retries should back off exponentially instead of retrying every 2 seconds, so a downstream outage doesn't hammer the failing endpoint. Not yet complete: policy logic is written, dispatcher is not yet wired to it.

## Scope and boundaries
- Allowed: `src/webhooks/`
- Do not: change the public webhook registration API
- Do not: change the delivery-status database schema

## Current state
`src/webhooks/retry_policy.py` now computes exponential delay. `src/webhooks/dispatcher.py` still reads the old fixed `RETRY_INTERVAL_SECONDS` constant instead of calling the new policy — the integration hasn't happened yet.

## Last verified evidence
- Check/test/runtime: `pytest tests/webhooks/test_retry_policy.py -q`
- Result: passes
- Check/test/runtime: `pytest tests/webhooks/test_dispatcher.py -q`
- Result: fails — one case expected next-retry delay `8`, observed `2`

## Files, artifacts and processes
- Working directory: `/workspace/notif-gateway`
- Branch: `feat/webhook-retry-backoff`
- Changed files: `src/webhooks/retry_policy.py` (exponential delay logic added), `src/webhooks/dispatcher.py` (not yet updated — still references `RETRY_INTERVAL_SECONDS`)
- Running processes/sessions: None

## Next action
1. In `src/webhooks/dispatcher.py`, wire the scheduler to call `retry_policy.next_delay(attempt)` instead of the fixed `RETRY_INTERVAL_SECONDS` constant, then rerun the dispatcher test.

## Blocker or risk
None currently.

## Done when
- [ ] `tests/webhooks/test_retry_policy.py` passes
- [ ] `tests/webhooks/test_dispatcher.py` passes
- [ ] `RETRY_INTERVAL_SECONDS` constant is removed with no remaining references

## Decision/learning
Retry delay computation was deliberately isolated in `retry_policy.py` rather than inlined in the dispatcher — the remaining work is integration only, not new logic.

## Open-loop lifecycle
- `promote` — dispatcher wiring to `retry_policy.next_delay(attempt)`: this is the immediate next action, ready to resume on next session, no revisit condition needed.

## Resume command
```sh
cd /workspace/notif-gateway && pytest tests/webhooks/ -q
```

---

Quick one-time setup question since this project has no recorded checkpoint preferences yet: save checkpoints in this project, or in a global store? And what's your role on this work (e.g. implementer, reviewer)? I'll remember the answer for future `$checkpoint:save` calls in this repo.
