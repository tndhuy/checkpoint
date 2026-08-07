---
name: recall
description: Find and load the most relevant saved checkpoint, verify stale evidence, and prepare the exact next resume action. Use when the user invokes $checkpoint:recall or asks to resume saved checkpoint work.
---

# Recall checkpoint

Locate and load one checkpoint to resume work from. Search both standalone `type: checkpoint` files and headings containing `checkpoint` inside larger project or Daily notes.

Accept `--scope project|global` to narrow the search to one location when a project has checkpoints recorded in both (uncommon, but possible after a scope change).

Use any project, title, or path hint included with the invocation. Otherwise prefer an active checkpoint matching the current project or working directory, then the most recently updated candidate. If multiple candidates remain plausible, ask exactly one multiple-choice question in the user's language and stop before reading further.

Read the chosen checkpoint in full. Before taking action, report concise answers to these questions:

1. What outcome is pursued?
2. What is true now, and how was it verified?
3. What must not change? Treat every `Do not:` line as a hard constraint.
4. What exact action comes next?
5. What proves completion?

Surface a filled `Resume command` as a copyable command instead of running it unprompted. If dates, branch, running processes, or other evidence may be stale, say so and re-verify before treating them as current.
