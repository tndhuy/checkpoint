# Checkpoint revision history — design

Status: approved (chat, 2026-08-27) — pending spec self-review and user sign-off on this document.

## Background

The plugin currently keeps exactly one checkpoint document per project (`.checkpoint/checkpoint.md` under `scope: project`, or the equivalent single note under an existing project-notes convention). `save/SKILL.md` explicitly instructs: "Update the active checkpoint instead of creating a duplicate." Every `$checkpoint:save` overwrites that one file wholesale — there is no way to recover the previous state, no diff, no history. `.checkpoint/` is gitignored, so git also cannot reconstruct prior versions.

This was raised directly by the user: *"ở checkpoint đang trả duy nhất 1 files khi cấu hình thôi hả rồi nó cứ cập nhật vào files đó riết à?"* — confirmed yes, and flagged as a gap. A prior research conversation with Codex (pasted into this session) explored three options — append-only Markdown, SQLite-canonical-with-Markdown-projection, and SQLite-only — and concluded SQLite is not justified at current usage scale (personal-scope plugin, a handful of saves per day); append-only Markdown revisions is the right first step, with SQLite revisited only if usage evidence later demands it (1000+ revisions, concurrent multi-agent writers, cross-project analytics).

## Goals

- Every `$checkpoint:save` creates a new, immutable revision file instead of overwriting the previous one.
- `recall` and `list` keep working with the same UX (find "the" checkpoint for this project), just now backed by "the latest revision" instead of "the only file."
- No new runtime dependency, no new tool/allowed-tools surface beyond one read-only capability (`Glob`) already used elsewhere in this plugin (`list`, `recall`).
- Existing single-file checkpoints (including this repo's own `.checkpoint/checkpoint.md`) migrate forward without losing their content.

## Non-goals (explicitly out of scope for this pass)

- Multiple concurrent named checkpoints per project (task-scoped `checkpoint_id`, e.g. `auth-refactor` vs `billing-fix`) — user explicitly chose the single-active-checkpoint-with-history scope over this during design (`AskUserQuestion`, 2026-08-27).
- Automatic retention/pruning of old revisions — user explicitly chose "keep forever, no auto-delete" for v0.1 (`AskUserQuestion`, 2026-08-27). Revisit only if revision count actually becomes a problem.
- Recalling a specific past revision by number (`--revision N`) — `recall` only ever loads the latest. The data model supports adding this later without another migration, but it is not built now (YAGNI — not requested).
- SQLite in any form — explicitly deferred per the Codex research conclusion above; revisit only on real evidence of scale/concurrency/analytics need.

## Directory and file layout

```
.checkpoint/
├── config.md                        (unchanged — scope, role, hooks_enabled, stop_cooldown_minutes)
├── .gitignore                       (unchanged — single `*` line)
└── revisions/
    ├── 2026-08-26-001.md
    ├── 2026-08-27-002.md
    └── 2026-08-27-003.md            (latest = highest revision number, not "most recent filename string")
```

No `checkpoint_id` — a project has exactly one revision stream, so the project itself is the identity (matches the Non-goals decision above).

**Filename format:** `<YYYY-MM-DD>-<NNN>.md`, where `NNN` is the same zero-padded (3-digit) *global* revision number carried in frontmatter — not a per-day counter. The date prefix reflects when that specific revision was written (see Migration below for the one exception). Because the revision number is monotonically increasing and dates never move backward across revisions, plain lexicographic sort of filenames still yields correct chronological/revision order — no timestamp parsing needed to find the latest.

## Frontmatter schema changes

Two new fields added to the existing canonical checkpoint frontmatter (`type`, `status`, `profile`, `scope`, `role`, `project`, `branch`, `owner`):

```yaml
revision: 3
parent_revision: 2        # omitted or null on revision 1
```

`created` and `updated` gain time-of-day precision (ISO 8601, e.g. `2026-08-27T10:08:00+07:00`) instead of date-only (`YYYY-MM-DD`). Date-only was fine when at most one save happened "per day" conceptually; multiple revisions on the same calendar day are now the normal case (this session alone produced 3), so date-only can no longer distinguish same-day revisions from frontmatter alone.

`assets/checkpoint-template.md` and `assets/scope-config-template.md` get updated to reflect this (template skeleton only — no behavior change to `scope-config-template.md`'s own fields).

## Component changes

### `save` (`plugins/checkpoint/skills/save/SKILL.md`)

- `allowed-tools` gains `Glob` (currently `Read, Write, Edit`) — read-only directory listing, same capability class `list`/`recall` already have. No write/execute capability added.
- Destination logic: Glob `.checkpoint/revisions/*.md` (or the project-notes-convention equivalent, if one is already in use — unaffected by this change). Parse the trailing `-NNN.md` numeric suffix of each match, ignoring any file that doesn't match the pattern (see Error handling). Take the max; next revision = max + 1 (or 1 if no matches — first save for this project, or first save after upgrading from the old single-file scheme, see Migration).
- Write the new revision as `.checkpoint/revisions/<today's date>-<next, zero-padded>.md`, with `revision: <next>` and `parent_revision: <max>` (omitted if `next == 1`) in frontmatter.
- Remove "Update the active checkpoint instead of creating a duplicate" from the Destination section; replace with an explicit instruction to always create a new revision file and never edit a prior one.
- `.checkpoint/.gitignore` creation logic (on first-ever `.checkpoint/` creation) is unchanged.

### `recall` (`plugins/checkpoint/skills/recall/SKILL.md`)

- Where it currently locates "the checkpoint file" for a project, it instead Globs `.checkpoint/revisions/*.md`, parses the same `-NNN.md` suffix, and reads the file with the highest revision number in full. The existing 5-question report (outcome, verified truth, hard constraints, next action, done gate) is unchanged.
- Recalling a specific past revision is out of scope (see Non-goals).

### `list` (`plugins/checkpoint/skills/list/SKILL.md`)

- Continues to show one summary line per project (frontmatter fields + title), now sourced from the latest revision file. Additionally reports the revision count for that project (a cheap `Glob` count, no file reads needed — consistent with `list`'s existing "don't read full contents unless needed" rule).

## Migration (existing single-file checkpoints)

On `save`'s invocation, whenever a `Glob` of `.checkpoint/revisions/*.md` returns **zero matching revision files** (whether because the directory doesn't exist yet, or exists but is empty/contains no correctly-named files) *and* a legacy single-file checkpoint is present (`.checkpoint/checkpoint.md`, or the project-notes-convention equivalent with `type: checkpoint` frontmatter):

1. Read the legacy file's frontmatter `updated` field (fallback to `created` if `updated` is absent) to determine the date component of the migrated filename — **not** today's date, since the legacy content was actually captured on that earlier date.
2. Write it as `.checkpoint/revisions/<that date>-001.md`, adding `revision: 1` (no `parent_revision`) to its frontmatter, upgrading `created`/`updated` to include a time component if they were date-only (use midnight local time as a documented placeholder when no time information exists — label it, don't silently invent precision that wasn't there).
3. Leave the legacy file in place, untouched — do not delete it (no destructive auto-actions; see Error handling). The new `save` continues normally, writing revision `002` next.
4. `recall`/`list` prefer `revisions/` whenever it exists and has at least one matching file, regardless of whether a legacy file is also still present.

This repo's own `.checkpoint/checkpoint.md` (currently at revision-equivalent content from today, 2026-08-27) goes through exactly this path on the next real `$checkpoint:save` call after this feature ships.

## Error handling

- A file in `revisions/` that doesn't match `<date>-<NNN>.md` (e.g. a stray manual edit) is skipped by the numeric-suffix parse in `save`/`list`/`recall` — never crashes, never counted toward "max revision."
- `save` writes the new revision file **before** anything else — there is no separate index/pointer file to keep in sync, so a failed write simply means the next `save` attempt retries the same revision number. No corrupt-pointer state is possible by construction (this is *why* the design uses `Glob`-scan-for-max instead of a maintained pointer — see the earlier chat discussion).
- If both `revisions/` (non-empty) and a legacy single file exist simultaneously (partial/already-completed migration), `revisions/` wins; the legacy file is inert and never re-migrated or deleted automatically.

## Testing

- Static content tests (same style as the existing `tests/test_skill_instruction.py`): assert `save/SKILL.md` describes the new revision-writing behavior and no longer contains the old "update instead of duplicate" instruction; assert the template asset carries `revision`/`parent_revision` fields and time-precision `created`/`updated`.
- Fresh-agent forward-testing (mandatory for `SKILL.md` instruction changes per this repo's own precedent, 2026-08-07 decision): actually invoke `$checkpoint:save` multiple times in a scratch project and confirm revision numbers increment correctly without collision; invoke `$checkpoint:recall` and confirm it loads the highest-numbered revision; run the migration path against a synthetic legacy `checkpoint.md` and confirm it becomes `revisions/<date>-001.md` with the right date and the legacy file left in place.

## Rollout

Version bump (all 4 tracked manifests, per this repo's established convention) and a `CHANGELOG.md` entry, same pattern as the `hooks_enabled`/`stop_cooldown_minutes` change. Implementation proceeds via `writing-plans` → normal implementation workflow once this document is approved (this is a single cohesive storage-model change with sequential dependencies — schema, then `save`, then `recall`/`list`, then migration, then tests — not independent parallelizable sub-projects, so `subagent-driven-development` is not the right execution track for it per this repo owner's own stated workflow rule).
