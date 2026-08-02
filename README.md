# Checkpoint Skill

Agent-neutral workflow for capturing concise, evidence-backed task state before context switches, pauses, handoffs, compaction, or agent changes.

The repository ships both an open Agent Skills-compatible skill and installable Codex/Claude plugin packages.

## Layout

- `plugins/checkpoint-skill/` — distributable plugin root.
- `plugins/checkpoint-skill/skills/checkpoint/` — portable runtime skill.
- `.agents/plugins/marketplace.json` — Codex marketplace.
- `.claude-plugin/marketplace.json` — Claude Code marketplace.
- `scripts/` and `tests/` — deterministic quality gates.
- `benchmarks/` — fixtures and dated behavioral evidence.

## Verify

```bash
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint-skill
```

Codex's plugin manifest is validated with the built-in `plugin-creator` validator during release preparation.

## Install from a local checkout

### Codex

```bash
codex plugin marketplace add /absolute/path/to/checkpoint-skill
codex plugin add checkpoint-skill@checkpoint-skill-local
```

Start a new task after installation.

### Claude Code

```bash
claude plugin marketplace add /absolute/path/to/checkpoint-skill
claude plugin install checkpoint-skill@checkpoint-skill
```

Restart Claude Code after installation.

### Direct skill discovery

Hosts supporting the open Agent Skills layout can point their discovery directory at:

```text
plugins/checkpoint-skill/skills/checkpoint
```

## Evidence

The 2026-08-02 isolated-agent benchmark passed developer, research, and operations fixtures. Checkpoint resumes asked 5 reconstructive questions versus 14 for raw-state baselines. See `benchmarks/results/2026-08-02/report.md`.

Host-native marketplace installation is verified for Codex and Claude at version `0.1.0`. An isolated fresh Codex run loaded the tracked skill and scored 19/19. Automatic Codex discovery on the author's full profile is currently obscured by that profile exceeding the host skill-context budget; Claude runtime execution is blocked by an expired OAuth session. See `benchmarks/results/2026-08-02/host-install-smoke.md`.

This is same-run isolated-context evidence. Clean-profile discovery and a multi-day real-project handoff remain the next validation tiers.

## License

MIT
