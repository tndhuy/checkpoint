# Repository instructions

## Source of truth

- Runtime plugin: `plugins/checkpoint/`
- Runtime skill: `plugins/checkpoint/skills/checkpoint/`
- Contract and distribution checks: `scripts/`
- Behavioral fixtures and evidence: `benchmarks/`

Do not duplicate the runtime skill into another tracked directory. Development discovery paths must point to this source.

## Required verification

Run `python3 scripts/verify.py` after changing the skill, manifests, evaluators, fixtures, or tests.

Keep generated scratch output under `benchmarks/results/tmp/`. Add dated evidence only after its evaluator passes. Do not rewrite prior dated evidence.

## Release rules

- Keep plugin, marketplace, and project versions aligned.
- Run Codex and Claude manifest validators before tagging.
- Use a fresh task or session for behavioral forward tests.
- Never claim multi-day handoff proof from a same-run fixture benchmark.
- Do not add hooks, MCP servers, telemetry, network access, or autonomous writes without a documented use case and threat review.
