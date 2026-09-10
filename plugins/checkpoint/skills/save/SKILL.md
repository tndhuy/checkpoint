---
name: save
description: Save the current task as an evidence-backed checkpoint for reliable resume, handoff, or context switching. Use when the user invokes $checkpoint:save or explicitly asks to save checkpoint state now.
argument-hint: "[--scope project|global] [--role <text>] [--trigger manual|post-commit|post-push|stop|pre-compact] [optional note, e.g. why you're checkpointing or a destination hint]"
allowed-tools: Read, Write, Edit
---

# Save checkpoint

Capture operational state, not a conversation transcript. The user explicitly invoked save: write the checkpoint now instead of summarizing this process.

## Destination

Prefer an existing project checkpoint or project note, today's Daily note for cross-project state, a dedicated handoff note, then chat-only output when storage is unavailable. Update an active checkpoint instead of creating a duplicate, per `../checkpoint/SKILL.md`'s Update section — diff against the existing file, don't regenerate a whole section for a one-line change, and respect its per-section length ceiling. Keep transient state out of durable knowledge stores.

## Scope, role, and trigger flags

Accept `--scope project|global` and `--role <text>` on this command. Resolve both per `../checkpoint/references/scope-and-role.md`: an explicit flag overrides and re-persists the value for this project; otherwise reuse a previously recorded value silently; otherwise ask once — **this resolution never blocks or delays writing the checkpoint** (read that file for the full resolution order and first-run behavior). Accept `--trigger manual|post-commit|post-push|stop|pre-compact` (default `manual`) to record why this save is happening, without affecting scope or role.

## Waypoint evidence

Before gathering evidence, check for mechanically-captured waypoints: take this project's absolute path, replace every `/` with `-` to get `<slug>` (e.g. `/home/alice/dev/myapp` → `-home-alice-dev-myapp`), and `Read` `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl`. If it doesn't exist, skip this step entirely and proceed exactly as before this feature existed.

If it exists, also `Read` the sibling `~/.claude/checkpoint-skill/waypoints/<slug>.consumed` (treat a missing or unparseable value as `0`) and skip that many lines from the top of the `.jsonl`. If the marker's value is greater than the `.jsonl`'s current total line count, treat it as `0` too — this can only happen if the log was deleted or reset while the marker survived, and re-reading everything is the safe failure mode. Use only the remaining lines, and only for facts this skill already treats as mechanical — `Working directory`, `Branch`, `Changed files` — never for `Outcome`, `Decision/learning`, or any section requiring judgment; conversational context always wins over a stale waypoint line for those.

After the checkpoint file is written, `Write` the `.consumed` marker with the `.jsonl`'s total line count at the time it was read. Never truncate or delete the `.jsonl` itself — it stays append-only; only the marker moves.

## Profile and evidence

Use `developer` when repository, branch, source, test, build, migration, or runtime evidence exists; `operations` for services and machine state; `research` for claims and sources; otherwise `generic`. When evidence for more than one profile is present, see `../checkpoint/references/profiles.md` for the precedence rule and a worked example — do not guess or blend fields from two profiles.

Capture only verified facts: outcome, scope, current state, last verified evidence, relevant files or processes, exact next action, blocker or risk, and the done gate. Label unknown or stale facts. Never invent tests, paths, branches, processes, or completion.

For a developer checkpoint, always include `Working directory`, `Branch`, `Changed files`, test/build/runtime evidence, and `Resume command`; write `Unknown` for missing facts. Preserve each hard boundary on its own line beginning `- Do not:`.

## Required output

Resolve prose language per `../checkpoint/references/scope-and-role.md`'s
Language section: a persisted `language` value wins even when the current
request is in a different language; only fall back to the current request's
language when nothing is persisted yet. Keep technical identifiers, paths,
commands, branch names, and error messages verbatim.

Render the full canonical checkpoint with every heading below, including for chat-only output. Do not rename, merge, omit, or collapse these sections:

- Outcome
- Scope and boundaries
- Current state
- Last verified evidence
- Files, artifacts and processes
- Next action
- Blocker or risk
- Done when

Add decisions and a resume command when useful. Label open loops as `promote`, `park`, or `archive`. Keep the result scannable in under one minute. Preserve exact paths, commands, branch names, failure messages, and prohibition wording supplied by the user.

Use `../checkpoint/assets/checkpoint-template.md` as the exact skeleton — including its YAML frontmatter (`type: checkpoint`, `status`, `profile`, `scope`, `role`, `project`, `branch`, `owner`). `list` and `recall` locate and filter checkpoints by that frontmatter; omitting it makes a saved checkpoint invisible to both. Keep every shown heading and developer field; fill `profile` with the value resolved above.

A hook-triggered invocation (`--trigger stop`, `pre-compact`, `post-commit`, or `post-push` — acting on an automated nudge, not the user typing `$checkpoint:save`) still writes the full template to the file exactly as above, but the chat response collapses to one line: `Checkpoint saved to <path>.` Do not re-render the full template in chat, and do not redo, re-verify, or re-narrate work already completed and reported to the user this session — the hook is asking for persistence, not a fresh report. Reserve full chat rendering for `--trigger manual` (the default) or no flag, i.e. an invocation the user actually typed.

Before finishing, verify that a fresh agent can answer: what outcome is pursued, what is true and how it was verified, what must not change, what action comes next, and what proves completion.
