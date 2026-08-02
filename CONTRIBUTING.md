# Contributing

## Change workflow

1. Add or update a fixture that demonstrates the behavior.
2. Run the baseline without the proposed instruction when behavior is changing.
3. Update the skill or deterministic evaluator.
4. Run `python3 scripts/verify.py`.
5. Forward-test with a fresh agent that cannot read expectations or prior outputs.
6. Store passing evidence under a dated `benchmarks/results/YYYY-MM-DD/` directory.
7. Update `CHANGELOG.md` when runtime or distribution behavior changes.

## Pull request gate

- Skill structure and distribution manifests validate.
- Unit tests pass on supported Python versions.
- New behavior has a regression test or an explained exception.
- Runtime files contain no private absolute paths, credentials, project names, or benchmark answers.
- Existing benchmark evidence remains immutable.
