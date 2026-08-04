---
name: list
description: List saved checkpoints by project, title, status, or path without loading full checkpoint contents. Use when the user invokes $checkpoint:list or asks what checkpoints are available.
---

# List checkpoints

Find and summarize existing checkpoints. Do not read full contents unless needed to disambiguate; frontmatter and the title line are enough.

Search the current project's checkpoint or notes location, recent Daily notes when a notes vault is in use, and dedicated handoff notes. Match both standalone files whose frontmatter contains `type: checkpoint` and headings containing `checkpoint` inside larger notes. Do not filter by file-level `type` alone.

Apply any project, title, or path hint included with the invocation. Report the most recently updated active checkpoints first. For each match, show the available project, branch, status, updated date, title, and enough path to select it unambiguously.

If nothing is found, say so and suggest `$checkpoint:save`; never invent checkpoints.
