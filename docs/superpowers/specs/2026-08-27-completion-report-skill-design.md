# Completion-report skill — design

Status: approved (chat, 2026-08-27) — pending spec self-review and user sign-off on this document.

## Background

The user's global `~/.claude/CLAUDE.md` gained a new "Task Reporting" section this session, mandating a detailed end-of-turn chat report after any substantive task: what was achieved and why (with alternatives considered), the technique/algorithm/data-structure used and whether it's optimal, a diff/breakpoint summary flagging what needs careful review, an ELI5 for non-trivial concepts, and jargon annotated via footnote/glossary/callout as appropriate.

That instruction governs live chat output, but it does not persist anywhere. The user explicitly asked (`AskUserQuestion`, 2026-08-27) for the same depth of content to also exist as a saved artifact in this plugin — a "báo cáo hoàn thành" (completion report), separate from `checkpoint` — and for it to be self-triggered automatically after a substantive task completes, not only on explicit invocation.

This is a new flow this plugin does not have today (`save`/`recall`/`list` all operate on the single mutable checkpoint stream), so per this repo's own brainstorming process it takes the Architectural path: a written spec, not just an in-chat bounded design.

## Goals

- A new skill, `report`, that persists one immutable, detailed retrospective document per completed task.
- Content mirrors CLAUDE.md's Task Reporting structure (what/why/alternatives, technique/algorithm assessment, diff highlights, optional ELI5, jargon annotations, optional further-research suggestions) so the chat report and the saved report never drift into two different shapes.
- Self-triggers the same way `checkpoint` already does: Claude proactively recommends writing one after a substantive completed task, states why, proposes a destination, and asks before persisting — never a silent auto-write. No new hook; Claude Code has no "task complete" lifecycle event, so this is judgment-driven from the skill's own `Decide` section, exactly like `checkpoint/SKILL.md` already does for state-saving.
- Reuses existing machinery: scope/role resolution (`references/scope-and-role.md`), profile precedence (`references/profiles.md`), and the same `.checkpoint/` root — no new config surface.

## Non-goals (explicitly out of scope for this pass)

- A new hook wired to any lifecycle event — rejected; see Goals above.
- Editing or revising a report after it's written — reports are immutable, one file per completed task (see "Why not fold into `save`" below). If a task's understanding changes later, that becomes a new report or a checkpoint decision note, not an edit to history.
- Cross-linking every report from a Daily note / MOC automatically — out of scope; `checkpoint/SKILL.md`'s existing "Update" section already covers linking persistent checkpoints, and this can be revisited later if reports prove to need the same treatment.
- Retention/pruning of old reports — same "keep forever for v0.1" stance as the pending checkpoint revision-history spec; revisit only on real evidence it's a problem.

## Why a separate skill, not a `save --report` flag

Rejected alternative: add a `--report` flag to `save` that writes the extra sections into the existing checkpoint file. This is simpler surface area, but it conflates two different lifecycles:

- `checkpoint` (`save`/`recall`/`list`) is a **mutable, single-active-stream** record of *unfinished* work — "update the active checkpoint instead of creating a duplicate."
- A completion report is an **immutable, one-per-task** record of *finished* work — never revised, never overwritten, one new file per completed task.

Forcing both into `save`'s single-file-per-project model would mean either overwriting historical reports (data loss) or silently changing `save`'s semantics for everyone who doesn't want reports. A separate skill keeps each flow's invariants simple and independently testable, matching this repo's existing pattern of one skill per distinct operation (`save`/`recall`/`list` are already split this way for the same reason).

## Directory and file layout

```
.checkpoint/
├── config.md
├── revisions/            (or checkpoint.md, depending on the pending revision-history spec)
└── reports/
    ├── 2026-08-27-checkpoint-revisions-design-spec.md
    └── 2026-08-27-completion-report-skill-design.md
```

**Filename format:** `<YYYY-MM-DD>-<slug>.md`, where `slug` is a short kebab-case rendering of the task title (not a sequence number — each report is a distinct, self-contained task, not a stream to revise, so there is no "next revision" concept). On a same-day slug collision (rare — two distinct completed tasks with very similar titles on one day), append `-2`, `-3`, etc.

## Frontmatter schema

```yaml
type: report
created: 2026-08-27T20:15:00+07:00   # ISO 8601 with time, same precision rationale as the pending revisions spec
profile: developer                    # generic | developer | research | operations — same precedence rule as checkpoint
scope: project                        # project | global — same resolution as checkpoint, shared config
role: ""
project: checkpoint-skill
branch: main
related_checkpoint: ""                # optional relative path to an active checkpoint this task was part of, or "" if none
```

## Template (`assets/report-template.md`)

```markdown
---
type: report
created: YYYY-MM-DDTHH:MM:SS+00:00
profile: generic
scope: project
role: ""
project: ""
branch: ""
related_checkpoint: ""
---

# Report — <task title>

## Kết quả & lý do

<What was actually accomplished. Why this approach was picked over
alternatives — name at least one alternative considered and why it lost, or
say explicitly there wasn't a real alternative.>

## Kỹ thuật đã dùng

<The algorithm / data structure / pattern applied, why it fits here, whether
it's already best practice for this case or a more optimal option exists
worth flagging, and the one-line lesson learned.>

## Thay đổi cụ thể

<What changed, file by file if more than one was touched. Call out
explicitly which parts need careful review (risky, non-obvious, or
hard-to-reverse) versus which are routine.>

## ELI5

<Optional — only for genuinely non-trivial concepts. Omit this heading
entirely if nothing in the task needs it; don't force a trivial restatement.>

## Ghi chú thuật ngữ

<Optional. Footnote (¹ ² *) for a term used once or twice, inline with a
one-line explanation right after. Glossary (term → definition list) only
when 4+ new terms appear. Callout/sidebar (`> [!NOTE]`) for a tangential
explanation that would break the main narrative if inlined. Omit this
heading if nothing needs annotating.>

## Đề xuất mở rộng

<Optional. Further research or practical extensions worth considering later.
Omit if none.>
```

Unlike the canonical checkpoint template, `ELI5`, `Ghi chú thuật ngữ`, and `Đề xuất mở rộng` are conditionally omitted headings, not always-rendered-with-"Unknown" fields — they mirror CLAUDE.md's own "skip this structure for trivial replies" / "omit if none" framing, since forcing them onto every report would fight the "genuinely non-trivial" gate that section already has in chat.

## Component: `report` (`plugins/checkpoint/skills/report/SKILL.md`)

New skill file, siblings of `save`/`recall`/`list`/`checkpoint`. Frontmatter:

```yaml
---
name: report
description: Persist a detailed, evidence-backed completion report for a finished substantive task — what was achieved and why, technique/algorithm assessment, diff highlights, and optional ELI5/glossary/further-research sections. Use when the user invokes $checkpoint:report, or proactively propose it right after finishing a substantive task (feature shipped, bug fixed, investigation concluded) the same way checkpoint proposes itself for unfinished state.
argument-hint: "[--scope project|global] [--role <text>] [optional note]"
allowed-tools: Read, Write, Edit
---
```

Body sections, following the same shape as `save/SKILL.md`:

- **Decide** — mirrors `checkpoint/SKILL.md`'s own Decide section: recommend a report after finishing a task whose rationale/technique/diff would take real work to reconstruct later (a shipped feature, a fixed bug, a concluded investigation) — not for trivial completed Q&A. State why, propose the destination, and ask before writing unless the user explicitly invoked `$checkpoint:report` directly (in which case write it now, same non-blocking guarantee `save` already has for scope/role).
- **Scope, role** — resolve exactly as `save` does, via `../checkpoint/references/scope-and-role.md`, sharing the same `.checkpoint/config.md`. No separate `--trigger` flag — reports don't need save's automated-trigger provenance concept.
- **Profile** — resolve exactly as `save` does, via `../checkpoint/references/profiles.md`.
- **Gather evidence** — capture only what's actually true: real alternatives actually considered (not invented ones), the real technique/pattern used, the real files changed. Never invent an alternative that wasn't weighed, or a lesson that wasn't learned.
- **Write** — use `../checkpoint/assets/report-template.md`. Written in the language used by the user in the current request (per the language rule already centralized in `checkpoint/SKILL.md`, which the language-fix track of this session updated to explicitly cover every sub-skill including `report`). Omit `ELI5`, `Ghi chú thuật ngữ`, and `Đề xuất mở rộng` headings when they don't apply — don't pad.
- **Quality gate** — before finishing, verify: does this report let someone who wasn't here understand what happened and why, without re-deriving it from the diff themselves?

## Relationship to `list`/`recall`

`list`/`recall` are unaffected — reports are a distinct `type: report` frontmatter value, not `type: checkpoint`, and neither skill searches for or surfaces them. This is deliberate: reports are a historical record to read directly (like a changelog entry), not something to "resume" — `recall`'s whole purpose (resume unfinished work) doesn't apply. A future `report list` could be added if this proves to matter; not built now (YAGNI).

## Testing

- Static content tests (same style as `tests/test_skill_instruction.py`): assert `report/SKILL.md` exists, carries `name: report`, `argument-hint:`, `allowed-tools:`; assert the Decide section language matches the "propose, don't auto-write" pattern already tested implicitly via the hooks' message-only design; assert the template asset contains all required headings and the three conditional ones.
- Fresh-agent forward test (mandatory for new `SKILL.md` per this repo's 2026-08-07 precedent): actually invoke `$checkpoint:report` after a scratch task and confirm the file lands at `.checkpoint/reports/<date>-<slug>.md` with correct frontmatter and sections; confirm conditional sections are correctly omitted when not applicable.

## Rollout

Version bump (all 4 tracked manifests) and a `CHANGELOG.md` entry, same pattern as prior features. Implementation proceeds via `writing-plans` → normal implementation workflow once this document is approved.
