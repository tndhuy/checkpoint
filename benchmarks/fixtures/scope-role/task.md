# Developer task state — first checkpoint in this project

Repository: `/workspace/notif-gateway`; branch `feat/webhook-retry-backoff`.

No `.checkpoint/config.md` exists in this repository, and no global checkpoint config has been configured on this machine. This is the first time `$checkpoint:save` has been invoked in this project.

Outcome: webhook delivery retries should back off exponentially instead of retrying every 2 seconds, so a downstream outage doesn't hammer the failing endpoint.

Current state: `src/webhooks/retry_policy.py` now computes exponential delay, but the scheduler in `src/webhooks/dispatcher.py` still reads the old fixed `RETRY_INTERVAL_SECONDS` constant instead of calling the new policy. `pytest tests/webhooks/test_retry_policy.py -q` passes; `pytest tests/webhooks/test_dispatcher.py -q` fails one case: expected next-retry delay `8`, observed `2`.

Allowed scope: `src/webhooks/`. Do not change the public webhook registration API or the delivery-status database schema.

Next action: wire `dispatcher.py`'s scheduler to call `retry_policy.next_delay(attempt)` instead of the fixed constant, then rerun the dispatcher test.

Blocker: none currently.

Done when: both test files pass and the fixed `RETRY_INTERVAL_SECONDS` constant is removed with no remaining references.

No processes are running. Resume from repository root with `pytest tests/webhooks/ -q` after the code change.

---

The user just typed: `$checkpoint:save`
