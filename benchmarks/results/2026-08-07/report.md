# Checkpoint benchmark — 2026-08-07 (scope/role forward test)

## Verdict

FAIL on the first run, FIXED and PASS on the corrected re-run. This is a genuine regression the forward test caught before release, not a clean pass.

## Method

Per `CONTRIBUTING.md`'s "run the baseline without the proposed instruction" step, applied here as "run the baseline *with* the newly proposed instruction, unfixed."

1. A fresh, isolated creator agent (no filesystem access, no memory of any prior session) received the `save` skill plus the new `references/scope-and-role.md` reference verbatim, and one fixture: `benchmarks/fixtures/scope-role/task.md` — a first-run project with no `.checkpoint/config.md` and no global config, explicit `$checkpoint:save` invocation.
2. Its response was scored with `scripts/evaluate_checkpoint.py` against `benchmarks/fixtures/scope-role/expected.json` (`profile: developer`, 5 required terms drawn from the fixture).
3. The skill instructions were revised based on the failure (see Findings).
4. A second, independently fresh agent received the corrected instructions and the same fixture.
5. Its response was scored the same way.

## Results

| Run | Contract | Verdict |
|---|---:|---|
| 1 — original scope/role wording | 1/18 | **FAIL** |
| 2 — corrected wording | 18/18 | PASS |

Raw transcripts: `scope-role-run1-baseline-bug.md`, `scope-role-run2-corrected.md` in this directory.

## Findings

Run 1's agent read the first-run branch of the scope/role resolution order ("ask exactly one question... persist both answers") as blocking, and asked its scope/role question **instead of** writing the checkpoint — silently dropping the pre-existing, unrelated hard requirement in `save/SKILL.md`: *"The user explicitly invoked save: write the checkpoint now instead of summarizing this process"* and *"always render the full canonical template... including for chat-only output."* Zero checkpoint content was produced; the developer's explicit `$checkpoint:save` request went unanswered pending a config question that had nothing to do with what they asked to capture.

This is exactly the failure mode `save/SKILL.md`'s existing test coverage (`test_explicit_invocation_requires_canonical_template`) could not catch, because that test only asserts the *instruction text* contains certain phrases — it does not exercise agent behavior. The instruction text was technically unchanged and still present; a new, ambiguously-scoped instruction elsewhere silently overrode it in practice.

## Fix

Added an explicit non-blocking rule to both `references/scope-and-role.md` and `save/SKILL.md` itself (defense in depth — the failure happened even with the reference doc present, so the summary in `save/SKILL.md` needed its own explicit statement, not just a pointer): on first run, `save` renders and writes the full checkpoint immediately using defaults (`scope: project`, `role: Unknown`), and the scope/role question rides alongside that response, never in place of it. Run 2 confirms the fix: full contract pass, and the scope/role question is still asked in the same response — both properties hold simultaneously.

## Verification

- `scripts/verify.py`: 20/20 unit tests pass, distribution validator passes, skill structure check passes (re-run after the fix, not just before it).
- `claude plugin validate --strict .` and `claude plugin validate --strict plugins/checkpoint`: both pass.
- `checkpoint_contract.py`'s new `verbosity_warnings` field is empty on the corrected run's output — the checkpoint stayed concise despite the added scope/role question appended after it.

## Limitations and next proof

- Single fixture, single domain (developer/backend). Scope=`global` and role≠`Unknown` first-run paths were not separately forward-tested — only the all-defaults first-run path was exercised end-to-end.
- `list --scope` and `recall --scope` filtering were not forward-tested at all this round; only `save`'s scope/role/trigger behavior was.
- Codex-side behavior (`$checkpoint:save` via the Codex app-server smoke harness in `scripts/smoke_codex_app_server.mjs`) was not run this round; only the host-neutral skill text was forward-tested via an isolated text-generation agent, matching the method used in the 2026-08-02 benchmark but not the real Codex app-server protocol.
- No real project has exercised this over multiple actual `save` calls to confirm the config file, once written, is actually read back silently on the second call (steps 1–2 of resolution) rather than only the first-run path (step 3) validated here.
