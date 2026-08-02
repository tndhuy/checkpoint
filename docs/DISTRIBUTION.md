# Distribution

## Package model

The repository is a marketplace root. The installable plugin lives at `plugins/checkpoint-skill/`; the portable Agent Skill lives one level below at `skills/checkpoint/`.

This avoids maintaining separate Codex, Claude, and generic copies. Every host resolves to the same tracked `SKILL.md`.

## Local release check

```bash
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint-skill
```

Also run OpenAI's plugin validator:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/checkpoint-skill
```

## Versioning

Use semantic versioning. Keep these values identical:

- `pyproject.toml`
- `plugins/checkpoint-skill/.codex-plugin/plugin.json`
- `plugins/checkpoint-skill/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`

The deterministic distribution validator blocks drift.

## Publish flow

1. Run all local validators and behavioral fixtures.
2. Update `CHANGELOG.md`.
3. Commit the release.
4. Create a signed or annotated `vX.Y.Z` tag.
5. Push the repository and tag.
6. Add the GitHub repository as a marketplace in Codex and Claude.
7. Install into clean host profiles.
8. Start fresh sessions and run one trigger test plus one boundary test.

Do not publish hooks, MCP servers, telemetry, network access, or autonomous writes unless a release has a documented need and threat review.
