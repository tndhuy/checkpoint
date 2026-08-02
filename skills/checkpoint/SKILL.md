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

## Select profile

Use `generic` unless evidence supports a more specific profile. Read `references/profiles.md` when applying `developer`, `research` or `operations`. Profiles add fields; they never remove the canonical core.

## Gather evidence

Capture objective, scope, current state, last verified evidence, relevant files/processes, exact next action, blocker/risk and done gate. Label uncertainty. Never invent tests, paths, branches, processes or completion.

## Write

Use `assets/checkpoint-template.md`. Keep it scannable in under one minute. Required sections:

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
