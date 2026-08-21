---
name: checkpoint
description: Capture concise, evidence-backed, resumable task state before switching context, pausing, handing off, compacting a long chat, ending a session, or moving between projects or agents. Also use when the user asks to save state, resume later, record an open loop, prepare a handoff, or avoid losing context. Recommend it when reconstruction would take more than five minutes; request permission before unsolicited persistent writing.
---

# Checkpoint

Capture operational state, not a conversation transcript.

## Decide

Recommend a checkpoint when unfinished work would take more than five minutes to reconstruct, especially before a project/agent switch, pause, handoff or compaction. Skip simple Q&A and completed work with no follow-up.

If checkpointing was not explicitly requested, explain why it helps, propose a destination and ask before persistent writing. If requested, write it directly.

## Choose destination

Prefer:

1. existing project checkpoint or project note;
2. today's Daily note for cross-project state;
3. a dedicated handoff note;
4. chat-only output when storage is unavailable or declined.

Keep transient state out of the durable knowledge Wiki. Promote only verified reusable learning.

## Choose scope and role

Resolve `scope` (`project` default, or `global`) and `role` (free text) once per project, then reuse silently — never re-ask or re-infer after they are recorded. An explicit `--scope` or `--role` flag on the invocation overrides and re-persists the value for this project. On first run with nothing recorded, resolving these never blocks or delays writing the checkpoint itself: write it now with the defaults, and ask the one scope/role question alongside it, not instead of it. Read `references/scope-and-role.md` for the full resolution order, the `.checkpoint/config.md` format, `.gitignore` handling, and the `--trigger` provenance flag.

## Select profile

Use `generic` unless evidence supports a more specific profile. Repository, branch, source path, test or migration evidence selects `developer`; services, processes or machine metrics select `operations`; research questions, claims or sources select `research`. When evidence for more than one profile is present, the profile is decided by `Next action`, not by which evidence appeared first or is most abundant — see `references/profiles.md` for the precedence rule and a worked example. Read `references/profiles.md` when the profile adds details not covered below. Profiles add fields; they never remove the canonical core.

## Gather evidence

Capture objective, scope, current state, last verified evidence, relevant files/processes, exact next action, blocker/risk and done gate. Label uncertainty. Never invent tests, paths, branches, processes or completion.

## Write

Use `assets/checkpoint-template.md`. Keep it scannable in under one minute.

Write generated checkpoint documents in the language used by the user in the
current request, unless the user explicitly requests another language. Keep
technical identifiers, paths, commands, branch names, and error messages
verbatim.

When the user explicitly invokes the skill, including `$checkpoint`, `/checkpoint` or a host-namespaced form such as `$checkpoint:checkpoint` or `$checkpoint:save`, always render the full canonical template, including for chat-only output. Do not collapse it into a summary or rename, merge or omit required headings. Profile-specific fields may say `Unknown` when evidence is unavailable; keep the field so absence is explicit. Preserve exact paths, commands, branch names, failure messages and prohibition wording verbatim when supplied.

For developer checkpoints, always include `Working directory`, `Branch`, `Changed files`, test evidence and `Resume command`; write `Unknown` for any missing fact. Keep each prohibition on one line beginning `- Do not:` so boundaries remain searchable and unambiguous.

Required sections:

- Outcome
- Scope and boundaries
- Current state
- Last verified evidence
- Files, artifacts and processes
- Next action
- Blocker or risk
- Done when

Add decisions and a resume command only when useful. Label important open loops:

- `promote`: proven and ready to become a current standard;
- `park`: intentionally paused with reason and revisit condition;
- `archive`: closed, superseded or historical only.

## Update

Update the active checkpoint instead of creating duplicates. Preserve verified facts and explicitly replace stale operational state. Link persistent checkpoints from their project, Daily note or MOC.

## Quality gate

Before finishing, ensure a fresh agent can answer:

1. What outcome is pursued?
2. What is true now and how was it verified?
3. What must not change?
4. What exact action comes next?
5. What proves completion?

If any answer is missing, the checkpoint is not resumable.
