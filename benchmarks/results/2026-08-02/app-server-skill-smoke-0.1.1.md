# Codex app-server skill smoke — 0.1.1

Date: 2026-08-02

## Why this supersedes the text-only probe

Codex skill invocation is structured input. The app sends the user text plus a `type: skill` item containing the skill name and absolute `SKILL.md` path. A literal `$checkpoint` string passed to `codex exec` does not reproduce that protocol, so the text-only result in `host-install-smoke.md` cannot establish discovery or skill behavior.

## Method

1. Start an ephemeral Codex app-server thread.
2. Set read-only sandbox, no approvals, no network and no orchestrator MCP.
3. Send the developer fixture as text.
4. Attach the tracked checkpoint `SKILL.md` as a `type: skill` input item.
5. Capture the final agent message.
6. Score it with `scripts/evaluate_checkpoint.py` and the developer expectations fixture.

Command:

```bash
node scripts/smoke_codex_app_server.mjs \
  plugins/checkpoint-skill/skills/checkpoint/SKILL.md \
  benchmarks/fixtures/developer/task.md \
  /tmp/checkpoint-app-server.md

python3 scripts/evaluate_checkpoint.py \
  /tmp/checkpoint-app-server.md \
  benchmarks/fixtures/developer/expected.json
```

## Result

- App-server turn: completed.
- Required headings: 8/8.
- Developer profile concepts: 5/5.
- Expected task facts: 6/6.
- Deterministic score: 19/19.
- File writes by agent: none.
- Tools used by agent: none.

## Regression found and fixed

The first generic fixture run scored 17/19 because changed-file absence was omitted and a prohibition was split into wording that was no longer searchable as `do not change public response shape`. Version 0.1.1 now requires developer checkpoints to record `Changed files: Unknown` when necessary and keep each prohibition on a single `Do not:` line.

## Remaining validation

- Restore Claude OAuth and run the equivalent no-tool Claude plugin test.
- Measure one multi-day real-project handoff rather than only same-run reconstruction.
