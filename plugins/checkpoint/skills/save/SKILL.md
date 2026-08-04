---
name: save
description: Save the current task as an evidence-backed checkpoint for reliable resume, handoff, or context switching. Use when the user invokes $checkpoint:save or explicitly asks to save checkpoint state now.
---

# Save checkpoint

Capture operational state, not a conversation transcript. The user explicitly invoked save: write the checkpoint now instead of summarizing this process.

## Destination

Prefer an existing project checkpoint or project note, today's Daily note for cross-project state, a dedicated handoff note, then chat-only output when storage is unavailable. Update an active checkpoint instead of creating a duplicate. Keep transient state out of durable knowledge stores.

## Profile and evidence

Use `developer` when repository, branch, source, test, build, migration, or runtime evidence exists; `operations` for services and machine state; `research` for claims and sources; otherwise `generic`.

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

Use this exact skeleton. Keep every shown heading and developer field:

````markdown
# Checkpoint — <task or outcome>

## Outcome

## Scope and boundaries
- Allowed:
- Do not:

## Current state

## Last verified evidence
- Check/test/runtime:
- Result:

## Files, artifacts and processes
- Working directory:
- Branch:
- Changed files:
- Running processes/sessions:

## Next action
1.

## Blocker or risk

## Done when
- [ ]

## Decision/learning

## Open-loop lifecycle
- `promote` | `park` | `archive` — item, reason, and revisit condition if parked

## Resume command
```sh
# exact command, or Unknown
```
````

Before finishing, verify that a fresh agent can answer: what outcome is pursued, what is true and how it was verified, what must not change, what action comes next, and what proves completion.
