# Checkpoint benchmark — 2026-08-02

## Verdict

PASS for the three fixture profiles: developer, research and operations.

This run proves deterministic contract preservation and isolated-agent cold resume within the same benchmark run. It does not yet prove performance across a real multi-day project handoff.

## Method

1. A fresh creator agent received only the checkpoint skill and one raw fixture.
2. A deterministic evaluator checked required sections, profile concepts and fixture-critical facts.
3. A second fresh agent received only the generated checkpoint and produced a resume assessment.
4. A baseline agent received only the raw fixture and produced the same assessment.
5. The evaluator checked resume fields, critical resume concepts and reconstructive-question count.

Agents were instructed not to inspect expectations, tests, documentation, Git history or other result files.

## Results

| Profile | Contract | Checkpoint questions | Baseline questions | Cold-resume gate |
|---|---:|---:|---:|---|
| Developer | 19/19 | 2 | 4 | PASS |
| Research | 18/18 | 3 | 5 | PASS |
| Operations | 20/20 | 0 | 5 | PASS |

Totals: 5 reconstructive questions with checkpoints versus 14 from raw-state baselines, a reduction of 9 questions (64.3%) across these fixtures.

## Verification

- 10 unit tests pass.
- Repository skill structure passes the local verifier.
- Official skill-creator validator reports `Skill is valid!`.
- All three checkpoint contract evaluators pass.
- All three cold-resume evaluators pass and use fewer reconstructive questions than their baselines.

## Interpretation

Checkpointing did not make the agents smarter. It converted implicit state into an explicit handoff contract: current state, exact next action, scope boundary and done gate. The measured benefit in this run is reduced reconstruction, not higher implementation quality.

## Limitations and next proof

- Small synthetic fixture set.
- Same-day run, despite fresh isolated agent contexts.
- Question count can be influenced by agent style.
- No elapsed-time or repeated-tool-call telemetry yet.

Next confidence step: use the skill on one real task, resume it in a later session or with another agent, then record elapsed resume time, repeated tool calls, questions and scope mistakes.
