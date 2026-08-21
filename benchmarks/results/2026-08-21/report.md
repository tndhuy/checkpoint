# Checkpoint benchmark — 2026-08-21

## Verdict

PASS for the new `mixed-evidence-profile` fixture (19/19).

This run tests the new profile-precedence rule added to `references/profiles.md` and `SKILL.md`'s "Select profile" section: when a task carries evidence for more than one profile (here: research evidence — comparing two libraries — followed by developer evidence — implementing the chosen one), the profile is decided by `Next action`, not by which evidence appeared first or is most abundant. This was a proactive change (no observed real-world misclassification prompted it) — the fixture exists to give the rule regression coverage before it is relied on.

## Method

1. A fresh agent received only the relevant skill instructions (Select-profile rule, the full updated `references/profiles.md`, and the "Write" section's required structure) and the raw `mixed-evidence-profile` fixture — no filesystem or tool access, no visibility into `expected.json`, tests, or this report.
2. Its output was saved verbatim and evaluated with `scripts/evaluate_checkpoint.py` against `benchmarks/fixtures/mixed-evidence-profile/expected.json`.

Unlike the 2026-08-02 run, this one did not include a second cold-resume pass or a baseline comparison — it is scoped to the single question this change needed answered: does the precedence rule land the correct profile on a genuinely mixed-evidence task.

## Results

| Fixture | Contract | Profile chosen | Expected |
|---|---:|---|---|
| mixed-evidence-profile | 19/19 | developer | developer |

One soft (non-failing) verbosity warning: `Last verified evidence` ran 87 words against an 80-word ceiling — not a correctness issue, left as-is.

## Verification

- `scripts/verify.py` passes (distribution manifests/versions/paths/privacy, all unit tests, skill structure).
- The generated checkpoint correctly used developer-profile fields (Branch, Changed files, test evidence, Resume command) driven by the code-step `Next action`, despite the task opening with research evidence (library comparison, benchmark claim) that a naive "first evidence wins" reading could have misclassified as `research`.

## Interpretation

The precedence rule works on the one case it was written for. This does not prove the rule handles every mixed-evidence shape (a task where `Next action` itself straddles two kinds of work, for instance) — only that the clearest, most common case (research that concludes into an implementation task) resolves correctly instead of ambiguously.

## Limitations and next proof

- Single fixture, single run — no repeated-agent variance check.
- Does not cover the `generic` fallback case (`Next action` spanning two kinds of work equally) described in the same rule addition — untested.
- Does not cover research-evidence-after-code or operations-mixed-with-developer permutations.
- No real (non-synthetic) misclassification has ever been observed — this remains proactive coverage, not a regression fix. Revisit if a real case is found not to match this rule's prediction.

## Addendum — recall cold-resume test (same fixture, same day)

`$checkpoint:recall` had zero forward-test coverage anywhere in this repo's history before this run — closing that gap, reusing the `mixed-evidence-profile` checkpoint generated above.

**Method**: two independent fresh agents, neither with tool/filesystem access. Agent A received only the `recall` skill's 5-question instructions plus the checkpoint document generated earlier in this report. Agent B (baseline) received only the raw `task.md` fixture, with no checkpoint, framed as "a raw session log with nothing independently re-verified." Both produced a JSON resume assessment (`current_state`, `exact_next_action`, `scope_boundary`, `done_gate`, `reconstructive_questions`), evaluated with `scripts/evaluate_resume.py` against `benchmarks/fixtures/mixed-evidence-profile/resume-expected.json`.

**Result**:
```json
{
  "passed": false,
  "missing_keys": [],
  "invalid_keys": [],
  "missing_resume_terms": ["feat/rate-limit-middleware"],
  "reconstructive_questions": 4,
  "baseline_questions": 10,
  "fewer_questions_than_baseline": true
}
```

**Interpretation**: the core claim holds — checkpoint-fed resume needed 4 reconstructive questions against the baseline's 10 (60% reduction, in line with the 2026-08-02 report's 64.3% finding on the original three fixtures). Recall genuinely reduces reconstruction burden here. But the strict evaluator marks this run FAIL: the agent's structured JSON never restated the branch name (`feat/rate-limit-middleware`) inside the four required fields — it mentioned the branch in a free-text "staleness note" outside the JSON, and in one of its own `reconstructive_questions` ("Is the working directory still ... on branch feat/rate-limit-middleware?"), so the fact was retained and even correctly flagged as needing re-verification, just not echoed where the evaluator checks for it.

This is reported as-is rather than loosened after the fact — changing `resume-expected.json` post-hoc to make this pass would be gaming the test, not fixing anything. Left as an open, honest finding below.

## Known limitation (recall)

- `recall` reliably reduces reconstructive questions versus a raw-log baseline (this run: 4 vs 10), but on this run its structured JSON output didn't always restate every identifying fact (here: the branch name) inside the four required fields, even when the same fact appeared correctly elsewhere in its own answer. Whether this is a fixture-strictness artifact or a real recall-skill gap worth a wording fix is unresolved — single run, not enough evidence either way. Revisit if it recurs.
