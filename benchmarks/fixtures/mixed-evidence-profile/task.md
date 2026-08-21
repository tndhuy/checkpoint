# Mixed-evidence task state — research led into implementation

Repository: `/workspace/api-gateway`; branch `feat/rate-limit-middleware`.

Earlier this session: compared two rate-limiting libraries, `token-bucket-rs` and `sliding-window-py`, against this service's traffic pattern (bursty, not steady). Sources checked: each library's README and its benchmark suite. Verified claim: `token-bucket-rs` handles burst traffic without dropping requests under the service's peak load (~400 req/s for 2s bursts), confirmed by running its own `cargo bench --bench burst` locally. Decision made: use `token-bucket-rs`.

Since then: added `token-bucket-rs` as a dependency in `Cargo.toml` and started wiring it into `middleware/throttle.py` via its FFI bindings. `RateLimiter::new(capacity, refill_rate)` is constructed correctly, but `RateLimiter.acquire()` is not yet called on the request path — `middleware/throttle.py` still lets all requests through unthrottled. `cargo test --lib rate_limit` passes (library-level tests); `pytest tests/middleware/test_throttle.py -q` fails: `test_burst_requests_are_limited` expects the 401st request in a 1-second burst to be rejected, but it currently passes through.

Allowed scope: `middleware/throttle.py`, `Cargo.toml`. Do not change the public request-handling API other middleware depends on.

Next action: call `RateLimiter.acquire()` at the top of `middleware/throttle.py`'s request handler, returning HTTP 429 when it returns false, then rerun `pytest tests/middleware/test_throttle.py -q`.

Blocker: none currently.

Done when: `test_burst_requests_are_limited` passes and `token-bucket-rs` is actually enforced on the request path, not just constructed.

No processes are running. Resume from repository root with `pytest tests/middleware/ -q` after the code change.

---

The user just typed: `$checkpoint:save`
