# Checkpoint Skill

Agent-neutral skill for capturing concise, evidence-backed and resumable task state before context switches, pauses, handoffs or compaction.

## Repository layout

- `skills/checkpoint/` — installable runtime skill.
- `scripts/` — deterministic contract and cold-resume evaluators.
- `tests/` — regression tests for structure and evaluation behavior.
- `benchmarks/fixtures/` — developer, research and operations scenarios.
- `benchmarks/results/` — dated forward-test evidence.
- `docs/BENCHMARK.md` — benchmark protocol and acceptance gates.

## Verify

```bash
python3 scripts/verify.py
```

Run a dated checkpoint contract:

```bash
python3 scripts/evaluate_checkpoint.py \
  benchmarks/results/2026-08-02/developer-checkpoint.md \
  benchmarks/fixtures/developer/expected.json
```

Run its cold-resume comparison:

```bash
python3 scripts/evaluate_resume.py \
  benchmarks/results/2026-08-02/developer-resume.json \
  benchmarks/fixtures/developer/expected.json \
  --baseline benchmarks/results/2026-08-02/developer-baseline.json
```

## Install locally

The maintained checkout is linked into the agent discovery directory:

```text
~/.agents/skills/checkpoint -> <repo>/skills/checkpoint
```

The installer is intentionally not automatic. Replacing an existing discovery path must preserve its contents and requires explicit approval.

## Current evidence

The 2026-08-02 isolated-agent benchmark passed all developer, research and operations fixtures. Checkpoints required 5 reconstructive questions in total versus 14 for raw-state baselines. See `benchmarks/results/2026-08-02/report.md`.

This is same-run cold-context evidence, not yet a multi-day real-project handoff. The next proof should record resume time, repeated tool calls, questions and scope mistakes on a real task.
