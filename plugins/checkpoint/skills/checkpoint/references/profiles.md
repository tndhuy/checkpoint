# Checkpoint profiles

Profiles extend the canonical template. Never infer facts that are unavailable.

## Generic

Use for mixed or unknown work. Keep only the canonical sections.

## Developer

Add repository, branch/worktree, changed files, tests/build/runtime evidence, processes, safety boundaries and exact resume command.

## Research

Add research question, sources checked, verified claims, hypotheses, open questions, citation state and next source/action.

## Operations

Add environment, services/processes, observed metrics, commands already run, risk boundary, rollback/recovery action and the next safe diagnostic.

## Storage fallback

When no persistent storage is configured, return a copyable `generic + chat-only` checkpoint. Never silently authorize file writes from profile detection.
