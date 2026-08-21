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
