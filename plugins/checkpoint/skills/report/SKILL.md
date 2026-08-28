---
name: report
description: Persist a detailed, evidence-backed completion report for a finished substantive task — what was achieved and why, technique/algorithm assessment, diff highlights, and optional ELI5/glossary/further-research sections. Use when the user invokes $checkpoint:report, or proactively propose it right after finishing a substantive task (feature shipped, bug fixed, investigation concluded) the same way checkpoint proposes itself for unfinished state.
argument-hint: "[--scope project|global] [--role <text>] [optional note]"
allowed-tools: Read, Write, Edit
---

# Report — completion report

Persist an immutable retrospective for a finished task. Never edit or overwrite a written report — every report is a new file.

## Decide

Recommend a report right after finishing a substantive task whose rationale, technique, or diff would take real work to reconstruct later — a shipped feature, a fixed bug, a concluded investigation. Skip trivial completed Q&A.

If not explicitly requested, explain why it helps, propose the destination (`.checkpoint/reports/<date>-<slug>.md`) and ask before persisting. If the user explicitly invokes `$checkpoint:report`, write it directly instead of summarizing this process.

## Scope and role

Resolve `scope` (`project` default, or `global`) and `role` exactly as `save` does — see `../checkpoint/references/scope-and-role.md`. Reuse the same `.checkpoint/config.md` (or global config) already recorded for this project; never re-ask once a value exists. An explicit `--scope`/`--role` flag on this invocation overrides and re-persists the value for this project.

## Profile

Resolve exactly as `save` does — see `../checkpoint/references/profiles.md`. Use `developer` when repository, branch, test, or build evidence exists for the finished task; `operations`/`research` per their usual triggers; otherwise `generic`.

## Gather evidence

Capture only what's actually true: real alternatives actually considered (never invent one that wasn't weighed), the real technique or pattern applied, the real files changed, and a genuine one-line lesson learned. Never invent a lesson, an alternative, or a review-attention flag that has no basis in the actual work.

## Write

Use `../checkpoint/assets/report-template.md` as the exact skeleton, including its YAML frontmatter (`type: report`, `created`, `profile`, `scope`, `role`, `project`, `branch`, `related_checkpoint`). Name the file `<YYYY-MM-DD>-<slug>.md` under `.checkpoint/reports/` (or the equivalent path under the resolved global root), where `slug` is a short kebab-case rendering of the task title. On a same-day slug collision, append `-2`, `-3`, etc. — never overwrite an existing report.

If an active checkpoint for this project exists, set `related_checkpoint` to its path relative to the report; otherwise leave it `""`. Write `Unknown` for any fact that cannot be verified (e.g. `branch` when the project has no `.git`); never leave a template default in place.

Write the report in the language used by the user in the current request, unless the user explicitly requests another language — the same rule centralized in `../checkpoint/SKILL.md`. Keep technical identifiers, paths, commands, branch names, and error messages verbatim. Keep the template's heading names verbatim regardless of the report's language; only the body text follows the user's language.

Omit the `ELI5`, `Ghi chú thuật ngữ`, and `Đề xuất mở rộng` headings entirely when they don't apply to this task — don't pad a report with a heading that has nothing under it.

## Quality gate

Before finishing, verify: does this report let someone who wasn't here understand what happened and why, without re-deriving it from the diff themselves? If not, the report is incomplete.
