---
name: save
description: Save the current task as an evidence-backed checkpoint for reliable resume, handoff, or context switching. Use when the user invokes $checkpoint:save or explicitly asks to save checkpoint state now.
argument-hint: "[--scope project|global] [--role <text>] [--trigger manual|post-commit|post-push|stop|pre-compact] [optional note, e.g. why you're checkpointing or a destination hint]"
allowed-tools: Read, Write, Edit
---

# Save checkpoint

Capture operational state, not a conversation transcript. The user explicitly invoked save: write the checkpoint now instead of summarizing this process.

## Destination

Prefer an existing project checkpoint or project note, today's Daily note for cross-project state, a dedicated handoff note, then chat-only output when storage is unavailable. Update an active checkpoint instead of creating a duplicate. Keep transient state out of durable knowledge stores.

## Scope, role, and trigger flags

Accept `--scope project|global` and `--role <text>` on this command. Resolve both per `../checkpoint/references/scope-and-role.md`: an explicit flag overrides and re-persists the value for this project; otherwise reuse a previously recorded value silently; otherwise ask once — **this resolution never blocks or delays writing the checkpoint** (read that file for the full resolution order and first-run behavior). Accept `--trigger manual|post-commit|post-push|stop|pre-compact` (default `manual`) to record why this save is happening, without affecting scope or role.

## Profile and evidence

Use `developer` when repository, branch, source, test, build, migration, or runtime evidence exists; `operations` for services and machine state; `research` for claims and sources; otherwise `generic`. When evidence for more than one profile is present, see `../checkpoint/references/profiles.md` for the precedence rule and a worked example — do not guess or blend fields from two profiles.

Capture only verified facts: outcome, scope, current state, last verified evidence, relevant files or processes, exact next action, blocker or risk, and the done gate. Label unknown or stale facts. Never invent tests, paths, branches, processes, or completion.

For a developer checkpoint, always include `Working directory`, `Branch`, `Changed files`, test/build/runtime evidence, and `Resume command`; write `Unknown` for missing facts. Preserve each hard boundary on its own line beginning `- Do not:`.

## Required output

Write the generated checkpoint document in the language used by the user in
the current request, unless the user explicitly requests another language.
Keep technical identifiers, paths, commands, branch names, and error messages
verbatim.

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

Before finishing, verify that a fresh agent can answer: what outcome is pursued, what is true and how it was verified, what must not change, what action comes next, and what proves completion.
