---
description: Capture evidence-backed task state for reliable resume, handoff, or context switching
argument-hint: "[--scope project|global] [--role <text>] [--trigger manual|post-commit|post-push|stop|pre-compact] [optional note, e.g. why you're checkpointing or a destination hint]"
allowed-tools: Read, Write, Edit
---

The user explicitly invoked the checkpoint save command. Follow the host-neutral save skill below in full, then write the checkpoint now.

@${CLAUDE_PLUGIN_ROOT}/skills/save/SKILL.md

Additional context from the user for this invocation, if any: $ARGUMENTS
