# Distribution

## Package model

The repository is a marketplace root. The installable plugin lives at `plugins/checkpoint/`; the portable Agent Skill lives one level below at `skills/checkpoint/`.

This avoids maintaining separate Codex, Claude, and generic copies. Every host resolves to the same tracked `SKILL.md`.

## Local release check

```bash
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint
```

Also run OpenAI's plugin validator:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/checkpoint
```

Run the real Codex host smoke test when Codex is installed and authenticated:

```bash
node scripts/smoke_codex_app_server.mjs \
  plugins/checkpoint/skills/checkpoint/SKILL.md \
  benchmarks/fixtures/developer/task.md \
  /tmp/checkpoint-app-server.md

python3 scripts/evaluate_checkpoint.py \
  /tmp/checkpoint-app-server.md \
  benchmarks/fixtures/developer/expected.json
```

Typing `$checkpoint` into `codex exec` is not an equivalent smoke test. The desktop app invokes a skill by sending both text and a `type: skill` input item containing its name and absolute `SKILL.md` path; the harness reproduces that protocol.

## Versioning

Use semantic versioning. Keep these values identical:

- `pyproject.toml`
- `plugins/checkpoint/.codex-plugin/plugin.json`
- `plugins/checkpoint/.claude-plugin/plugin.json`

Codex discovers the plugin's `skills/` directory and exposes `$checkpoint:checkpoint`, `$checkpoint:save`, `$checkpoint:list`, and `$checkpoint:recall`. Claude Code continues to expose `/checkpoint:save`, `/checkpoint:list`, and `/checkpoint:recall` from `commands/`.
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
