---
type: checkpoint
created: 2026-08-02
updated: 2026-08-02
status: active
profile: developer
project: payment-service
branch: fix/idempotent-refund
owner: ""
---

# Checkpoint — Idempotent duplicate refunds

## Outcome

Make duplicate refund requests return the original successful refund without issuing a second provider call.

## Scope and boundaries
- Allowed: `src/refunds/`, `tests/refunds/test_idempotency.py`, and a migration only if a uniqueness constraint is required.
- Do not: change the public response shape, provider client, or unrelated payment flows. Do not create a duplicate migration blindly.

## Current state

The reproduction test exists. The implementation writes the idempotency record after the provider request, so concurrent duplicate requests still race.

Decision: reserve the idempotency key inside the existing database transaction and rely on the unique `(merchant_id, idempotency_key)` constraint.

## Last verified evidence
- Check/test/runtime: `pytest tests/refunds/test_idempotency.py -q`
- Result: one failure; expected provider calls `1`, observed `2`.

## Files, artifacts and processes
- Working directory: `/workspace/payment-service`
- Branch: `fix/idempotent-refund`
- Changed files: `tests/refunds/test_idempotency.py`; implementation change writes an idempotency record, exact source file change not stated.
- Relevant files: `src/refunds/service.py`, `20260118_refund_keys.sql`
- Running processes/sessions: none.

## Next action
1. Inspect `20260118_refund_keys.sql` and confirm the unique index exists.
2. Inspect `src/refunds/service.py::create_refund` and reserve the idempotency key before the provider call inside the existing database transaction.
3. Run `pytest tests/refunds/test_idempotency.py -q`.
4. Run the existing refund suite and inspect the diff for response-contract changes.

## Blocker or risk

Unconfirmed whether migration `20260118_refund_keys.sql` already contains the required unique index. Creating another migration before checking risks duplicating the constraint. Provider calls must not move outside the allowed contract boundaries.

## Done when
- [ ] Focused idempotency test passes.
- [ ] Existing refund suite passes.
- [ ] Diff shows no public response-contract changes.

## Decision/learning

Reserve the idempotency key before the provider request within the existing transaction; uniqueness is enforced by `(merchant_id, idempotency_key)` once the existing index is confirmed.

## Open-loop lifecycle
- `park` — migration creation; wait until `20260118_refund_keys.sql` is inspected and only add a migration if the unique constraint is absent.

## Resume command
```sh
cd /workspace/payment-service
# After the code change:
pytest tests/refunds/test_idempotency.py -q
```
