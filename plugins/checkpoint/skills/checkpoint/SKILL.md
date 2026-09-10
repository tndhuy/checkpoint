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

Resolve the checkpoint's prose language per `references/scope-and-role.md`'s
Language section: a persisted `language` value (once set) wins even when the
surrounding session's working language differs — a checkpoint is read back by
the same person later, not by whichever language one technical request
happened to be phrased in. Only fall back to the language used in the current
request when nothing is persisted yet. This applies to prose and narrative
content even when the surrounding session is technical or predominantly in
another language (e.g. a one-line Vietnamese request about an English
codebase still gets a Vietnamese checkpoint) — do not default to English just
because the work discussed is technical. Keep technical identifiers, paths,
commands, branch names, and error messages verbatim regardless of language.

This same rule governs every other document, report, or chat response this
skill or its sub-skills (`save`, `recall`, `list`, `report`) produce — not
only the checkpoint document itself.

When the user explicitly invokes the skill, including `$checkpoint`, `/checkpoint` or a host-namespaced form such as `$checkpoint:checkpoint` or `$checkpoint:save`, always render the full canonical template, including for chat-only output. Do not collapse it into a summary or rename, merge or omit required headings. Profile-specific fields may say `Unknown` when evidence is unavailable; keep the field so absence is explicit. Preserve exact paths, commands, branch names, failure messages and prohibition wording verbatim when supplied.

A hook-triggered invocation (`--trigger stop`, `pre-compact`, `post-commit`, or `post-push` — the model acting on an automated nudge, not the user typing the command) still writes the full canonical template to the file exactly as above, but the chat response collapses to one line: `Checkpoint saved to <path>.` Do not re-render the full template in chat, and do not redo, re-verify, or re-narrate work already completed and reported to the user this session — the hook is asking for persistence, not a fresh report. Reserve full chat rendering for an invocation the user actually typed.

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

Add decisions and a resume command only when useful — except for developer checkpoints, where `Resume command` is always required per the line above. Label important open loops:

- `promote`: proven and ready to become a current standard;
- `park`: intentionally paused with reason and revisit condition;
- `archive`: closed, superseded or historical only.

## Update

Update the active checkpoint instead of creating duplicates. Preserve verified facts and explicitly replace stale operational state — but "replace" means the specific line whose underlying fact changed, not the section around it. Before writing, diff the new facts against what the existing file already says: if a fact carried over unchanged (an `Allowed`/`Do not` boundary, a `Done when` item still pending, a `park`ed open loop nobody acted on), keep its existing wording verbatim instead of re-narrating it in fresh prose. Regenerating a whole section on every update — even when only one bullet in it actually changed — is the failure mode this rule exists to prevent: a checkpoint whose diff is nearly the full file on every save has stopped being reliably scannable, which defeats its purpose. Link persistent checkpoints from their project, Daily note or MOC.

Keep narrative sections short enough to hold in working memory on one read: `Next action`, `Blocker or risk`, `Decision/learning`, and `Current state` each stay under roughly 5 lines / ~500 characters. If a fact genuinely needs more than that to state accurately, that's a signal to split it into its own note (project note, Daily note, or a verified Wiki synthesis) and link it — not to let the checkpoint itself grow. "Scannable in under one minute" is the target; this length ceiling is what keeps that target enforceable instead of aspirational.

## Quality gate

Before finishing, ensure a fresh agent can answer:

1. What outcome is pursued?
2. What is true now and how was it verified?
3. What must not change?
4. What exact action comes next?
5. What proves completion?

If any answer is missing, the checkpoint is not resumable.
