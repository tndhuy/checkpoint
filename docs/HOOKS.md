# Automated triggers

`docs/DISTRIBUTION.md` sets the bar: *"Do not publish hooks, MCP servers, telemetry, network access, or autonomous writes unless a release has a documented need and threat review."* This document is that documentation for checkpoint auto-triggers.

**As of 0.1.9, Tier 2 below is shipped** (`plugins/checkpoint/hooks/hooks.json`) — a knowing exception to "ships no hook and no trigger logic," accepted for this personal-scope install (not published to a public marketplace). Threat review: the two hooks capable of acting (`SessionStart`, `Stop`) only ever emit a reminder or a block `reason` string — no filesystem write, no network access, no autonomous save; the checkpoint skill only reacts to the resulting explicit `$checkpoint:save --trigger ...` invocation, the same way it reacts to a manually typed one. As of 0.1.21 this no longer holds without exception: `waypoint-writer.js` does write to the filesystem — never a checkpoint file, only its own append-only `.jsonl`/`.consumed` files under `~/.claude/checkpoint-skill/waypoints/` — see the "Waypoint capture" section below for that write's full threat review. Tier 1 (`hookify`) remains available and unaffected.

## Tier 1 — `hookify`, message-only (preferred)

If the `hookify` plugin is installed on your host, a rule file is enough — no code, no new permission surface, removable by deleting one file.

`.claude/hookify.suggest-checkpoint.local.md`:

```markdown
---
name: suggest-checkpoint
enabled: true
event: bash
pattern: git\s+(commit|push)
action: warn
---

You just ran a `git commit`/`git push`. Consider `$checkpoint:save --trigger post-commit`
(or `post-push`) if this closes out a chunk of work worth being able to resume from.
```

This is preferred over a native hook for the commit/push case specifically because `hookify`'s `bash` event matches directly on the command text (`pattern` against the `command` field). A native `PostToolUse` hook only matches on tool name (`Bash`, `Edit`, ...); isolating `git commit` specifically would require a wired script that greps the command itself — strictly more code for the same result.

`hookify` has no built-in cooldown. The rule fires on every matching command; since it only shows a message (`action: warn`), that is cheap enough to leave as-is.

## Tier 2 — native plugin hook (only if Tier 1 isn't enough)

Use this only if a passive reminder proves insufficient and the ask becomes "the agent should actually reason about whether to checkpoint," not just be nudged. Two events, chosen because each maps to a behavior the `checkpoint` skill already promises but currently has no enforcement path for:

- **`Stop`** — before the agent ends a turn, check for uncommitted work or an open next-action with no recent checkpoint. If found, surface the skill's existing recommend-and-ask flow (*"explain why it helps, propose a destination and ask before persistent writing"*) instead of silently ending.
- **`PreCompact`** — the skill's own description already lists compaction as a trigger moment. This is the only reliable way to guarantee that fires, since the agent has no dependable way to notice compaction is imminent from inside the conversation.

A wired script for either event should inject a reminder for the agent to weigh — mirroring the exact shape of this host's own idle-nudge hooks (for example, a reminder to use task-tracking tools after they've gone unused for a while). It must never write a checkpoint file on its own: the skill's core safety property is "ask before persistent writing" unless explicitly invoked, and an auto-writing hook breaks that.

Any cooldown/debounce (to avoid nagging on every `Stop`) belongs inside the wired script itself — compare the most recent checkpoint's timestamp to now and skip the reminder if it's recent. Neither `hookify` nor the native hook schema has this built in.

**Resolved in 0.1.13** (was a known limitation from 0.1.9 through 0.1.12): real-world use surfaced `Stop` blocking too often — several other host plugins also register `Stop` hooks, so a session can see many `Stop` events close together, and `stop-checkpoint.js` blocked on every one not already covered by the same-turn `stop_hook_active` guard. `hooks/stop-checkpoint.js` now implements the cooldown this section originally called for, but deliberately not via checkpoint-timestamp diffing (that would need the script to know where checkpoints live, replicating scope/role resolution logic outside the skill) — instead it tracks its own last-blocked-at time in a tmp-dir marker file and skips repeat blocks within a 20-minute window. The `reason` text was also shortened; the triviality judgment ("skip trivial completed Q&A") stays, just more tersely. `PreCompact` fires once per compaction and still needs no cooldown.

**Resolved in 0.1.17**: `stop-checkpoint.js` forced the extra turn via `decision: "block"` + `reason`, which Claude Code's transcript renders as a `<hook name> hook error` notice — confusing, since the hook was working exactly as designed, not failing. Per Claude Code's own hooks reference (Stop decision control section), `hookSpecificOutput.additionalContext` forces the same extra turn through the same loop protections (`stop_hook_active`, the continuation cap) but is labeled "Stop hook feedback" instead. Switched to that field; no behavior change beyond the transcript label.

**Not recommended:** a native `PostToolUse` hook duplicating the commit/push match Tier 1 already covers with less code.

## Waypoint capture (mechanical, async, additive)

As of 0.1.21, a fourth Tier-2 script, `waypoint-writer.js`, is registered as a *second, independent* entry under both `Stop` and `PreCompact` — alongside, not replacing, `stop-checkpoint.js` and `pre-compact-reminder.js`. Unlike those two, it never surfaces a message: it silently appends `{timestamp, cwd, branch, headSha, headMessage, statusShort}` — read straight from local `git` output, no LLM, no judgment — to `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl` (`<slug>` = the project's absolute path with every `/` replaced by `-`). `save` later reads this file as optional evidence for the mechanically-derivable parts of a checkpoint; see `skills/save/SKILL.md`'s "Waypoint evidence" section and `docs/superpowers/specs/2026-09-11-checkpoint-waypoint-design.md` for the full design.

**Threat review** (per this file's own opening bar — "documented need and threat review" for any autonomous write):

- **What is written:** exactly the six mechanical fields above, sourced from local `git` command output only. No user input, no LLM output, and no conversational content ever reaches this file.
- **Where it is written:** `~/.claude/checkpoint-skill/waypoints/` only — never inside the project tree, under either `scope`. The hook never resolves `scope`/`role` at all, sidestepping the `scope: global` "write nothing inside the project" invariant entirely rather than special-casing it.
- **What it cannot do:** write, modify, or delete a checkpoint file. It writes to a different file in a different location that `save` treats as optional evidence, never as an alternative destination.
- **Failure mode:** fail-open. A failed or missing waypoint write degrades `save` to exactly its pre-0.1.21 behavior — `save` already handles "no waypoints found" as its default path.
- **Kill switch:** `hooks_enabled: false` disables it exactly like the other three Tier-2 hooks (same shared `lib/read-project-config.js` check) — no separate, harder-to-discover toggle. That said, under `scope: global` (see `references/scope-and-role.md`) none of the four Tier-2 hooks has a documented way to reach this toggle at all: `lib/read-project-config.js` only ever resolves `.checkpoint/config.md` inside the current project directory, with no fallback to a global config — a pre-existing gap, not introduced by this hook.

Deduping compares `headSha` + `branch` + `statusShort` against the log's last line, so repeated `Stop` fires with no intervening change never grow the file — this also catches a checkout to a different branch pointing at the same commit. The file is strictly append-only; `save` tracks its own read progress in a sibling `.consumed` marker (a plain line count) rather than mutating the log.

## Per-project settings

`.checkpoint/config.md` (see `assets/scope-config-template.md` in the `checkpoint` skill) accepts two optional fields, hand-added — `save` never writes them itself:

- `hooks_enabled: true|false` — `false` silences all Tier-2 hooks for this project: `stop-checkpoint.js` (`Stop`), `pre-compact-reminder.js` (`PreCompact`), `post-compact-checkpoint.js` (`SessionStart`), and `waypoint-writer.js` (`Stop`/`PreCompact`). Default `true`.
- `stop_cooldown_minutes: N` — overrides the `Stop` hook's cooldown window (see above). `0` means never suppress a repeat block. Default `20`.

Both read via `plugins/checkpoint/hooks/lib/read-project-config.js`, which fails open to the defaults above on a missing file, missing field, or malformed value — a broken config can never make a hook behave worse than it did before this file existed. `post-compact-checkpoint.js` needs `cwd` (only available via stdin) to locate the config, so it now waits on a stdin read before emitting; an empty/unparseable/timed-out stdin still emits its reminder unconditionally, same as before this feature existed.

## The `--trigger` flag

Whichever tier fires, the resulting invocation should pass `--trigger manual|post-commit|post-push|stop|pre-compact` to `save` so the checkpoint records why it exists — see `references/scope-and-role.md` in the `checkpoint` skill.
