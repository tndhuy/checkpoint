# Developer task state

Repository: `/workspace/payment-service`; branch `fix/idempotent-refund`.

Outcome: make duplicate refund requests return the original successful refund without issuing a second provider call.

Current state: reproduction test was added in `tests/refunds/test_idempotency.py`. Implementation now writes the idempotency record, but it happens after the provider request and therefore still races. `pytest tests/refunds/test_idempotency.py -q` reports one failure: expected provider calls 1, observed 2.

Allowed scope: `src/refunds/`, the focused test and migration only if a uniqueness constraint is required. Do not change public response shape, provider client or unrelated payment flows.

Decision: move reservation of the idempotency key into the existing database transaction and rely on the unique `(merchant_id, idempotency_key)` constraint.

Next action: inspect `src/refunds/service.py::create_refund`, reserve the key before the provider call, then rerun the focused test.

Blocker: confirm whether the existing unique index is present in migration `20260118_refund_keys.sql`; do not create a duplicate migration blindly.

Done when: focused test passes, the existing refund suite passes and diff shows no response-contract changes.

No processes are running. Resume from repository root with `pytest tests/refunds/test_idempotency.py -q` after the code change.
