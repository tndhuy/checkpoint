# Checkpoint Skill

Agent-neutral workflow for capturing concise, evidence-backed task state before context switches, pauses, handoffs, compaction, or agent changes.

The repository ships both an open Agent Skills-compatible skill and installable Codex/Claude plugin packages.

## Layout

- `plugins/checkpoint/` — distributable plugin root and `checkpoint` namespace.
- `plugins/checkpoint/skills/checkpoint/` — portable runtime skill.
- `.agents/plugins/marketplace.json` — Codex marketplace.
- `.claude-plugin/marketplace.json` — Claude Code marketplace.
- `scripts/` and `tests/` — deterministic quality gates.
- `benchmarks/` — fixtures and dated behavioral evidence.

## Verify

```bash
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint
```

Codex's plugin manifest is validated with the built-in `plugin-creator` validator during release preparation.

## Install from a local checkout

### Codex

```bash
codex plugin marketplace add /absolute/path/to/checkpoint-skill
codex plugin add checkpoint@checkpoint-skill-local
```

Start a new task after installation.

Codex exposes these namespaced skills:

- `$checkpoint:save` — save the current task state.
- `$checkpoint:list` — list saved checkpoints.
- `$checkpoint:recall` — load and resume a checkpoint.
- `$checkpoint:checkpoint` — invoke the portable canonical workflow directly.

### Claude Code

```bash
claude plugin marketplace add /absolute/path/to/checkpoint-skill
claude plugin install checkpoint@checkpoint-skill
```

Restart Claude Code after installation.

### Direct skill discovery

Hosts supporting the open Agent Skills layout can point their discovery directory at:

```text
plugins/checkpoint/skills/checkpoint
```

## Evidence

The 2026-08-02 isolated-agent benchmark passed developer, research, and operations fixtures. Checkpoint resumes asked 5 reconstructive questions versus 14 for raw-state baselines. See `benchmarks/results/2026-08-02/report.md`.

Host-native marketplace installation is verified for Codex and Claude. Version `0.1.1` adds a real Codex app-server smoke test: it attaches `SKILL.md` as a `type: skill` input item, matching the desktop app protocol, and scores 19/19 against the developer contract. See `benchmarks/results/2026-08-02/app-server-skill-smoke-0.1.1.md`.

Version `0.1.4` adds Codex-native `$checkpoint:save`, `$checkpoint:list`, and `$checkpoint:recall` skills while retaining the Claude slash commands. Static validation and local installation pass. The current local app-server ignored structured skill items during the 0.1.4 forward probe, so behavioral verification must be repeated in a fresh Codex task.

The earlier plain-text CLI probe in `host-install-smoke.md` did not attach a skill input item and is retained only as historical evidence. It must not be treated as an automatic-discovery result. Claude runtime execution remains blocked until the local OAuth session is restored.

This is same-run isolated-context evidence. A multi-day real-project handoff remains the next validation tier.

## License

MIT
