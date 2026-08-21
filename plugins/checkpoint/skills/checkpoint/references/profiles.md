# Checkpoint profiles

Profiles extend the canonical template. Never infer facts that are unavailable.

## Precedence when evidence for more than one profile is present

A task can carry evidence for more than one profile at once (researched a library, then implemented it; deployed a service by editing its repo). Pick the profile by what `Next action` actually is, not by which evidence class appeared first or has the most evidence:

- `Next action` is a code/build/test step → `developer`, even if research evidence exists earlier in the task.
- `Next action` is resolving an open question or checking a source → `research`, even after code changes already happened.
- `Next action` is a service/process/diagnostic step → `operations`.

Never blend two profiles' extra fields into one checkpoint — pick one. If `Next action` genuinely spans two kinds of work equally, use `generic` rather than guessing.

**Worked example**: evaluated two rate-limiting libraries (research evidence: sources compared, a decision made), then started wiring the chosen one into the request middleware, and `Next action` is "finish wiring `RateLimiter.acquire()` into `middleware/throttle.py` and rerun `pytest tests/middleware/`." The next action is a code step, so this is `developer` — the research decision that preceded it becomes a fact under `Decision/learning`, not a reason to pick `research`.

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
