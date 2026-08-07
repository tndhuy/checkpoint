# Automated triggers

`docs/DISTRIBUTION.md` sets the bar: *"Do not publish hooks, MCP servers, telemetry, network access, or autonomous writes unless a release has a documented need and threat review."* This document is that documentation for checkpoint auto-triggers.

The plugin itself ships no hook and no trigger logic. Everything below is opt-in material you wire into your own host config; the checkpoint skill only reacts to the resulting `$checkpoint:save --trigger ...` invocation, the same way it reacts to a manually typed one.

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

**Not recommended:** a native `PostToolUse` hook duplicating the commit/push match Tier 1 already covers with less code.

## The `--trigger` flag

Whichever tier fires, the resulting invocation should pass `--trigger manual|post-commit|post-push|stop|pre-compact` to `save` so the checkpoint records why it exists — see `references/scope-and-role.md` in the `checkpoint` skill.
