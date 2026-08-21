# Checkpoint — feat/rate-limit-middleware

## Outcome
`token-bucket-rs` selected and added as a dependency for rate limiting; `RateLimiter` is constructed in `middleware/throttle.py` but not yet enforced on the request path. Burst-limiting test currently fails.

## Scope and boundaries
- Allowed scope: `middleware/throttle.py`, `Cargo.toml`.
- Do not: change the public request-handling API other middleware depends on.

## Current state
- Repository: `/workspace/api-gateway`
- Working directory: `/workspace/api-gateway` (repository root)
- Branch: `feat/rate-limit-middleware`
- Changed files:
  - `Cargo.toml` — added `token-bucket-rs` as a dependency.
  - `middleware/throttle.py` — wires `token-bucket-rs` via FFI bindings; `RateLimiter::new(capacity, refill_rate)` is constructed correctly, but `RateLimiter.acquire()` is not yet called on the request path, so all requests still pass through unthrottled.
- Processes: No processes are running.

## Last verified evidence
- Decision (from earlier research this session): use `token-bucket-rs` over `sliding-window-py` for this service's bursty traffic pattern. Sources checked: each library's README and its benchmark suite. Verified claim: `token-bucket-rs` handles burst traffic without dropping requests under the service's peak load (~400 req/s for 2s bursts), confirmed by running its own `cargo bench --bench burst` locally.
- `cargo test --lib rate_limit` — passes (library-level tests).
- `pytest tests/middleware/test_throttle.py -q` — fails: `test_burst_requests_are_limited` expects the 401st request in a 1-second burst to be rejected, but it currently passes through.

## Files, artifacts and processes
- `Cargo.toml` — dependency added, no further changes pending.
- `middleware/throttle.py` — request handler still needs `RateLimiter.acquire()` wired in.
- `tests/middleware/test_throttle.py` — contains the failing test `test_burst_requests_are_limited`.
- No processes running.

## Next action
Call `RateLimiter.acquire()` at the top of `middleware/throttle.py`'s request handler, returning HTTP 429 when it returns false, then rerun `pytest tests/middleware/test_throttle.py -q`.

## Blocker or risk
None currently.

## Done when
`test_burst_requests_are_limited` passes and `token-bucket-rs` is actually enforced on the request path, not just constructed.

## Decision/learning
Chose `token-bucket-rs` over `sliding-window-py` because it demonstrably handles the service's bursty traffic (~400 req/s for 2s bursts) without dropping requests, per its own `cargo bench --bench burst`.

## Resume command
From repository root, after making the code change described in Next action:
```
pytest tests/middleware/ -q
```
